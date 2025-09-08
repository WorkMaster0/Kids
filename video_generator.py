import os
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
import tempfile
import random
import numpy as np
from PIL import Image, ImageDraw
import requests

def generate_story_from_topic(topic: str) -> str:
    """Генерація короткої історії на основі теми"""
    
    stories = {
        "динозавр": "Пригоди динозаврика Дуси!",
        "космос": "Подорож до зірок!",
        "принцеса": "Чарівна принцеса!",
        "ліс": "Лісові друзі!",
        "машинки": "Веселі перегони!",
        "казка": "Чарівна казка!",
        "моря": "Підводна пригода!",
        "робот": "Робот-помічник!"
    }
    
    topic_lower = topic.lower()
    for key, story in stories.items():
        if key in topic_lower:
            return story
    
    return random.choice(list(stories.values()))

def create_lightweight_animation(prompt: str, output_path: str, duration: int = 8):
    """Створення легкого мультфільму"""
    try:
        width, height = 640, 480  # Зменшили розмір
        fps = 15  # Зменшили FPS
        
        # Створюємо кілька ключових кадрів (не всі!)
        key_frames = []
        for i in range(5):  # Тільки 5 кадрів замість сотень
            img = Image.new('RGB', (width, height), color='lightblue')
            draw = ImageDraw.Draw(img)
            
            # Простий фон
            for y in range(0, height, 10):  # Крок 10 для економії
                r = 135 + int(120 * y / height)
                g = 206 + int(49 * y / height)
                b = 250 - int(50 * y / height)
                draw.line([(0, y), (width, y)], fill=(r, g, b))
            
            # Статичні елементи (без анімації)
            draw.ellipse([50, 50, 150, 150], fill='#FFE66D')
            
            # Будинок
            draw.rectangle([200, 300, 350, 450], fill='#FF6B6B')
            draw.polygon([(175, 300), (275, 200), (375, 300)], fill='#4ECDC4')
            
            # Текст
            try:
                from PIL import ImageFont
                font = ImageFont.load_default()
                draw.text((width//2, height-50), prompt, fill='black', font=font, anchor='mm')
            except:
                draw.text((width//2, height-50), prompt, fill='black', anchor='mm')
            
            key_frames.append(np.array(img))
        
        # Використовуємо тільки один кадр (статичне зображення)
        if key_frames:
            # Зберігаємо статичне зображення
            static_frame = Image.fromarray(key_frames[0])
            temp_img_path = output_path.replace('.mp4', '.png')
            static_frame.save(temp_img_path)
            
            # Створюємо відео з одного кадру + музика
            clip = ImageClip(temp_img_path).set_duration(duration)
            
            # Додаємо просту музику (створюємо самі)
            try:
                # Створюємо простий аудіо кліп (тиша з шумом)
                sample_rate = 44100
                t = np.linspace(0, duration, int(sample_rate * duration))
                audio_data = 0.1 * np.sin(2 * np.pi * 440 * t)  # Простий тон
                audio_clip = AudioArrayClip(audio_data.reshape(-1, 1), fps=sample_rate)
                clip = clip.set_audio(audio_clip)
            except:
                pass
            
            # Записуємо відео з низькою якістю
            clip.write_videofile(
                output_path,
                fps=fps,
                codec='libx264',
                audio_codec='aac',
                bitrate='500k',  # Низький бітрейт
                preset='ultrafast',  # Найшвидший preset
                verbose=False,
                logger=None,
                threads=1  # Тільки один потік
            )
            
            # Очищаємо
            clip.close()
            if os.path.exists(temp_img_path):
                os.remove(temp_img_path)
            
            return True
        
        return False
        
    except Exception as e:
        print(f"Помилка створення легкого відео: {e}")
        return False

async def generate_cartoon(topic: str, user_id: str):
    """Генерація мультфільму"""
    try:
        print(f"Створення мультфільму для: {topic}")
        
        story_text = generate_story_from_topic(topic)
        
        temp_dir = tempfile.mkdtemp()
        video_path = os.path.join(temp_dir, "cartoon.mp4")
        
        if create_lightweight_animation(story_text, video_path, duration=6):  # Коротше відео
            if os.path.exists(video_path):
                file_size = os.path.getsize(video_path) / (1024 * 1024)
                print(f"Розмір відео: {file_size:.2f} MB")
                
                if file_size > 10:  # Якщо занадто велике
                    os.remove(video_path)
                    return {"text": story_text, "error": "video_too_large"}
                
                return video_path
            
        return {"text": story_text, "error": "creation_failed"}
            
    except Exception as e:
        print(f"Помилка: {e}")
        return {"text": generate_story_from_topic(topic), "error": "general_error"}