# shore.py - Зубчатые берега по краям экрана
import pygame
import random
import math
from config import ISLAND_GREEN, DARK_GREEN, SCREEN_HEIGHT, SCREEN_WIDTH

class Shore:
    """Берег с зубчатыми краями (слева или справа)"""
    def __init__(self, side, start_y, end_y):
        self.side = side  # 'left' или 'right'
        self.start_y = start_y
        self.end_y = end_y
        self.points = self.generate_shore()
        
    def generate_shore(self):
        """Генерация зубчатых краёв берега"""
        points = []
        current_y = self.start_y
        
        if self.side == 'left':
            base_x = 0
            # Начинаем от левого края экрана
            points.append((0, current_y))
            
            while current_y > self.end_y:
                # Зубчатые выступы
                indent = random.randint(40, 100)
                segment_height = random.randint(80, 150)
                
                points.append((indent, current_y))
                current_y -= segment_height / 2
                points.append((indent + random.randint(-20, 20), current_y))
                current_y -= segment_height / 2
                
            points.append((0, self.end_y))
            
        else:  # right
            base_x = SCREEN_WIDTH
            points.append((SCREEN_WIDTH, current_y))
            
            while current_y > self.end_y:
                indent = random.randint(40, 100)
                segment_height = random.randint(80, 150)
                
                points.append((SCREEN_WIDTH - indent, current_y))
                current_y -= segment_height / 2
                points.append((SCREEN_WIDTH - indent + random.randint(-20, 20), current_y))
                current_y -= segment_height / 2
                
            points.append((SCREEN_WIDTH, self.end_y))
        
        return points
    
    def draw(self, screen, camera_y):
        """Отрисовка берега"""
        adjusted_points = [(int(p[0]), int(p[1] - camera_y)) for p in self.points]
        
        # Проверка видимости
        if any(-200 < p[1] < SCREEN_HEIGHT + 200 for p in adjusted_points):
            # Добавляем точки для замыкания полигона
            if self.side == 'left':
                # Замыкаем слева
                corner_points = [(0, SCREEN_HEIGHT + 200)] + adjusted_points + [(0, -200)]
            else:
                # Замыкаем справа
                corner_points = [(SCREEN_WIDTH, SCREEN_HEIGHT + 200)] + adjusted_points + [(SCREEN_WIDTH, -200)]
            
            pygame.draw.polygon(screen, ISLAND_GREEN, corner_points)
            pygame.draw.lines(screen, DARK_GREEN, False, adjusted_points, 4)
    
    def collides_with(self, x, y, radius=25):
        """Проверка столкновения с берегом"""
        if self.side == 'left':
            # Если корабль слишком близко к левому краю
            return x - radius < 120
        else:
            # Если корабль слишком близко к правому краю
            return x + radius > SCREEN_WIDTH - 120