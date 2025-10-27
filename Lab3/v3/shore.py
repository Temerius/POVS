# shore.py - Полностью исправленный класс берегов
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
            
            while current_y < self.end_y:  # Идём вниз (y увеличивается)
                # Зубчатые выступы
                indent = random.randint(40, 100)
                segment_height = random.randint(80, 150)
                
                points.append((indent, current_y))
                current_y += segment_height / 2
                points.append((indent + random.randint(-20, 20), current_y))
                current_y += segment_height / 2
                
            points.append((0, self.end_y))
            
        else:  # right
            base_x = SCREEN_WIDTH
            points.append((SCREEN_WIDTH, current_y))
            
            while current_y < self.end_y:  # Идём вниз (y увеличивается)
                indent = random.randint(40, 100)
                segment_height = random.randint(80, 150)
                
                points.append((SCREEN_WIDTH - indent, current_y))
                current_y += segment_height / 2
                points.append((SCREEN_WIDTH - indent + random.randint(-20, 20), current_y))
                current_y += segment_height / 2
                
            points.append((SCREEN_WIDTH, self.end_y))
        
        return points
    
    def draw(self, screen, camera_y):
        """Отрисовка берега"""
        adjusted_points = [(int(p[0]), int(p[1] - camera_y)) for p in self.points]
        
        # Проверка видимости
        visible = False
        for p in adjusted_points:
            if -100 < p[1] < SCREEN_HEIGHT + 100:
                visible = True
                break
        
        if not visible:
            return
        
        if self.side == 'left':
            # Создаем замкнутый полигон для левого берега
            # Начинаем с верхнего левого угла экрана
            polygon_points = [(0, -200)]
            # Добавляем все точки берега
            polygon_points.extend(adjusted_points)
            # Заканчиваем в нижнем левом углу экрана
            polygon_points.append((0, SCREEN_HEIGHT + 200))
        else:
            # Для правого берега
            polygon_points = [(SCREEN_WIDTH, -200)]
            polygon_points.extend(adjusted_points)
            polygon_points.append((SCREEN_WIDTH, SCREEN_HEIGHT + 200))
        
        # Рисуем полигон земли
        pygame.draw.polygon(screen, ISLAND_GREEN, polygon_points)
        # Рисуем контур береговой линии
        pygame.draw.lines(screen, DARK_GREEN, False, adjusted_points, 4)
    
    def collides_with(self, x, y, radius=25):
        """Проверка столкновения с берегом"""
        if self.side == 'left':
            # Проверяем расстояние до ближайшей точки берега
            for i in range(len(self.points) - 1):
                x1, y1 = self.points[i]
                x2, y2 = self.points[i+1]
                # Расстояние от точки до отрезка
                dist = self.point_to_segment_distance(x, y, x1, y1, x2, y2)
                if dist < radius + 10:  # Небольшой запас
                    return True
            return False
        else:
            # То же самое для правого берега
            for i in range(len(self.points) - 1):
                x1, y1 = self.points[i]
                x2, y2 = self.points[i+1]
                dist = self.point_to_segment_distance(x, y, x1, y1, x2, y2)
                if dist < radius + 10:
                    return True
            return False
    
    def point_to_segment_distance(self, px, py, x1, y1, x2, y2):
        """Расстояние от точки до отрезка"""
        # Вектор от начальной точки отрезка к конечной
        line_vec = (x2 - x1, y2 - y1)
        # Вектор от начальной точки отрезка к точке
        point_vec = (px - x1, py - y1)
        
        # Длина линии в квадрате
        line_len_sq = line_vec[0]**2 + line_vec[1]**2
        
        # Если отрезок вырожден в точку
        if line_len_sq == 0:
            return math.sqrt((px - x1)**2 + (py - y1)**2)
        
        # Проекция точки на линию
        t = max(0, min(1, (point_vec[0] * line_vec[0] + point_vec[1] * line_vec[1]) / line_len_sq))
        
        # Ближайшая точка на отрезке
        nearest_x = x1 + t * line_vec[0]
        nearest_y = y1 + t * line_vec[1]
        
        # Расстояние до этой точки
        return math.sqrt((px - nearest_x)**2 + (py - nearest_y)**2)