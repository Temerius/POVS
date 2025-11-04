# game_objects.py - Визуальные объекты игры

import pygame
import math
import random
from config import *


class Island:
    """Класс острова"""
    
    def __init__(self, x, y, seed):
        self.x = x
        self.y = y
        random.seed(seed)
        self.radius = random.randint(ISLAND_MIN_RADIUS, ISLAND_MAX_RADIUS)
        self.color = (
            max(20, min(80, ISLAND_GREEN[0] + random.randint(-15, 15))),
            max(80, min(160, ISLAND_GREEN[1] + random.randint(-20, 20))),
            max(10, min(60, ISLAND_GREEN[2] + random.randint(-10, 10)))
        )
        self.points = self._generate_shape()
    
    def _generate_shape(self):
        """Генерация неправильной формы острова"""
        points = []
        for i in range(ISLAND_SHAPE_POINTS):
            angle = (i / ISLAND_SHAPE_POINTS) * 2 * math.pi
            noise = random.uniform(0.85, 1.15)
            r = self.radius * noise
            x = self.x + math.cos(angle) * r
            y = self.y + math.sin(angle) * r
            points.append((x, y))
        return points
    
    def draw(self, screen, camera_y):
        """Отрисовка острова"""
        adjusted_points = [(int(p[0]), int(p[1] - camera_y)) for p in self.points]
        min_y = min(p[1] for p in adjusted_points)
        max_y = max(p[1] for p in adjusted_points)
        
        if max_y < -200 or min_y > SCREEN_HEIGHT + 200:
            return
        
        pygame.draw.polygon(screen, self.color, adjusted_points)
        pygame.draw.polygon(screen, DARK_GREEN, adjusted_points, 3)


class Shore:
    """Класс береговой линии"""
    
    def __init__(self, side, start_y, end_y):
        self.side = side
        self.start_y = start_y
        self.end_y = end_y
        self.points = self._generate_shore()
        
        if side == 'left':
            self.x_left = 0
            self.x_right = SHORE_WIDTH
        else:
            self.x_left = SCREEN_WIDTH - SHORE_WIDTH
            self.x_right = SCREEN_WIDTH
    
    def _generate_shore(self):
        """Генерация зубчатых краёв берега"""
        points = []
        current_y = self.start_y
        
        if self.side == 'left':
            points.append((0, current_y))
            
            while current_y < self.end_y:
                indent = random.randint(SHORE_INDENT_MIN, SHORE_INDENT_MAX)
                segment_height = random.randint(SHORE_SEGMENT_HEIGHT_MIN, SHORE_SEGMENT_HEIGHT_MAX)
                
                points.append((indent, current_y))
                current_y += segment_height / 2
                points.append((indent + random.randint(-20, 20), current_y))
                current_y += segment_height / 2
            
            points.append((0, self.end_y))
        else:
            points.append((SCREEN_WIDTH, current_y))
            
            while current_y < self.end_y:
                indent = random.randint(SHORE_INDENT_MIN, SHORE_INDENT_MAX)
                segment_height = random.randint(SHORE_SEGMENT_HEIGHT_MIN, SHORE_SEGMENT_HEIGHT_MAX)
                
                points.append((SCREEN_WIDTH - indent, current_y))
                current_y += segment_height / 2
                points.append((SCREEN_WIDTH - indent + random.randint(-20, 20), current_y))
                current_y += segment_height / 2
            
            points.append((SCREEN_WIDTH, self.end_y))
        
        return points
    
    def draw(self, screen, camera_y):
        """Отрисовка берега"""
        adjusted_points = [(int(p[0]), int(p[1] - camera_y)) for p in self.points]
        
        visible = any(-100 < p[1] < SCREEN_HEIGHT + 100 for p in adjusted_points)
        if not visible:
            return
        
        if self.side == 'left':
            polygon_points = [(0, -200)] + adjusted_points + [(0, SCREEN_HEIGHT + 200)]
        else:
            polygon_points = [(SCREEN_WIDTH, -200)] + adjusted_points + [(SCREEN_WIDTH, SCREEN_HEIGHT + 200)]
        
        pygame.draw.polygon(screen, ISLAND_GREEN, polygon_points)
        pygame.draw.lines(screen, DARK_GREEN, False, adjusted_points, 4)