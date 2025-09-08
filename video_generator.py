import os
import requests
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, TextClip
from moviepy.config import change_settings
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import random

# Налаштування FFmpeg
change_settings({"FFMPEG_BINARY": "/usr/bin/ffmpeg"})

def generate_story(topic: str) -> str:
    """Генерація цікавих дитячих історій"""
    
    # База персонажів
    characters = {
        "тварини": ["🐻 Ведмежик Топтижка", "🐰 Кролик Стрибунчик", "🦊 Лисичка Сестричка", 
                   "🐭 Мишка Цвіркун", "🐸 Жаба Квакушка", "🦉 Сова Розумница"],
        "персонажі": ["👦 Хлопчик Андрійко", "👧 Дівчинка Софійка", "🧙 Чарівник Зірочка",
                     "👸 Принцеса Мрія", "🦸 Супергерой Світлик"],
        "фантастичні": ["👽 Інопланетянин Глік", "🤖 Робот Біп-Боп", "🦄 Єдиноріг Місячик",
                       "🐉 Дракончик Іскринка", "🧚 Фея Квіточка"]
    }
    
    # База локацій
    locations = ["у чарівному лісі 🌳", "на хмарній планеті ☁️", "у підводному царстві 🐠", 
                "в замку з цукерок 🍭", "у країні мрій 🌈", "на дитячому майданчику 🎪"]
    
    # База пригод
    adventures = {
        "знахідка": ["знайшли чарівний ключик 🗝️", "відкрили таємну карту 🗺️", 
                    "знайшли дивну іграшку 🧸", "виявили портал у інший світ 🌀"],
        "рятування": ["рятували маленького пташка 🐦", "допомагали втраченому цуценятку 🐶",
                     "лікували хворого деревце 🌱", "рятували річку від забруднення 💧"],
        "дослідження": ["досліджували печеру з кристалами 💎", "вивчали зірки телескопом 🔭",
                       "шукали древні артефакти 🏺", "досліджували підводний світ 🐙"],
        "святкування": ["готувалися до дня народження 🎂", "організовували лісовий бал 🎪",
                       "готували сюрприз для друзів 🎁", "влаштовували конкурс талантів 🎤"]
    }
    
    # Обираємо випадкові елементи
    character_type = random.choice(list(characters.keys()))
    character = random.choice(characters[character_type])
    location = random.choice(locations)
    adventure_type = random.choice(list(adventures.keys()))
    adventure = random.choice(adventures[adventure_type])
    
    # Теми для особливих запитів
    special_topics = {
        "динозавр": "🦖 Пригоди динозаврика Дусі у юрському періоді!",
        "космос": "🚀 Подорож до зірок на ракеті-цуценятку!",
        "моря": "🐳 Підводна пригода з морською зірочкою!",
        "ліс": "🌳 Історія про дружбу лісових звірят!",
        "казка": "📖 Чарівна казка з добрим кінцем!",
        "пісня": "🎵 Весела пісенька-пригода!"
    }
    
    # Генеруємо історію
    if topic.lower() in special_topics:
        story = special_topics[topic.lower()]
    else:
        story = (
            f"{character} {location} {adventure}. "
            f"Разом з друзями вони вчилися дружбі та доброті! "
            f"Історія закінчилася щасливо з мораллю: завжди допомагай іншим! 🌟"
        )
    
    return story

def generate_story_scenes(story_text: str):
    """Генерація сцен для історії"""
    scenes = []
    
    # Розбиваємо історію на сцени
    parts = story_text.split('. ')
    for i, part in enumerate(parts[:3]):  # Максимум 3 сцени
        if part.strip():
            scenes.append({
                "text": part + '.',
                "image_prompt": f"Дитяче мультяшне зображення: {part}",
                "duration": 10  # секунд на сцену
            })
    
    return scenes

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
        
        # Якщо немає зображень, повертаємо тільки текст
        return {"text": story_text}
        
    except Exception as e:
        print(f"Помилка генерації відео: {e}")
        # ВИПРАВЛЕНО: повертаємо словник, а не рядок
        return {"text": generate_story(topic)}