import os
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from gtts import gTTS
import tempfile
import time

def generate_audio(text: str, filename: str):
    """Генерація аудіо (текст у мову)"""
    try:
        print(f"Генеруємо аудіо для тексту: {text[:50]}...")
        tts = gTTS(text=text, lang='uk', slow=False)
        tts.save(filename)
        print(f"Аудіо збережено у: {filename}")
        return True
    except Exception as e:
        print(f"Помилка генерації аудіо: {e}")
        return False

def create_video_from_audio(audio_path: str, prompt: str, output_path: str):
    """Створення відео з аудіо"""
    try:
        if not os.path.exists(audio_path):
            print("Аудіо файл не існує")
            return False
        
        # Генеруємо зображення для відео
        from image_generator import generate_video_image
        image_path = output_path.replace('.mp4', '.png')
        
        if not generate_video_image(prompt, image_path):
            print("Не вдалося створити зображення")
            return False
        
        # Завантажуємо аудіо
        audio_clip = AudioFileClip(audio_path)
        audio_duration = audio_clip.duration
        
        # Створюємо відео кліп
        image_clip = ImageClip(image_path).set_duration(audio_duration)
        
        # Об'єднуємо аудіо та відео
        final_clip = image_clip.set_audio(audio_clip)
        
        # Записуємо відео
        print("Записуємо відеофайл...")
        final_clip.write_videofile(
            output_path, 
            fps=24, 
            codec='libx264', 
            audio_codec='aac',
            threads=4,
            preset='fast',
            verbose=False,
            logger=None
        )
        
        # Закриваємо кліпи для звільнення пам'яті
        final_clip.close()
        image_clip.close()
        audio_clip.close()
        
        # Видаляємо тимчасове зображення
        if os.path.exists(image_path):
            os.remove(image_path)
        
        print(f"Відео успішно створено: {output_path}")
        return True
        
    except Exception as e:
        print(f"Помилка створення відео: {e}")
        import traceback
        traceback.print_exc()
        return False

async def generate_video_with_audio(prompt: str, user_id: str):
    """Генерація відео з аудіо"""
    try:
        print(f"Початок генерації відео для: {prompt}")
        
        # Створюємо тимчасову папку
        temp_dir = tempfile.mkdtemp()
        print(f"Тимчасова папка: {temp_dir}")
        
        # Генеруємо аудіо
        audio_path = os.path.join(temp_dir, "audio.mp3")
        if not generate_audio(prompt, audio_path):
            return {"text": prompt, "error": "audio_failed"}
        
        # Перевіряємо чи існує аудіо файл
        if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
            print("Аудіо файл не створено")
            return {"text": prompt, "error": "audio_empty"}
        
        # Створюємо відео
        video_path = os.path.join(temp_dir, "video.mp4")
        if create_video_from_audio(audio_path, prompt, video_path):
            if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
                return video_path
            else:
                print("Відео файл не створено")
                return {"audio": audio_path, "text": prompt, "error": "video_failed"}
        else:
            print("Не вдалося створити відео")
            return {"audio": audio_path, "text": prompt, "error": "video_creation_failed"}
            
    except Exception as e:
        print(f"Загальна помилка генерації відео: {e}")
        import traceback
        traceback.print_exc()
        return {"text": prompt, "error": "general_error"}