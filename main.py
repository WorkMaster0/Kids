import time
import threading
import requests
import logging
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# ================= CONFIG =================
TELEGRAM_TOKEN = "8227990363:AAGGZbv_gMZyPdPM95f6FnbtxoY96wiqXpQ"
CHAT_ID = "6053907025"

IMPULSE_THRESHOLD = 0.01  # 1%
MAX_WORKERS = 10
PORT = 8000

# ================= API URLS =================
LBANK_FUTURES_SYMBOLS = "https://futures.lbank.com/api/v1/contracts"
LBANK_FUTURES_KLINE = "https://futures.lbank.com/api/v1/kline"

# ================= LOGGING =================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
log = logging.getLogger("LBANK-FUTURES-IMPULSE")

# ================= FLASK =================
app = Flask(__name__)

# ================= TELEGRAM =================
def send_telegram(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text},
            timeout=5
        )
    except Exception as e:
        log.error("Telegram error: %s", e)

# ================= FUTURES SYMBOLS =================
def fetch_futures_symbols():
    try:
        r = requests.get(LBANK_FUTURES_SYMBOLS, timeout=10)
        data = r.json()

        symbols = [
            s["symbol"]
            for s in data.get("data", [])
            if s.get("status") == 1
        ]

        log.info("Fetched %d futures symbols", len(symbols))
        return symbols

    except Exception as e:
        log.error("Symbols fetch error: %s", e)
        return []

# ================= KLINES =================
def fetch_klines(symbol, size=5):
    try:
        params = {
            "symbol": symbol,
            "period": "1min",
            "size": size
        }
        r = requests.get(LBANK_FUTURES_KLINE, params=params, timeout=5)
        data = r.json()

        if "data" not in data:
            return None

        return data["data"]

    except Exception as e:
        log.error("Kline error %s: %s", symbol, e)
        return None

# ================= IMPULSE DETECTOR =================
def detect_impulse(symbol):
    klines = fetch_klines(symbol)
    if not klines or len(klines) < 4:
        return None

    price_now = float(klines[-1]["close"])
    price_past = float(klines[-4]["close"])

    change = (price_now - price_past) / price_past

    if abs(change) >= IMPULSE_THRESHOLD:
        return {
            "symbol": symbol,
            "direction": "LONG 🚀" if change > 0 else "SHORT 🔻",
            "change_pct": change * 100,
            "price": price_now
        }
    return None

# ================= SCANNER =================
def run_impulse_scan():
    send_telegram("⚡ LBANK FUTURES імпульсний скан запущено (3 хв / ≥1%)")
    log.info("Impulse scan started")

    symbols = fetch_futures_symbols()
    results = []

    def scan(sym):
        r = detect_impulse(sym)
        if r:
            results.append(r)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as exe:
        exe.map(scan, symbols)

    if not results:
        send_telegram("❌ Імпульсів не знайдено")
        return

    results.sort(key=lambda x: abs(x["change_pct"]), reverse=True)

    for r in results:
        msg = (
            f"🚀 FUTURES IMPULSE\n"
            f"Symbol: {r['symbol']}\n"
            f"Direction: {r['direction']}\n"
            f"Move: {r['change_pct']:.2f}% за 3 хв\n"
            f"Price: {r['price']}\n"
            f"Time: {datetime.utcnow()}"
        )
        send_telegram(msg)

# ================= TELEGRAM WEBHOOK =================
@app.route(f"/telegram/{TELEGRAM_TOKEN}", methods=["POST"])
def telegram_webhook():
    update = request.get_json(force=True)
    text = update.get("message", {}).get("text", "").lower()

    if text.startswith("/impulse"):
        threading.Thread(target=run_impulse_scan, daemon=True).start()

    return jsonify({"ok": True})

# ================= MAIN =================
if __name__ == "__main__":
    log.info("LBANK Futures Impulse Bot started")
    app.run(host="0.0.0.0", port=PORT)