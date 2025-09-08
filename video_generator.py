import os
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
import random
import tempfile

def generate_story(topic: str) -> str:
    """Генерація цікавих дитячих історій"""
    
    # База персонажів
    characters = {
        "тварини": ["Ведмежик Топтижка", "Кролик Стрибунчик", "Лисичка Сестричка", 
                   "Мишка Цвіркун", "Жаба Квакушка", "Сова Розумница"],
        "персонажі": ["Хлопчик Андрійко", "Дівчинка Софійка", "Чарівник Зірочка",
                     "Принцеса Мрія", "Супергерой Світлик"],
        "фантастичні": ["Інопланетянин Глік", "Робот Біп-Боп", "Єдиноріг Місячик",
                       "Дракончик Іскринка", "Фея Квіточка"]
    }
    
    # База локацій
    locations = ["у чарівному лісі", "на хмарній планеті", "у підводному царстві", 
                "в замку з цукерок", "у країні мрій", "на дитячому майданчику"]
    
    # База пригод
    adventures = {
        "знахідка": ["знайшли чарівний ключик", "відкрили таємну карту", 
                    "знайшли дивну іграшку", "виявили портал у інший світ"],
        "рятування": ["рятували маленького пташка", "допомагали втраченому цуценятку",
                     "лікували хворого деревце", "рятували річку від забруднення"],
        "дослідження": ["досліджували печеру з кристалами", "вивчали зірки телескопом",
                       "шукали древні артефакти", "досліджували підводний світ"],
        "святкування": ["готувалися до дня народження", "організовували лісовий бал",
                       "готували сюрприз для друзів", "влаштовували конкурс талантів"]
    }
    
    # Обираємо випадкові елементи
    character_type = random.choice(list(characters.keys()))
    character = random.choice(characters[character_type])
    location = random.choice(locations)
    adventure_type = random.choice(list(adventures.keys()))
    adventure = random.choice(adventures[adventure_type])
    
    # Теми для особливих запитів
    special_topics = {
        "динозавр": "Пригоди динозаврика Дусі у юрському періоді!",
        "космос": "Подорож до зірок на ракеті-цуценятку!",
        "моря": "Підводна пригода з морською зірочкою!",
        "ліс": "Історія про дружбу лісових звірят!",
        "казка": "Чарівна казка з добрим кінцем!",
        "пісня": "Весела пісенька-пригода!",
        "машинки": "Гонки маленьких машинок у місті іграшок!",
        "принцеса": "Пригоди принцеси у зачарованому замку!"
    }
    
    # Генеруємо історію
    if topic.lower() in special_topics:
        story = special_topics[topic.lower()]
    else:
        story = (
            f"{character} {location} {adventure}. "
            f"Разом з друзями вони вчилися дружбі та доброті! "
            f"Історія закінчилася щасливо з мораллю: завжди допомагай іншим!"
        )
    
    return story

def generate_story_scenes(story_text: str):
    """Генерація сцен для історії"""
    scenes = []
    
    # Розбиваємо історію на сцени
    parts = story_text.split('. ')
    for i, part in enumerate(parts[:4]):  # Максимум 4 сцени
        if part.strip() and len(part) > 10:  # Мінімальна довжина сцени
            scenes.append({
                "text": part + '.',
                "image_prompt": f"Дитяче мультяшне зображення: {part}",
                "duration": 7  # секунд на сцену
            })
    
    return scenes

def generate_audio(text: str, filename: str):
    """Генерація аудіо (текст у мову)"""
    try:
        tts = gTTS(text=text, lang='uk', slow=False)
        tts.save(filename)
        return filename
    except Exception as e:
        print(f"Помилка генерації аудіо: {e}")
        # Створюємо пустий аудіо файл як заглушку
        with open(filename, 'wb') as f:
            f.write(b'')  # Пустий файл
        return filename

async def generate_children_video(topic: str, user_id: str):
    """Генерація повноцінного дитячого відео"""
    try:
        # Генеруємо історію
        story_text = generate_story(topic)
        scenes = generate_story_scenes(story_text)
        
        if not scenes:
            return {"text": story_text}
        
        # Створюємо тимчасову папку
        temp_dir = tempfile.mkdtemp()
        audio_path = os.path.join(temp_dir, "story_audio.mp3")
        
        # Генеруємо аудіо історії
        generate_audio(story_text, audio_path)
        
        # Генеруємо зображення для кожної сцени
        image_paths = []
        for i, scene in enumerate(scenes):
            img_path = os.path.join(temp_dir, f"scene_{i}.png")
            from Image_generator import generate_story_image
            if generate_story_image(scene['image_prompt'], img_path):
                image_paths.append(img_path)
        
        # Перевіряємо чи є зображення
        if not image_paths:
            return {"text": story_text}
        
        # Створюємо відео
        try:
            audio_clip = AudioFileClip(audio_path)
            total_duration = audio_clip.duration
            scene_duration = total_duration / len(image_paths)
            
            clips = []
            for img_path in image_paths:
                clip = ImageClip(img_path).set_duration(scene_duration)
                clips.append(clip)
            
            final_clip = concatenate_videoclips(clips).set_audio(audio_clip)
            video_path = os.path.join(temp_dir, "final_video.mp4")
            
            # Налаштування для кращої якості
            final_clip.write_videofile(
                video_path, 
                fps=24, 
                codec='libx264', 
                audio_codec='aac',
                threads=4,
                preset='fast',
                ffmpeg_params=['-crf', '23']
            )
            
            return video_path
            
        except ImportError as e:
            print(f"MoviePy не встановлено: {e}")
            return {
                "audio": audio_path,
                "images": image_paths,
                "text": story_text
            }
        except Exception as e:
            print(f"Помилка створення відео: {e}")
            return {
                "audio": audio_path,
                "images": image_paths,
                "text": story_text
            }
        
    except Exception as e:
        print(f"Помилка генерації відео: {e}")
        return {"text": generate_story(topic)}