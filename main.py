import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from video_generator import generate_children_video
from flask import Flask, request
import asyncio
import threading

# Налаштування
TOKEN = "8227990363:AAGGZbv_gMZyPdPM95f6FnbtxoY96wiqXpQ"
logging.basicConfig(level=logging.INFO)

# Отримуємо URL з змінних оточення Render
RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL', 'https://kids-rvcr.onrender.com')
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}/{TOKEN}"

# Створюємо Flask додаток
app = Flask(__name__)

# Глобальні змінні для Application
application = None
bot_instance = None

def setup_application():
    """Ініціалізація Application (синхронно)"""
    global application, bot_instance
    
    application = Application.builder().token(TOKEN).build()
    bot_instance = application.bot
    
    # Додаємо обробники
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Ініціалізуємо application
    asyncio.run(initialize_app())
    
    logging.info("✅ Application ініціалізовано")

async def initialize_app():
    """Ініціалізація Application"""
    await application.initialize()
    await application.start()

async def set_webhook_async():
    """Асинхронне встановлення вебхука"""
    try:
        await bot_instance.set_webhook(url=WEBHOOK_URL)
        logging.info(f"✅ Webhook встановлено: {WEBHOOK_URL}")
        return True
    except Exception as e:
        logging.error(f"❌ Помилка встановлення webhook: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 Привіт! Я створюю дитячі відео!\n\n"
        "🎯 Напиши тему для відео!\n"
        "Приклад: \"казка про динозаврика\""
    )
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.message.from_user.id
    
    await update.message.reply_text("🎬 Створюю контент...")
    
    try:
        result = await generate_children_video(user_message, user_id)
        
        if isinstance(result, dict) and "audio" in result:
            # Відправляємо аудіо
            with open(result["audio"], 'rb') as audio_file:
                await update.message.reply_audio(
                    audio=audio_file,
                    caption=f"🎵 {result['text']}\n\nТема: {user_message}"
                )
            os.remove(result["audio"])
        else:
            await update.message.reply_text(f"📖 {result['text']}\n\nТема: {user_message}")
            
    except Exception as e:
        logging.error(f"Помилка: {e}")
        await update.message.reply_text("❌ Спробуйте іншу тему")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = "📖 Напиши тему для відео: \"казка\", \"вчимо кольори\", \"пісенька\""
    await update.message.reply_text(help_text)

@app.route('/')
def home():
    return "🤖 Дитячий Video Bot is running! 🎬"

@app.route('/set_webhook', methods=['GET'])
def set_webhook_route():
    """Вручну встановити вебхук"""
    try:
        # Створюємо новий event loop для кожного запиту
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(set_webhook_async())
        loop.close()
        
        if result:
            return f"✅ Webhook встановлено: {WEBHOOK_URL}"
        else:
            return f"❌ Не вдалося встановити webhook"
    except Exception as e:
        return f"❌ Помилка: {e}"

@app.route('/remove_webhook', methods=['GET'])
def remove_webhook_route():
    """Видалити вебхук"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(bot_instance.delete_webhook())
        loop.close()
        return "✅ Webhook видалено"
    except Exception as e:
        return f"❌ Помилка: {e}"

@app.route('/status', methods=['GET'])
def status():
    """Перевірка статусу"""
    return {
        "status": "running",
        "webhook_url": WEBHOOK_URL,
        "bot_initialized": application is not None
    }

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    """Обробка вебхука від Telegram"""
    try:
        if not request.data:
            return 'No data', 400
            
        data = request.get_json()
        if not data:
            return 'Invalid JSON', 400
        
        update = Update.de_json(data, bot_instance)
        
        # Обробляємо оновлення в окремому потоці з новим event loop
        def process_update_sync():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(application.process_update(update))
                loop.close()
            except Exception as e:
                logging.error(f"Помилка обробки оновлення: {e}")
        
        thread = threading.Thread(target=process_update_sync)
        thread.start()
        
        return 'OK'
        
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return 'Error', 500

async def shutdown():
    """Коректне закриття"""
    if application:
        await application.stop()
        await application.shutdown()

def main():
    """Запуск бота"""
    if os.environ.get('RENDER'):
        logging.info("🚀 Запуск на Render з вебхуком...")
        
        # Ініціалізуємо application
        setup_application()
        
        # Встановлюємо вебхук
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(set_webhook_async())
            loop.close()
        except Exception as e:
            logging.error(f"Помилка встановлення webhook: {e}")
        
        # Запускаємо Flask
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
        
    else:
        logging.info("🖥️ Запуск локально з polling...")
        # Для локального запуску
        application = Application.builder().token(TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.run_polling()

if __name__ == "__main__":
    main()