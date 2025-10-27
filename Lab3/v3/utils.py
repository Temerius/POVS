# utils.py - Добавлена обработка ошибок
import pygame
import os
from config import WHITE

def load_image(path, default_size=(60, 60)):
    """Загрузка изображения с fallback"""
    try:
        # Проверяем, существует ли файл
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.scale(img, default_size)
    except Exception as e:
        print(f"Ошибка загрузки изображения {path}: {e}")
    
    # Создаем заглушку
    surf = pygame.Surface(default_size, pygame.SRCALPHA)
    pygame.draw.rect(surf, (100, 100, 100), (5, 5, default_size[0]-10, default_size[1]-10), 2)
    pygame.draw.line(surf, WHITE, (0, 0), (default_size[0], default_size[1]), 2)
    pygame.draw.line(surf, WHITE, (default_size[0], 0), (0, default_size[1]), 2)
    return surf