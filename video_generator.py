import os
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip
from moviepy.audio.AudioClip import AudioArrayClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
import tempfile
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

def generate_story_from_topic(topic: str) -> str:
    """Генерація короткої історії на основі теми"""
    
    stories = {
        "динозавр": "Маленький динозаврик Дуся знайшов яйце з дивним блиском. Разом з друзями вони вирушили у подорож до Вулкану Чудес, де відкрили секрет древньої магії!",
        "космос": "Цуценятко-космонавт Барсік на ракеті 'Гав-Гав' летить до зірок. На шляху він рятує інопланетнят від злого метеорита і знаходить нових друзів!",
        "принцеса": "Принцеса Зірочка в зачарованому замку навчається чарівництву. Разом з єдинорогом Райдужкою вони рятують королівство від темряви!",
        "ліс": "Ведмежа Топта, лисичка Руда і зайчик Стрибун грають у хованки. Раптом вони знаходять таємну печеру з скарбами дружби!",
        "машинки": "Червона машинка Швидкість і синій автобус Веселун влаштовують перегони. Вчаться працювати разом і допомагати іншим!",
        "казка": "У країні Мрій живуть чарівні істоти. Сьогодні вони готують найбільший торт для свята Дружби!",
        "моря": "Медузка Блискітка і крабик Куцій досліджують кораловий риф. Знаходять скарб і рятують рибку від сітки!",
        "робот": "Робот Біп-Боп вчить дітей рахувати зірки. Разом вони будують місто Майбутнього з цукерок!"
    }
    
    # Шукаємо відповідну історію
    topic_lower = topic.lower()
    for key, story in stories.items():
        if key in topic_lower:
            return story
    
    # Якщо тема не знайдена, обираємо випадкову історію
    return random.choice(list(stories.values()))

def download_background_music():
    """Завантажуємо фонову музику (безкоштовну)"""
    try:
        # Безкоштовна дитяча музика з YouTube Audio Library
        music_urls = [
            "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
            "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
            "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3"
        ]
        
        temp_dir = tempfile.mkdtemp()
        music_path = os.path.join(temp_dir, "background_music.mp3")
        
        # Завантажуємо музику
        response = requests.get(random.choice(music_urls), timeout=10)
        if response.status_code == 200:
            with open(music_path, 'wb') as f:
                f.write(response.content)
            return music_path
    except:
        pass
    return None

def create_cartoon_animation(prompt: str, output_path: str, duration: int = 15):
    """Створення мультфільму з анімацією"""
    try:
        width, height = 1024, 768
        fps = 24
        total_frames = duration * fps
        
        # Створюємо кадри для анімації
        frames = []
        
        for i in range(total_frames):
            # Створюємо нове зображення для кожного кадру
            img = Image.new('RGB', (width, height), color='lightblue')
            draw = ImageDraw.Draw(img)
            
            # Анімований градієнтний фон
            progress = i / total_frames
            for y in range(height):
                r = int(135 + (120 * y / height) + 50 * np.sin(progress * 10))
                g = int(206 + (49 * y / height) + 30 * np.cos(progress * 8))
                b = int(250 - (50 * y / height) + 40 * np.sin(progress * 12))
                draw.line([(0, y), (width, y)], fill=(r, g, b))
            
            # Анімоване сонце
            sun_x = 100 + 50 * np.sin(progress * 5)
            sun_y = 100 + 30 * np.cos(progress * 3)
            draw.ellipse([sun_x, sun_y, sun_x+150, sun_y+150], fill='#FFE66D', outline='#FF9F1C')
            
            # Анімовані хмари
            for cloud_i in range(3):
                cloud_x = 300 + cloud_i * 200 + 20 * np.sin(progress * 2 + cloud_i)
                cloud_y = 80 + 10 * np.cos(progress * 3 + cloud_i)
                size = 100 + 20 * np.sin(progress * 4 + cloud_i)
                draw.ellipse([cloud_x, cloud_y, cloud_x+size, cloud_y+size//2], fill='white', outline='#E0E0E0')
            
            # Анімовані будинки
            for house_i in range(2):
                house_x = 200 + house_i * 400 + 5 * np.sin(progress * 3 + house_i)
                house_y = 400 + 3 * np.cos(progress * 2 + house_i)
                
                # Основа будинку
                colors = ['#FF6B6B', '#4ECDC4', '#FFE66D', '#6B48FF']
                draw.rectangle([house_x, house_y, house_x+180, house_y+200], 
                              fill=colors[house_i % len(colors)], outline='white')
                
                # Дах
                draw.polygon([
                    (house_x-15, house_y), 
                    (house_x+90, house_y-60), 
                    (house_x+195, house_y)
                ], fill=colors[(house_i + 1) % len(colors)], outline='white')
                
                # Вікно
                draw.rectangle([
                    house_x+45, house_y+50, 
                    house_x+135, house_y+150
                ], fill='#FFFDE7', outline='white')
            
            # Анімовані дерева
            for tree_i in range(3):
                tree_x = 150 + tree_i * 300 + 8 * np.sin(progress * 4 + tree_i)
                tree_y = 500 + 5 * np.cos(progress * 3 + tree_i)
                
                # Ствол
                draw.rectangle([tree_x, tree_y, tree_x+25, tree_y+120], fill='#8B4513', outline='#654321')
                
                # Крона (анімована)
                crown_size = 70 + 10 * np.sin(progress * 6 + tree_i)
                draw.ellipse([
                    tree_x-35, tree_y-40, 
                    tree_x+60, tree_y+30
                ], fill='#2E8B57', outline='#228B22')
            
            # Текст (з'являється повільно)
            if i > total_frames // 4:
                try:
                    font = ImageFont.truetype("arial.ttf", 32)
                except:
                    font = ImageFont.load_default()
                
                alpha = min(1.0, (i - total_frames // 4) / (total_frames // 4))
                text_color = (0, 0, 0, int(255 * alpha))
                
                # Тінь
                draw.text((width//2+3, height-60+3), prompt, fill=(255, 255, 255, int(200 * alpha)), 
                         font=font, anchor='mm')
                # Основний текст
                draw.text((width//2, height-60), prompt, fill=text_color, 
                         font=font, anchor='mm')
            
            frames.append(np.array(img))
        
        print(f"Створено {len(frames)} кадрів анімації")
        
        # Завантажуємо фонову музику
        music_path = download_background_music()
        
        # Створюємо відео з кадрів
        clip = ImageClip(frames[0]).set_duration(duration)
        if len(frames) > 1:
            clip = clip.set_fps(fps)
        
        # Додаємо музику
        if music_path and os.path.exists(music_path):
            try:
                music_clip = AudioFileClip(music_path).volumex(0.3)
                if music_clip.duration > duration:
                    music_clip = music_clip.subclip(0, duration)
                clip = clip.set_audio(music_clip)
            except:
                pass
        
        # Записуємо відео
        clip.write_videofile(
            output_path,
            fps=fps,
            codec='libx264',
            audio_codec='aac',
            preset='fast',
            verbose=False,
            logger=None
        )
        
        # Очищаємо ресурси
        clip.close()
        if music_path and os.path.exists(music_path):
            try:
                os.remove(music_path)
            except:
                pass
        
        return True
        
    except Exception as e:
        print(f"Помилка створення анімації: {e}")
        import traceback
        traceback.print_exc()
        return False

async def generate_cartoon(topic: str, user_id: str):
    """Генерація мультфільму"""
    try:
        print(f"Створення мультфільму для теми: {topic}")
        
        # Генеруємо історію
        story_text = generate_story_from_topic(topic)
        print(f"Історія: {story_text}")
        
        # Створюємо тимчасову папку
        temp_dir = tempfile.mkdtemp()
        video_path = os.path.join(temp_dir, "cartoon.mp4")
        
        # Створюємо мультфільм
        if create_cartoon_animation(story_text, video_path, duration=12):
            if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
                return video_path
            else:
                print("Мультфільм не створено")
                return {"text": story_text, "error": "animation_failed"}
        else:
            print("Не вдалося створити мультфільм")
            return {"text": story_text, "error": "animation_creation_failed"}
            
    except Exception as e:
        print(f"Загальна помилка: {e}")
        import traceback
        traceback.print_exc()
        return {"text": generate_story_from_topic(topic), "error": "general_error"}