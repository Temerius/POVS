# utils.py
import pygame
import math

def load_image(path, default_size=(60, 60)):
    """Загрузка изображения с fallback"""
    try:
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, default_size)
    except:
        surf = pygame.Surface(default_size, pygame.SRCALPHA)
        if 'player' in path:
            surf.fill((100, 100, 100, 255))
        elif 'enemy_simple' in path:
            surf.fill((150, 75, 0, 255))
        elif 'enemy_hard' in path:
            surf.fill((80, 40, 0, 255))
        else:
            surf.fill((200, 200, 200, 255))
        return surf

def check_collision_circle(x1, y1, r1, x2, y2, r2):
    """Проверка столкновения двух окружностей"""
    dx = x1 - x2
    dy = y1 - y2
    dist = math.sqrt(dx * dx + dy * dy)
    return dist < r1 + r2