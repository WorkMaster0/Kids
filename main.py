import os
import logging
from telegram import Update, Bot
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

# Глобальний bot instance
bot = Bot(TOKEN)

# Обробники команд
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = "👋 Привіт! Напиши тему для відео (наприклад: 'казка про динозаврика')"
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.message.from_user.id
    
    await update.message.reply_text("🎬 Створюю контент...")
    
    try:
        result = await generate_children_video(user_message, user_id)
        
        # Перевіряємо тип результату
        if isinstance(result, dict):
            if "audio" in result:
                # Відправляємо аудіо
                with open(result["audio"], 'rb') as audio_file:
                    await update.message.reply_audio(
                        audio=audio_file,
                        caption=f"🎵 {result['text']}\n\nТема: {user_message}"
                    )
                os.remove(result["audio"])
                
                # Відправляємо зображення
                if "images" in result:
                    for img_path in result["images"]:
                        with open(img_path, 'rb') as img_file:
                            await update.message.reply_photo(photo=img_file)
                        os.remove(img_path)
            elif "text" in result:
                # Тільки текст
                await update.message.reply_text(f"📖 {result['text']}\n\nТема: {user_message}")
                
        elif isinstance(result, str) and os.path.exists(result):
            # Відео файл
            with open(result, 'rb') as video_file:
                await update.message.reply_video(
                    video=video_file,
                    caption=f"🎉 Ваше відео готове!\nТема: {user_message}"
                )
            os.remove(result)
        else:
            await update.message.reply_text("❌ Не вдалося створити контент. Спробуйте іншу тему.")
            
    except Exception as e:
        logging.error(f"Помилка: {e}")
        await update.message.reply_text("❌ Спробуйте іншу тему")

# Функції для вебхука
def set_webhook_sync():
    """Синхронне встановлення вебхука"""
    try:
        import requests
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
        # Створюємо новий event loop для кожного запиту
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Створюємо тимчасовий Application для обробки
        app = Application.builder().token(TOKEN).build()
        
        # Додаємо обробники
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Ініціалізуємо та обробляємо
        loop.run_until_complete(app.initialize())
        update = Update.de_json(update_data, app.bot)
        loop.run_until_complete(app.process_update(update))
        loop.run_until_complete(app.shutdown())
        
        loop.close()
    except Exception as e:
        logging.error(f"Помилка обробки: {e}")

@app.route('/')
def home():
    return "🤖 Дитячий Video Bot is running! 🎬"

@app.route('/set_webhook', methods=['GET'])
def set_webhook_route():
    """Вручну встановити вебхук"""
    if set_webhook_sync():
        return f"✅ Webhook встановлено: {WEBHOOK_URL}"
    else:
        return "❌ Не вдалося встановити webhook"

@app.route('/remove_webhook', methods=['GET'])
def remove_webhook_route():
    """Видалити вебхук"""
    try:
        import requests
        url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook"
        response = requests.post(url)
        return "✅ Webhook видалено"
    except Exception as e:
        return f"❌ Помилка: {e}"

@app.route('/status', methods=['GET'])
def status():
    """Перевірка статусу"""
    try:
        import requests
        url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
        response = requests.get(url).json()
        return {
            "status": "running",
            "webhook_info": response
        }
    except:
        return {"status": "running", "webhook_url": WEBHOOK_URL}

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    """Обробка вебхука від Telegram"""
    try:
        data = request.get_json()
        if not data:
            return 'Invalid JSON', 400
        
        # Обробляємо в окремому потоці
        thread = threading.Thread(target=process_update_sync, args=(data,))
        thread.start()
        
        return 'OK'
        
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return 'Error', 500

def main():
    """Запуск бота"""
    if os.environ.get('RENDER'):
        logging.info("🚀 Запуск на Render з вебхуком...")
        
        # Встановлюємо вебхук при старті
        set_webhook_sync()
        
        # Запускаємо Flask
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
        
    else:
        logging.info("🖥️ Запуск локально з polling...")
        # Для локального запуску
        application = Application.builder().token(TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.run_polling()

if __name__ == "__main__":
    main()