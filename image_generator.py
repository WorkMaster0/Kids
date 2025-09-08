from PIL import Image, ImageDraw, ImageFont
import random

def generate_video_image(prompt: str, filename: str):
    """Генерація зображення для відео"""
    try:
        width, height = 1024, 768
        
        # Створюємо градієнтний фон
        img = Image.new('RGB', (width, height), color='lightblue')
        draw = ImageDraw.Draw(img)
        
        # Градієнтний фон
        for y in range(height):
            r = int(135 + (120 * y / height))
            g = int(206 + (49 * y / height))
            b = int(250 - (50 * y / height))
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        
        # Кольори для дитячих зображень
        colors = ['#FF6B6B', '#4ECDC4', '#FFE66D', '#6B48FF', '#FF9F1C', '#FF48C4', '#2BD62B', '#FF8C42']
        
        # Сонце
        draw.ellipse([50, 50, 200, 200], fill='#FFE66D', outline='#FF9F1C')
        
        # Хмари
        for i in range(3):
            x = random.randint(250, 900)
            y = random.randint(50, 200)
            size = random.randint(80, 150)
            draw.ellipse([x, y, x+size, y+size//2], fill='white', outline='#E0E0E0')
        
        # Будинки
        for i in range(2):
            x = random.randint(100, 900)
            y = 400
            height_house = random.randint(150, 250)
            width_house = random.randint(120, 200)
            
            # Основа будинку
            color_idx = (i * 2) % len(colors)
            draw.rectangle([x, y, x+width_house, y+height_house], 
                          fill=colors[color_idx], outline='white')
            
            # Дах
            draw.polygon([(x-20, y), (x+width_house//2, y-50), (x+width_house+20, y)],
                        fill=colors[(color_idx + 1) % len(colors)], outline='white')
            
            # Вікно
            draw.rectangle([x+width_house//4, y+height_house//3, 
                          x+width_house*3//4, y+height_house*2//3],
                         fill='#FFFDE7', outline='white')
        
        # Дерева
        for i in range(3):
            x = random.randint(100, 924)
            y = 500
            # Ствол
            draw.rectangle([x, y, x+20, y+100], fill='#8B4513', outline='#654321')
            # Крона
            draw.ellipse([x-30, y-40, x+50, y+20], fill='#2E8B57', outline='#228B22')
        
        # Додаємо текст
        try:
            font = ImageFont.truetype("arial.ttf", 36)
        except:
            font = ImageFont.load_default()
        
        # Тінь для тексту
        draw.text((width//2+2, height//2+2), prompt, fill='white', 
                 font=font, anchor='mm')
        # Основний текст
        draw.text((width//2, height//2), prompt, fill='black', 
                 font=font, anchor='mm')
        
        img.save(filename)
        print(f"Зображення збережено: {filename}")
        return True
        
    except Exception as e:
        print(f"Помилка генерації зображення: {e}")
        return generate_simple_image(prompt, filename)

def generate_simple_image(prompt: str, filename: str):
    """Резервна генерація простого зображення"""
    try:
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
        
        return True
        
    except Exception as e:
        print(f"Помилка створення простого зображення: {e}")
        return False