import os
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from gtts import gTTS
import tempfile
import random

def generate_story_from_topic(topic: str) -> str:
    """Генерація короткої історії на основі теми"""
    
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
    
    # Теми для особливих запитів
    special_topics = {
        "динозавр": "Динозаврик Дуся вирушив у неймовірну пригоду юрського періоду!",
        "космос": "Ракета-цуценятко летить до зірок назустріч неймовірним пригодам!",
        "моря": "Морська зірочка відкриває таємниці підводного світу!",
        "ліс": "Лісові звірята разом вчать нас дружбі та доброті!",
        "казка": "Чарівна казка з добрим кінцем та мораллю для дітей!",
        "пісня": "Весела пісенька-пригода розкаже про сміливих героїв!",
        "машинки": "Маленькі машинки влаштовують захоплюючі гонки у місті іграшок!",
        "принцеса": "Принцеса у зачарованому замку навчається доброті та мужності!"
    }
    
    # Перевіряємо спеціальні теми
    topic_lower = topic.lower()
    for key, story in special_topics.items():
        if key in topic_lower:
            return story
    
    # Генеруємо історію на основі загальних слів
    if any(word in topic_lower for word in ["тварин", "звір", "ведме", "лиси", "кролик"]):
        character_type = "тварини"
    elif any(word in topic_lower for word in ["хлопчик", "дівчинка", "принцеса", "герой"]):
        character_type = "персонажі"
    elif any(word in topic_lower for word in ["космос", "робот", "дракон", "фея"]):
        character_type = "фантастичні"
    else:
        character_type = random.choice(list(characters.keys()))
    
    # Обираємо випадкові елементи
    character = random.choice(characters[character_type])
    location = random.choice(locations)
    adventure_type = random.choice(list(adventures.keys()))
    adventure = random.choice(adventures[adventure_type])
    
    # Генеруємо історію
    story = (
        f"{character} {location} {adventure}. "
        f"Разом з друзями вони вчилися дружбі та доброті! "
        f"Історія закінчилася щасливо!"
    )
    
    return story

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

async def generate_video_with_audio(topic: str, user_id: str):
    """Генерація відео з аудіо на основі теми"""
    try:
        print(f"Початок генерації для теми: {topic}")
        
        # Генеруємо історію на основі теми
        story_text = generate_story_from_topic(topic)
        print(f"Згенерована історія: {story_text}")
        
        # Створюємо тимчасову папку
        temp_dir = tempfile.mkdtemp()
        print(f"Тимчасова папка: {temp_dir}")
        
        # Генеруємо аудіо
        audio_path = os.path.join(temp_dir, "audio.mp3")
        if not generate_audio(story_text, audio_path):
            return {"text": story_text, "error": "audio_failed"}
        
        # Перевіряємо чи існує аудіо файл
        if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
            print("Аудіо файл не створено")
            return {"text": story_text, "error": "audio_empty"}
        
        # Створюємо відео
        video_path = os.path.join(temp_dir, "video.mp4")
        if create_video_from_audio(audio_path, story_text, video_path):
            if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
                return video_path
            else:
                print("Відео файл не створено")
                return {"audio": audio_path, "text": story_text, "error": "video_failed"}
        else:
            print("Не вдалося створити відео")
            return {"audio": audio_path, "text": story_text, "error": "video_creation_failed"}
            
    except Exception as e:
        print(f"Загальна помилка генерації відео: {e}")
        import traceback
        traceback.print_exc()
        return {"text": generate_story_from_topic(topic), "error": "general_error"}