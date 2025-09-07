import os
import requests
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, TextClip
from moviepy.config import change_settings
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# Налаштування FFmpeg
change_settings({"FFMPEG_BINARY": "/usr/bin/ffmpeg"})

def generate_story(topic: str) -> str:
    """Генерація тексту історії (спрощена версія)"""
    stories = {
        "анімація": "Пригоди веселих звіряток у лісі! 🐻🐰🌳",
        "казка": "Жили-були три поросятка. Вони будували будинки... 🐷🐷🐷",
        "навчання": "Вчимо кольори весело! Червоний, синій, зелений... 🌈",
        "пісня": "Ла-ла-ла, весела пісенька для діточок! 🎵"
    }
    
    return stories.get(topic.lower(), f"Цікава історія про {topic}! 📚")

def generate_image(scene_description: str, filename: str):
    """Генерація зображення (спрощена версія)"""
    # Тут буде інтеграція з Stable Diffusion/DALL-E
    # Зараз створюємо просте зображення
    width, height = 1024, 768
    img = Image.new('RGB', (width, height), color='lightblue')
    draw = ImageDraw.Draw(img)
    
    # Проста графіка
    draw.rectangle([100, 100, 300, 300], fill='yellow', outline='orange')
    draw.ellipse([600, 200, 800, 400], fill='green')
    
    img.save(filename)
    return filename

def generate_audio(text: str, filename: str):
    """Генерація аудіо (текст у мову)"""
    tts = gTTS(text=text, lang='uk', slow=False)
    tts.save(filename)
    return filename

async def generate_children_video(topic: str, user_id: str):
    """Основна функція генерації відео"""
    try:
        # Створюємо папку для користувача
        user_dir = f"assets/user_{user_id}"
        os.makedirs(user_dir, exist_ok=True)
        
        # Генеруємо контент
        story_text = generate_story(topic)
        audio_path = f"{user_dir}/audio.mp3"
        video_path = f"{user_dir}/video.mp4"
        
        # Генеруємо аудіо
        generate_audio(story_text, audio_path)
        
        # Генеруємо кілька сцен
        clips = []
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration
        
        # Створюємо прості сцени
        for i in range(3):
            scene_path = f"{user_dir}/scene_{i}.png"
            generate_image(f"Сцена {i} для {topic}", scene_path)
            
            image_clip = ImageClip(scene_path).set_duration(duration/3)
            clips.append(image_clip)
        
        # Створюємо відео
        final_clip = CompositeVideoClip(clips).set_audio(audio_clip)
        final_clip.write_videofile(
            video_path,
            fps=24,
            codec='libx264',
            audio_codec='aac'
        )
        
        # Очищаємо тимчасові файли
        for file in os.listdir(user_dir):
            if file != "video.mp4":
                os.remove(f"{user_dir}/{file}")
        
        return video_path
        
    except Exception as e:
        print(f"Помилка генерації відео: {e}")
        return None