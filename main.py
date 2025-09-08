import os
import logging
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from video_generator import generate_cartoon
from flask import Flask, request
import asyncio
import threading
import tempfile
import requests
import sys
from datetime import datetime

# Додаємо поточну директорію до шляху пошуку модулів
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Налаштування
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', "8227990363:AAGGZbv_gMZyPdPM95f6FnbtxoY96wiqXpQ")
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)

# Отримуємо URL з змінних оточення Render
RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL', 'https://kids-rvcr.onrender.com')
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}/{TOKEN}"

# Створюємо Flask додаток
app = Flask(__name__)

# Глобальний bot instance
bot = Bot(TOKEN)

# Обробники команд
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 Привіт! Я створюю дитячі історії!\n\n"
        "Напиши тему, і я:\n"
        "📖 Придумаю цікаву історію\n"
        "🎵 Озвучу її українською\n"
        "🎨 Створю яскраве зображення\n"
        "🎬 Згенерую відео\n\n"
        "Приклади тем:\n"
        "• динозаврик\n"
        "• космос\n"
        "• принцеса\n"
        "• лісові звірята\n"
        "• машинки\n"
        "• казка\n\n"
        "Напиши будь-яку тему!"
    )
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "ℹ️ Допомога:\n\n"
        "Просто напиши будь-який текст, наприклад:\n"
        "- Весела пригода\n"
        "- Дитяча казка\n"
        "- Пригоди у лісі\n"
        "- Космічна подорож\n\n"
        "Я створю:\n"
        "🎵 Аудіо версію твого тексту\n"
        "🎨 Яскраве зображення\n"
        "🎬 Відеофайл з аудіо\n\n"
        "Почни з команди /start"
    )
    await update.message.reply_text(help_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.message.from_user.id
    
    if len(user_message) < 2:
        await update.message.reply_text("📝 Будь ласка, напиши тему (мінімум 2 символи)")
        return
    
    if len(user_message) > 30:
        await update.message.reply_text("📝 Тема занадто довга. Максимум 30 символів.")
        return
    
    await update.message.reply_text("🎬 Створюю мультфільм... Це займе близько хвилини ⏳")
    
    try:
        result = await generate_cartoon(user_message, user_id)
        
        if isinstance(result, str) and os.path.exists(result):
            # Мультфільм створено
            try:
                file_size = os.path.getsize(result) / (1024 * 1024)
                if file_size > 45:
                    await update.message.reply_text("❌ Мультфільм занадто великий")
                    os.remove(result)
                    return
                
                await update.message.reply_text("📤 Відправляю мультфільм...")
                
                with open(result, 'rb') as video_file:
                    await update.message.reply_video(
                        video=video_file,
                        caption=f"🎉 Мультфільм на тему: {user_message}",
                        supports_streaming=True,
                        width=1024,
                        height=768
                    )
                
                if os.path.exists(result):
                    os.remove(result)
                    
            except Exception as e:
                print(f"Помилка відправки відео: {e}")
                await update.message.reply_text("❌ Не вдалося відправити мультфільм")
                
        elif isinstance(result, dict) and "text" in result:
            # Тільки текст історії
            await update.message.reply_text(f"📖 Ось ідея для мультфільму:\n\n{result['text']}")
            
        else:
            await update.message.reply_text("❌ Не вдалося створити мультфільм")
            
    except Exception as e:
        logging.error(f"Помилка: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text("❌ Сталася помилка. Спробуй іншу тему!")

# Функції для вебхука
def set_webhook_sync():
    """Синхронне встановлення вебхука"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
        data = {"url": WEBHOOK_URL}
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            logging.info(f"✅ Webhook встановлено: {WEBHOOK_URL}")
            return True
        else:
            logging.error(f"❌ Помилка: {response.text}")
            return False
    except Exception as e:
        logging.error(f"❌ Помилка встановлення webhook: {e}")
        return False

def process_update_sync(update_data):
    """Синхронна обробка оновлення"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        loop.run_until_complete(app.initialize())
        update = Update.de_json(update_data, app.bot)
        loop.run_until_complete(app.process_update(update))
        loop.run_until_complete(app.shutdown())
        
        loop.close()
    except Exception as e:
        logging.error(f"Помилка обробки: {e}")

@app.route('/')
def home():
    return "🤖 Video Generator Bot is running! 🎬"

@app.route('/set_webhook', methods=['GET'])
def set_webhook_route():
    if set_webhook_sync():
        return f"✅ Webhook встановлено: {WEBHOOK_URL}"
    else:
        return "❌ Не вдалося встановити webhook"

@app.route('/remove_webhook', methods=['GET'])
def remove_webhook_route():
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook"
        response = requests.post(url)
        return "✅ Webhook видалено"
    except Exception as e:
        return f"❌ Помилка: {e}"

@app.route('/status', methods=['GET'])
def status():
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
        response = requests.get(url).json()
        return {
            "status": "running",
            "webhook_info": response,
            "webhook_url": WEBHOOK_URL
        }
    except Exception as e:
        return {"status": "running", "error": str(e), "webhook_url": WEBHOOK_URL}

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        if not data:
            return 'Invalid JSON', 400
        
        thread = threading.Thread(target=process_update_sync, args=(data,))
        thread.start()
        
        return 'OK'
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return 'Error', 500

@app.route('/health', methods=['GET'])
def health_check():
    return {
        "status": "healthy", 
        "service": "video-generator-bot",
        "timestamp": datetime.now().isoformat()
    }

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def run_polling():
    logging.info("🖥️ Запуск локально з polling...")
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

def main():
    if os.environ.get('RENDER'):
        logging.info("🚀 Запуск на Render з вебхуком...")
        set_webhook_sync()
        run_flask()
    else:
        run_polling()

if __name__ == "__main__":
    main()