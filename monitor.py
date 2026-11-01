import asyncio
import os
from datetime import datetime, timezone
from typing import Dict, List

import aiohttp
import ccxt
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
THRESHOLD_PERCENT = float(os.getenv("THRESHOLD_PERCENT", "0.5"))
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "10"))
DEDUP_SECONDS = int(os.getenv("DEDUP_SECONDS", "300"))

TARGET_TICKERS = {
    "AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "META", "GOOGL", "NFLX",
    "AMD", "INTC", "PLTR", "SHOP", "QQQ", "SPY",
}

EXCHANGES = [
    "kucoin",
    "mexc",
    "gate",
    "bybit",
    "bitget",
    "lbank",
    "coinw",
    "xt",
    "okx",
]

LAST_ALERTS: Dict[str, float] = {}


def spread_percent(bid: float, ask: float) -> float:
    if bid <= 0 or ask <= 0:
        return 999999.0
    mid = (bid + ask) / 2
    return ((ask - bid) / mid) * 100


def normalize_symbol(value: str) -> str:
    return value.replace("/", "").replace("-", "").replace("_", "").upper()


def get_exchange_market_candidates(exchange_name: str, ticker: str):
    try:
        exchange = getattr(ccxt, exchange_name)({"enableRateLimit": True})
        markets = exchange.load_markets()
    except Exception:
        return []

    norm_ticker = normalize_symbol(ticker)
    matches = []
    for market_symbol, market in markets.items():
        if not market.get("active", True):
            continue
        if market.get("type") != "spot":
            continue

        market_norm = normalize_symbol(market_symbol)
        if norm_ticker in market_norm:
            matches.append(market_symbol)

    return matches


async def send_telegram(message: str) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram is not configured. Message skipped:")
        print(message)
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, data=payload, timeout=10) as resp:
                data = await resp.json()
                if not data.get("ok"):
                    print(f"Telegram error: {data}")
        except Exception as exc:
            print(f"Telegram send failed: {exc}")


async def fetch_orderbook(exchange_name: str, market_symbol: str):
    try:
        exchange = getattr(ccxt, exchange_name)({"enableRateLimit": True})
        orderbook = exchange.fetch_order_book(market_symbol, limit=1)
    except Exception:
        return None

    bids = orderbook.get("bids") or []
    asks = orderbook.get("asks") or []
    if not bids or not asks:
        return None

    bid = float(bids[0][0])
    ask = float(asks[0][0])
    return {
        "exchange": exchange_name,
        "symbol": market_symbol,
        "bid": bid,
        "ask": ask,
    }


async def scan_once() -> None:
    tasks: List[asyncio.Task] = []

    for exchange_name in EXCHANGES:
        for ticker in TARGET_TICKERS:
            candidates = get_exchange_market_candidates(exchange_name, ticker)
            if not candidates:
                continue
            for symbol in candidates:
                tasks.append(asyncio.create_task(fetch_orderbook(exchange_name, symbol)))

    if not tasks:
        return

    results = await asyncio.gather(*tasks)
    now_ts = datetime.now(timezone.utc).timestamp()

    for quote in results:
        if not quote:
            continue

        s_pct = spread_percent(float(quote["bid"]), float(quote["ask"]))
        if s_pct > THRESHOLD_PERCENT:
            continue

        key = f"{quote['exchange']}:{quote['symbol']}"
        last_ts = LAST_ALERTS.get(key)
        if last_ts and (now_ts - last_ts) < DEDUP_SECONDS:
            continue

        LAST_ALERTS[key] = now_ts

        message = (
            "<b>ALERT: narrow spread</b>\n"
            f"Exchange: {quote['exchange']}\n"
            f"Symbol: {quote['symbol']}\n"
            f"Bid: {quote['bid']:.4f}\n"
            f"Ask: {quote['ask']:.4f}\n"
            f"Spread: {s_pct:.3f}%\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )
        print(message)
        await send_telegram(message)


async def main() -> None:
    print("Tokenized stock spread monitor started")
    while True:
        try:
            await scan_once()
        except Exception as exc:
            print(f"scan error: {exc}")
        await asyncio.sleep(POLL_SECONDS)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Monitor stopped by user")
