from image_generator import generate_story_image, generate_simple_image
import os
import logging
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from video_generator import generate_children_video, generate_story
from flask import Flask, request
import asyncio
import threading
import tempfile
import requests

# Налаштування
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', "8227990363:AAGGZbv_gMZyPdPM95f6FnbtxoY96wiqXpQ")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

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
        "Напиши тему для відео, наприклад:\n"
        "• казка про динозаврика\n"
        "• пригоди у лісі\n"
        "• космічна подорож\n"
        "• історія про принцесу\n"
        "• веселі машинки\n\n"
        "Я згенерую історію, зображення та відео!"
    )
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "ℹ️ Допомога:\n\n"
        "Просто напиши будь-яку тему для дитячої історії, наприклад:\n"
        "- казка про дракончика\n"
        "- пригоди у морі\n"
        "- історія про робота\n"
        "- веселі тварини\n\n"
        "Я створюю:\n"
        "📖 Текст історії\n"
        "🎨 Зображення\n"
        "🎵 Аудіо розповідь\n"
        "🎬 Відео (якщо вдасться)\n\n"
        "Почни з команди /start"
    )
    await update.message.reply_text(help_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.message.from_user.id
    
    if len(user_message) < 3:
        await update.message.reply_text("📝 Будь ласка, напиши трохи довшу тему (мінімум 3 символи)")
        return
    
    await update.message.reply_text("🎬 Створюю дитячу історію... Це може зайняти кілька хвилин.")
    
    try:
        result = await generate_children_video(user_message, user_id)
        
        print(f"Результат генерації: {type(result)}")
        
        # Перевіряємо тип результату
        if isinstance(result, dict):
            if "audio" in result and os.path.exists(result["audio"]):
                # Відправляємо аудіо
                try:
                    with open(result["audio"], 'rb') as audio_file:
                        await update.message.reply_audio(
                            audio=audio_file,
                            caption=f"🎵 Аудіо історія:\n\n{result['text']}\n\nТема: {user_message}",
                            title="Дитяча історія",
                            performer="StoryBot"
                        )
                    # Видаляємо тимчасові файли
                    if os.path.exists(result["audio"]):
                        os.remove(result["audio"])
                except Exception as e:
                    print(f"Помилка відправки аудіо: {e}")
                    await update.message.reply_text(f"📖 Ось ваша історія:\n\n{result['text']}")
                
                # Відправляємо зображення
                if "images" in result:
                    for img_path in result["images"]:
                        try:
                            if os.path.exists(img_path) and os.path.getsize(img_path) > 0:
                                with open(img_path, 'rb') as img_file:
                                    await update.message.reply_photo(
                                        photo=img_file,
                                        caption="🖼️ Зображення до історії"
                                    )
                                os.remove(img_path)
                        except Exception as e:
                            print(f"Помилка відправки зображення: {e}")
            elif "text" in result:
                # Тільки текст
                await update.message.reply_text(f"📖 Ось ваша історія:\n\n{result['text']}\n\nТема: {user_message}")
                
        elif isinstance(result, str) and os.path.exists(result):
            # Відео файл
            try:
                # Перевіряємо розмір файлу (Telegram має обмеження 50MB)
                file_size = os.path.getsize(result) / (1024 * 1024)  # MB
                if file_size > 45:
                    await update.message.reply_text("📖 Відео занадто велике, ось історія:")
                    await update.message.reply_text(f"{generate_story(user_message)}")
                    os.remove(result)
                    return
                
                await update.message.reply_text("📤 Відправляю відео...")
                
                with open(result, 'rb') as video_file:
                    await update.message.reply_video(
                        video=video_file,
                        caption=f"🎉 Ваше відео готове!\nТема: {user_message}",
                        supports_streaming=True,
                        width=1024,
                        height=768
                    )
                if os.path.exists(result):
                    os.remove(result)
            except Exception as e:
                print(f"Помилка відправки відео: {e}")
                # Якщо відео не вдалося відправити, надсилаємо текст історії
                await update.message.reply_text(f"📖 Ось ваша історія:\n\n{generate_story(user_message)}")
        else:
            await update.message.reply_text("❌ Не вдалося створити контент. Спробуйте іншу тему.")
            
    except Exception as e:
        logging.error(f"Помилка: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text("❌ Сталася помилка. Спробуйте іншу тему або напишіть /start")

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
        # Створюємо новий event loop для кожного запиту
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Створюємо тимчасовий Application для обробки
        app = Application.builder().token(TOKEN).build()
        
        # Додаємо обробники
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
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
        url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook"
        response = requests.post(url)
        return "✅ Webhook видалено"
    except Exception as e:
        return f"❌ Помилка: {e}"

@app.route('/status', methods=['GET'])
def status():
    """Перевірка статусу"""
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

@app.route('/health', methods=['GET'])
def health_check():
    """Перевірка здоров'я додатку"""
    return {"status": "healthy", "service": "kids-story-bot"}

def run_flask():
    """Запуск Flask сервера"""
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def run_polling():
    """Запуск бота з polling"""
    logging.info("🖥️ Запуск локально з polling...")
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

def main():
    """Запуск бота"""
    if os.environ.get('RENDER'):
        logging.info("🚀 Запуск на Render з вебхуком...")
        
        # Встановлюємо вебхук при старті
        set_webhook_sync()
        
        # Запускаємо Flask
        run_flask()
        
    else:
        # Для локального запуску
        run_polling()

if __name__ == "__main__":
    main()