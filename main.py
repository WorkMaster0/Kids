import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from video_generator import generate_children_video

# Налаштування
TOKEN = "8227990363:AAGGZbv_gMZyPdPM95f6FnbtxoY96wiqXpQ"
logging.basicConfig(level=logging.INFO)

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

async def generate_children_video(topic: str, user_id: str):
    """Генерація повноцінного дитячого відео"""
    try:
        # Генеруємо історію
        story_text = generate_story(topic)
        scenes = generate_story_scenes(story_text)
        
        # Створюємо тимчасову папку
        temp_dir = tempfile.mkdtemp()
        audio_path = os.path.join(temp_dir, "story_audio.mp3")
        
        # Генеруємо аудіо історії
        generate_audio(story_text, audio_path)
        
        # Генеруємо зображення для кожної сцени
        image_paths = []
        for i, scene in enumerate(scenes):
            img_path = os.path.join(temp_dir, f"scene_{i}.png")
            if generate_story_image(scene['image_prompt'], img_path):
                image_paths.append(img_path)
        
        # Створюємо відео (якщо є FFmpeg)
        if len(image_paths) > 0:
            try:
                from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
                
                clips = []
                audio_clip = AudioFileClip(audio_path)
                total_duration = audio_clip.duration
                scene_duration = total_duration / len(image_paths)
                
                for img_path in image_paths:
                    clip = ImageClip(img_path).set_duration(scene_duration)
                    clips.append(clip)
                
                final_clip = concatenate_videoclips(clips).set_audio(audio_clip)
                video_path = os.path.join(temp_dir, "final_video.mp4")
                final_clip.write_videofile(video_path, fps=24)
                
                return video_path
                
            except ImportError:
                # Якщо moviepy не встановлено - повертаємо аудіо + зображення
                return {
                    "audio": audio_path,
                    "images": image_paths,
                    "text": story_text
                }
        
        return {"text": story_text}
        
    except Exception as e:
        print(f"Помилка генерації відео: {e}")
        return {"text": generate_story(topic)}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка повідомлень з темою"""
    user_message = update.message.text
    user_id = update.message.from_user.id
    
    await update.message.reply_text("🎬 Створюю відео... Це займе 1-2 хвилини!")
    
    try:
        # Генеруємо відео
        video_path = await generate_children_video(user_message, user_id)
        
        if video_path and os.path.exists(video_path):
            # Відправляємо відео
            with open(video_path, 'rb') as video_file:
                await update.message.reply_video(
                    video=video_file,
                    caption=f"🎉 Ваше відео готове!\nТема: {user_message}"
                )
            # Видаляємо тимчасовий файл
            os.remove(video_path)
        else:
            await update.message.reply_text("❌ Не вдалося створити відео. Спробуйте іншу тему.")
            
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

def main():
    """Запуск бота"""
    application = Application.builder().token(TOKEN).build()
    
    # Обробники команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logging.info("Бот запущений!")
    application.run_polling()

if __name__ == "__main__":
    main()