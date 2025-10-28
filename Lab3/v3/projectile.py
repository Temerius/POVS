# projectile.py - Полностью исправленный класс снаряда
import pygame
import math
from config import *

class Projectile:
    def __init__(self, x, y, angle, speed=4.0, color=(255, 255, 0), is_player_shot=True):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.color = color
        self.lifetime = 90  # 1.5 секунды при 60 FPS
        self.radius = 5
        self.is_player_shot = is_player_shot
    
    def update(self):
        """Обновление позиции снаряда"""
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.lifetime -= 1
    
    def collides_with(self, obstacle):
        """Проверка столкновения с объектом"""
        if hasattr(obstacle, 'contains_point') and obstacle.contains_point(self.x, self.y, self.radius):
            return True
        elif hasattr(obstacle, 'x') and hasattr(obstacle, 'y') and hasattr(obstacle, 'radius'):
            # Расчет расстояния до центра объекта
            dx = self.x - obstacle.x
            dy = self.y - obstacle.y
            distance = math.sqrt(dx*dx + dy*dy)
            return distance < self.radius + obstacle.radius
        return False
    
    def draw(self, screen, camera_y):
        """Отрисовка снаряда"""
        y_screen = int(self.y - camera_y)
        pygame.draw.circle(screen, self.color, (int(self.x), int(y_screen)), self.radius)