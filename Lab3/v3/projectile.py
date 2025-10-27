# projectile.py - Исправленная отрисовка
import pygame
import math
from config import BLACK, SCREEN_HEIGHT

class Projectile:
    def __init__(self, x, y, angle, speed=12):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.radius = 5
        self.lifetime = 150
        
    def update(self):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.lifetime -= 1
        
    def draw(self, screen, camera_y):
        screen_y = int(self.y - camera_y)
        
        # Проверяем видимость снаряда
        if screen_y < -50 or screen_y > SCREEN_HEIGHT + 50:
            return
            
        pygame.draw.circle(screen, BLACK, (int(self.x), screen_y), self.radius)
        pygame.draw.circle(screen, (255, 150, 0), (int(self.x), screen_y), self.radius - 2)