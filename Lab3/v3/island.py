# island.py - Завершенная версия с исправленной видимостью
import pygame
import random
import math
from config import ISLAND_GREEN, DARK_GREEN, RED, SCREEN_HEIGHT

class Island:
    def __init__(self, x, y, seed):
        self.x = x
        self.y = y
        self.radius = random.randint(50, 120)
        self.seed = seed
        random.seed(seed)
        self.points = self.generate_shape()
        self.has_structure = random.random() < 0.15
        
    def generate_shape(self):
        """Генерация органичной формы острова"""
        points = []
        num_points = 20
        
        for i in range(num_points):
            angle = (i / num_points) * 2 * math.pi
            # Добавляем шум для неровных краёв
            noise = random.uniform(0.7, 1.3)
            r = self.radius * noise
            x = self.x + math.cos(angle) * r
            y = self.y + math.sin(angle) * r
            points.append((x, y))
        
        return points
    
    def draw(self, screen, camera_y):
        adjusted_points = [(int(p[0]), int(p[1] - camera_y)) for p in self.points]
        
        # Проверка видимости - проверяем, находится ли остров в видимой области
        min_y = min(p[1] for p in adjusted_points)
        max_y = max(p[1] for p in adjusted_points)
        
        # Если остров полностью вне видимой области, не рисуем его
        if max_y < -200 or min_y > SCREEN_HEIGHT + 200:
            return
            
        pygame.draw.polygon(screen, ISLAND_GREEN, adjusted_points)
        pygame.draw.polygon(screen, DARK_GREEN, adjusted_points, 3)
        
        # Маяк
        if self.has_structure:
            struct_x = int(self.x)
            struct_y = int(self.y - camera_y)
            # Рисуем маяк только если он в видимой области
            if -100 < struct_y < SCREEN_HEIGHT + 100:
                pygame.draw.rect(screen, (139, 69, 19), 
                               (struct_x - 8, struct_y - 35, 16, 35))
                pygame.draw.polygon(screen, RED, [
                    (struct_x, struct_y - 45),
                    (struct_x - 12, struct_y - 35),
                    (struct_x + 12, struct_y - 35)
                ])
    
    def collides_with(self, x, y, radius=25):
        """Проверка столкновения с островом"""
        dx = x - self.x
        dy = y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        return dist < self.radius * 0.8 + radius