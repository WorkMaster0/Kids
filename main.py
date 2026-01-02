import time
import threading
import requests
import logging
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# ================= CONFIG =================
TELEGRAM_TOKEN = "PASTE_TELEGRAM_TOKEN"
CHAT_ID = "PASTE_CHAT_ID"

IMPULSE_THRESHOLD = 0.003   # 0.3% (для реального ринку)
MAX_WORKERS = 12
PORT = 8000

# ================= LBANK FUTURES API =================
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

# ================= FETCH FUTURES SYMBOLS =================
def fetch_futures_symbols():
    try:
        r = requests.get(LBANK_FUTURES_SYMBOLS, timeout=10)
        data = r.json()

        symbols = [
            s["symbol"]
            for s in data.get("data", [])
            if s.get("status") == "open"
        ]

        log.info("Fetched %d futures symbols", len(symbols))
        return symbols

    except Exception as e:
        log.error("Symbols fetch error: %s", e)
        return []

# ================= FETCH KLINES =================
def fetch_klines(symbol, size=5):
    try:
        params = {
            "symbol": symbol,
            "period": "1min",
            "size": size
        }
        r = requests.get(LBANK_FUTURES_KLINE, params=params, timeout=5)
        data = r.json()

        if "data" not in data or not data["data"]:
            return None

        # LBANK повертає від нових до старих → розвертаємо
        return list(reversed(data["data"]))

    except Exception as e:
        log.error("Kline error %s: %s", symbol, e)
        return None

# ================= IMPULSE DETECTOR =================
def detect_impulse(symbol):
    klines = fetch_klines(symbol)
    if not klines or len(klines) < 4:
        return None

    try:
        price_now = float(klines[-1][4])
        price_past = float(klines[-4][4])
    except Exception:
        return None

    change = (price_now - price_past) / price_past

    log.info("%s change %.3f%%", symbol, change * 100)

    if abs(change) >= IMPULSE_THRESHOLD:
        return {
            "symbol": symbol,
            "direction": "LONG 🚀" if change > 0 else "SHORT 🔻",
            "change_pct": change * 100,
            "price": price_now
        }

    return None

# ================= SCAN RUNNER =================
def run_impulse_scan():
    send_telegram("⚡ LBANK FUTURES імпульсний скан запущено (3 хв)")
    log.info("Impulse scan started")

    symbols = fetch_futures_symbols()
    if not symbols:
        send_telegram("❌ Не вдалося отримати список пар")
        return

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
            f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )
        send_telegram(msg)

# ================= TELEGRAM WEBHOOK =================
@app.route("/telegram_webhook", methods=["POST"])
def telegram_webhook():
    update = request.get_json(force=True)
    message = update.get("message", {})
    text = message.get("text", "").lower()

    if text.startswith("/impulse"):
        threading.Thread(target=run_impulse_scan, daemon=True).start()

    return jsonify({"ok": True})

# ================= MAIN =================
if __name__ == "__main__":
    log.info("LBANK Futures Impulse Bot started")
    app.run(host="0.0.0.0", port=PORT)