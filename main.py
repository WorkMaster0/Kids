import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from video_generator import generate_children_video
from flask import Flask, request

# Налаштування
TOKEN = "8227990363:AAGGZbv_gMZyPdPM95f6FnbtxoY96wiqXpQ"
logging.basicConfig(level=logging.INFO)

# Отримуємо URL з змінних оточення Render
RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL', 'https://your-app-name.onrender.com')
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}/{TOKEN}"

# Створюємо Flask додаток для вебхука
app = Flask(__name__)

# Створюємо Telegram Application
application = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    welcome_text = (
        "👋 Привіт! Я створюю дитячі відео!\n\n"
        "🎬 Доступні теми:\n"
        "• Казки та історії\n"
        "• Навчальні відео\n"
        "• Пісеньки та віршики\n"
        "• Розвиваючі заняття\n\n"
        "Просто напиши тему для відео!"
    )
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка повідомлень з темою"""
    user_message = update.message.text
    user_id = update.message.from_user.id
    
    await update.message.reply_text("🎬 Створюю відео... Це займе 1-2 хвилини!")
    
    try:
        # Генеруємо відео
        result = await generate_children_video(user_message, user_id)
        
        if isinstance(result, dict) and "audio" in result:
            # Відправляємо аудіо + картинку
            with open(result["audio"], 'rb') as audio_file:
                await update.message.reply_audio(
                    audio=audio_file,
                    caption=f"🎵 {result['text']}\n\nТема: {user_message}"
                )
            
            if "images" in result:
                for img_path in result["images"]:
                    with open(img_path, 'rb') as img_file:
                        await update.message.reply_photo(
                            photo=img_file,
                            caption="🖼️ Малюнок для історії!"
                        )
                    os.remove(img_path)
            
            os.remove(result["audio"])
            
        elif isinstance(result, str) and os.path.exists(result):
            # Відправляємо відео
            with open(result, 'rb') as video_file:
                await update.message.reply_video(
                    video=video_file,
                    caption=f"🎉 Ваше відео готове!\nТема: {user_message}"
                )
            os.remove(result)
        else:
            await update.message.reply_text(f"📖 {result['text']}\n\nТема: {user_message}")
            
    except Exception as e:
        logging.error(f"Помилка: {e}")
        await update.message.reply_text("❌ Сталася помилка. Спробуйте пізніше.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = (
        "📖 Довідка по боту:\n\n"
        "🎯 Як користуватися:\n"
        "1. Напишіть тему для відео\n"
        "2. Чекайте 1-2 хвилини\n"
        "3. Отримуйте готове відео!\n\n"
        "📚 Приклади тем:\n"
        "• \"Казка про трьох поросят\"\n"
        "• \"Вчимо кольори\"\n"
        "• \"Весела пісенька про звіряток\"\n"
        "• \"Розвиваюче відео про цифри\"\n\n"
        "🎨 Бот створює:\n"
        "• Яскраві анімації\n"
        "• Дитячі голоси\n"
        "• Веселу музику\n"
        "• Навчальний контент"
    )
    await update.message.reply_text(help_text)

# Додаємо обробники
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.route('/')
def home():
    return "🤖 Дитячий Video Bot is running! 🎬"

@app.route('/set_webhook', methods=['GET'])
async def set_webhook():
    """Вручну встановити вебхук"""
    try:
        await application.bot.set_webhook(url=WEBHOOK_URL)
        return f"✅ Webhook встановлено: {WEBHOOK_URL}"
    except Exception as e:
        return f"❌ Помилка: {e}"

@app.route('/remove_webhook', methods=['GET'])
async def remove_webhook():
    """Видалити вебхук"""
    try:
        await application.bot.delete_webhook()
        return "✅ Webhook видалено"
    except Exception as e:
        return f"❌ Помилка: {e}"

@app.route(f'/{TOKEN}', methods=['POST'])
async def webhook():
    """Обробка вебхука від Telegram"""
    try:
        data = await request.get_json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        return 'OK'
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return 'Error', 500

def main():
    """Запуск бота з вебхуком"""
    # Перевіряємо чи ми на Render
    if os.environ.get('RENDER'):
        logging.info("🚀 Запуск на Render з вебхуком...")
        
        # Запускаємо Flask
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        logging.info("🖥️ Запуск локально з polling...")
        # Локально використовуємо polling
        application.run_polling()

if __name__ == "__main__":
    main()