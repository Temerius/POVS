# projectile.py - Снаряды игрока и врагов

import pygame
import math
from config import *

class Projectile:
    def __init__(self, x, y, angle, speed=PROJECTILE_SPEED, 
                 color=PROJECTILE_COLOR_PLAYER, is_player_shot=True):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.color = color
        self.lifetime = PROJECTILE_LIFETIME
        self.radius = PROJECTILE_RADIUS
        self.is_player_shot = is_player_shot
    
    def update(self):
        """Обновление позиции снаряда"""
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.lifetime -= 1
    
    def collides_with(self, obstacle):
        """Проверка столкновения с объектом"""
        # Берега и острова
        if hasattr(obstacle, 'contains_point') and obstacle.contains_point(self.x, self.y, self.radius):
            return True
        
        # Враги и другие объекты с координатами и радиусом
        if hasattr(obstacle, 'x') and hasattr(obstacle, 'y') and hasattr(obstacle, 'radius'):
            dx = self.x - obstacle.x
            dy = self.y - obstacle.y
            distance = math.sqrt(dx*dx + dy*dy)
            return distance < self.radius + obstacle.radius
        
        return False
    
    def draw(self, screen, camera_y):
        """Отрисовка снаряда"""
        y_screen = int(self.y - camera_y)
        pygame.draw.circle(screen, self.color, (int(self.x), y_screen), self.radius)