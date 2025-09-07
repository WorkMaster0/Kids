import openai
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

# Налаштування OpenAI (для DALL-E)
openai.api_key = "YOUR_OPENAI_API_KEY"

def generate_ai_image(prompt: str, filename: str):
    """Генерація зображення через DALL-E"""
    try:
        response = openai.Image.create(
            prompt=f"Дитяче яскраве мультяшне зображення: {prompt}",
            n=1,
            size="1024x768"
        )
        
        image_url = response['data'][0]['url']
        image_data = requests.get(image_url).content
        image = Image.open(BytesIO(image_data))
        image.save(filename)
        
        return filename
        
    except Exception as e:
        # Резервний варіант - просте зображення
        print(f"Помилка DALL-E: {e}")
        return generate_simple_image(prompt, filename)

def generate_simple_image(prompt: str, filename: str):
    """Резервна генерація простого зображення"""
    width, height = 1024, 768
    img = Image.new('RGB', (width, height), color='lightblue')
    draw = ImageDraw.Draw(img)
    
    # Додаємо текст
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()
    
    draw.text((width//2, height//2), prompt, fill='black', font=font, anchor='mm')
    img.save(filename)
    
    return filename
    
    def generate_story_image(prompt: str, filename: str):
    """Генерація зображення для сцени історії"""
    try:
        width, height = 1024, 768
        img = Image.new('RGB', (width, height), color='lightblue')
        draw = ImageDraw.Draw(img)
        
        # Кольори для дитячих зображень
        colors = ['#FF6B6B', '#4ECDC4', '#FFE66D', '#6B48FF', '#FF9F1C']
        
        # Малюємо яскраві фігури
        for i in range(8):
            color = colors[i % len(colors)]
            x1, y1 = random.randint(0, width), random.randint(0, height)
            size = random.randint(50, 200)
            
            if random.choice([True, False]):
                draw.rectangle([x1, y1, x1+size, y1+size], fill=color, outline='white')
            else:
                draw.ellipse([x1, y1, x1+size, y1+size], fill=color, outline='white')
        
        # Додаємо текст сцени
        try:
            font = ImageFont.truetype("arial.ttf", 30)
            words = prompt.split()[:10]  # Перші 10 слів
            short_prompt = ' '.join(words)
            draw.text((width//2, height-50), short_prompt, fill='black', 
                     font=font, anchor='mm')
        except:
            pass
        
        img.save(filename)
        return True
        
    except Exception as e:
        print(f"Помилка генерації зображення: {e}")
        return False