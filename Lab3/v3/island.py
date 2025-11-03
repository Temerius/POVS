# island.py - Острова с процедурной генерацией

import pygame
import random
import math
from config import *

class Island:
    def __init__(self, x, y, seed):
        self.x = x
        self.y = y
        self.radius = random.randint(ISLAND_MIN_RADIUS, ISLAND_MAX_RADIUS)
        self.seed = seed
        random.seed(seed)
        
        # Генерация уникального оттенка зеленого
        self.color = (
            max(20, min(80, ISLAND_GREEN[0] + random.randint(-15, 15))),
            max(80, min(160, ISLAND_GREEN[1] + random.randint(-20, 20))),
            max(10, min(60, ISLAND_GREEN[2] + random.randint(-10, 10)))
        )
        
        self.points = self._generate_shape()
        self.structures = self._generate_structures()
        self.decorations = self._generate_decorations()
    
    def _generate_shape(self):
        """Генерация органичной формы острова"""
        points = []
        for i in range(ISLAND_SHAPE_POINTS):
            angle = (i / ISLAND_SHAPE_POINTS) * 2 * math.pi
            noise = random.uniform(ISLAND_SHAPE_NOISE_MIN, ISLAND_SHAPE_NOISE_MAX)
            r = self.radius * noise
            x = self.x + math.cos(angle) * r
            y = self.y + math.sin(angle) * r
            points.append((x, y))
        return points
    
    def _generate_structures(self):
        """Генерация основных структур"""
        structures = []
        num_structures = random.randint(ISLAND_STRUCTURES_MIN, ISLAND_STRUCTURES_MAX)
        
        for _ in range(num_structures):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0.3, 0.7) * self.radius
            x = self.x + math.cos(angle) * distance
            y = self.y + math.sin(angle) * distance
            
            structure_type = random.choices(
                ['lighthouse', 'hut', 'palm', 'rock', 'shipwreck', 'chest'],
                weights=[0.1, 0.2, 0.3, 0.2, 0.1, 0.1]
            )[0]
            
            structures.append({
                'type': structure_type,
                'x': x,
                'y': y,
                'size': random.uniform(0.8, 1.2),
                'angle': random.uniform(0, 360)
            })
        
        return structures
    
    def _generate_decorations(self):
        """Генерация мелких декоративных элементов"""
        decorations = []
        num_decorations = random.randint(ISLAND_DECORATIONS_MIN, ISLAND_DECORATIONS_MAX)
        
        for _ in range(num_decorations):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0.2, 0.8) * self.radius
            x = self.x + math.cos(angle) * distance
            y = self.y + math.sin(angle) * distance
            
            decor_type = random.choices(
                ['bush', 'flower', 'stone', 'coconut'],
                weights=[0.3, 0.3, 0.2, 0.2]
            )[0]
            
            decorations.append({
                'type': decor_type,
                'x': x,
                'y': y,
                'size': random.uniform(0.5, 1.0)
            })
        
        return decorations
    
    def draw(self, screen, camera_y):
        """Отрисовка острова"""
        adjusted_points = [(int(p[0]), int(p[1] - camera_y)) for p in self.points]
        
        min_y = min(p[1] for p in adjusted_points)
        max_y = max(p[1] for p in adjusted_points)
        
        if max_y < -200 or min_y > SCREEN_HEIGHT + 200:
            return
        
        pygame.draw.polygon(screen, self.color, adjusted_points)
        pygame.draw.polygon(screen, DARK_GREEN, adjusted_points, 3)
        
        for structure in self.structures:
            self._draw_structure(screen, camera_y, structure)
        
        for decor in self.decorations:
            self._draw_decoration(screen, camera_y, decor)
    
    def _draw_structure(self, screen, camera_y, structure):
        """Отрисовка структур на острове"""
        x_screen = int(structure['x'])
        y_screen = int(structure['y'] - camera_y)
        size = structure['size']
        
        if y_screen < -100 or y_screen > SCREEN_HEIGHT + 100:
            return
        
        struct_type = structure['type']
        
        if struct_type == 'lighthouse':
            pygame.draw.rect(screen, BROWN, 
                           (x_screen - 8*size, y_screen - 35*size, 16*size, 35*size))
            pygame.draw.polygon(screen, RED, [
                (x_screen, y_screen - 45*size),
                (x_screen - 12*size, y_screen - 35*size),
                (x_screen + 12*size, y_screen - 35*size)
            ])
            if random.random() < 0.5:
                pygame.draw.circle(screen, GOLD, (x_screen, int(y_screen - 45*size)), int(5*size))
        
        elif struct_type == 'hut':
            pygame.draw.polygon(screen, BROWN, [
                (x_screen - 15*size, y_screen),
                (x_screen + 15*size, y_screen),
                (x_screen + 15*size, y_screen - 25*size),
                (x_screen, y_screen - 35*size),
                (x_screen - 15*size, y_screen - 25*size)
            ])
            pygame.draw.rect(screen, (100, 50, 0), 
                           (x_screen - 5*size, y_screen - 10*size, 10*size, 10*size))
        
        elif struct_type == 'palm':
            sway = math.sin(pygame.time.get_ticks() / 300 + structure['angle']) * 3 * size
            pygame.draw.rect(screen, (101, 67, 33), 
                           (x_screen - 3*size, y_screen, 6*size, -30*size))
            pygame.draw.circle(screen, (0, 100, 0), (int(x_screen + sway), int(y_screen - 30*size)), int(15*size))
            pygame.draw.circle(screen, (0, 120, 0), (int(x_screen + 10*size + sway/2), int(y_screen - 25*size)), int(10*size))
            pygame.draw.circle(screen, (0, 120, 0), (int(x_screen - 10*size + sway/2), int(y_screen - 25*size)), int(10*size))
        
        elif struct_type == 'rock':
            points = []
            for i in range(6):
                angle = i * math.pi / 3 + structure['angle'] / 100
                r = random.uniform(8, 12) * size
                points.append((
                    x_screen + math.cos(angle) * r,
                    y_screen - 20*size + math.sin(angle) * r
                ))
            pygame.draw.polygon(screen, (100, 100, 100), points)
            pygame.draw.polygon(screen, (80, 80, 80), points, 1)
        
        elif struct_type == 'shipwreck':
            pygame.draw.ellipse(screen, (70, 50, 30), 
                              (x_screen - 20*size, y_screen - 5*size, 40*size, 15*size))
            pygame.draw.rect(screen, (80, 60, 40), 
                           (x_screen - 2*size, y_screen - 25*size, 4*size, 20*size))
            pygame.draw.polygon(screen, (200, 200, 200, 100), [
                (x_screen, y_screen - 25*size),
                (x_screen + 15*size, y_screen - 15*size),
                (x_screen, y_screen - 5*size)
            ], 1)
        
        elif struct_type == 'chest':
            pygame.draw.rect(screen, GOLD, 
                           (x_screen - 10*size, y_screen - 5*size, 20*size, 10*size))
            pygame.draw.polygon(screen, (150, 100, 50), [
                (x_screen - 12*size, y_screen - 5*size),
                (x_screen + 12*size, y_screen - 5*size),
                (x_screen + 10*size, y_screen - 15*size),
                (x_screen - 10*size, y_screen - 15*size)
            ])
            pygame.draw.circle(screen, (50, 50, 50), (x_screen, y_screen - 10*size), int(3*size))
    
    def _draw_decoration(self, screen, camera_y, decor):
        """Отрисовка декораций"""
        x_screen = int(decor['x'])
        y_screen = int(decor['y'] - camera_y)
        size = decor['size']
        
        if y_screen < -50 or y_screen > SCREEN_HEIGHT + 50:
            return
        
        decor_type = decor['type']
        
        if decor_type == 'bush':
            pygame.draw.circle(screen, (0, 100, 0), (x_screen, y_screen), int(8*size))
            pygame.draw.circle(screen, (0, 80, 0), (x_screen, y_screen), int(6*size), 1)
        
        elif decor_type == 'flower':
            pygame.draw.circle(screen, (255, 100, 150), (x_screen, y_screen), int(5*size))
            pygame.draw.circle(screen, (255, 255, 0), (x_screen, y_screen), int(2*size))
        
        elif decor_type == 'stone':
            points = [
                (x_screen - 5*size, y_screen),
                (x_screen + 3*size, y_screen - 3*size),
                (x_screen + 5*size, y_screen + 2*size),
                (x_screen, y_screen + 5*size),
                (x_screen - 4*size, y_screen + 2*size)
            ]
            pygame.draw.polygon(screen, (120, 120, 120), points)
        
        elif decor_type == 'coconut':
            pygame.draw.circle(screen, (101, 67, 33), (x_screen, y_screen), int(4*size))
            pygame.draw.circle(screen, (50, 30, 15), (x_screen, y_screen), int(2*size))
    
    def collides_with(self, x, y, radius=25):
        """Проверка столкновения с островом"""
        dx = x - self.x
        dy = y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        return dist < self.radius * ISLAND_COLLISION_MULTIPLIER + radius


# shore.py - Берега с зубчатыми краями

class Shore:
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
    
    def contains_point(self, x, y, radius=0):
        """Проверка нахождения точки внутри берега"""
        return self.collides_with(x, y, radius)
    
    def collides_with(self, x, y, radius=25):
        """Проверка столкновения с берегом"""
        for i in range(len(self.points) - 1):
            x1, y1 = self.points[i]
            x2, y2 = self.points[i+1]
            dist = self._point_to_segment_distance(x, y, x1, y1, x2, y2)
            if dist < radius + 10:
                return True
        return False
    
    def _point_to_segment_distance(self, px, py, x1, y1, x2, y2):
        """Расстояние от точки до отрезка"""
        try:
            line_vec = (x2 - x1, y2 - y1)
            point_vec = (px - x1, py - y1)
            
            line_len_sq = line_vec[0]**2 + line_vec[1]**2
            
            if line_len_sq == 0:
                dx = px - x1
                dy = py - y1
                return math.sqrt(dx*dx + dy*dy) if abs(dx) < 1e6 and abs(dy) < 1e6 else 1e9
            
            t = max(0, min(1, (point_vec[0] * line_vec[0] + point_vec[1] * line_vec[1]) / line_len_sq)) # линейная интерполяция
            
            nearest_x = x1 + t * line_vec[0]
            nearest_y = y1 + t * line_vec[1]
            
            dx = px - nearest_x
            dy = py - nearest_y
            
            if abs(dx) > 1e6 or abs(dy) > 1e6:
                return 1e9
            
            return math.sqrt(dx*dx + dy*dy)
        except (OverflowError, ValueError):
            return 1e9