# island.py - Улучшенная версия с разнообразными объектами
import pygame
import random
import math
from config import ISLAND_GREEN, DARK_GREEN, RED, BROWN, GOLD, SCREEN_HEIGHT

class Island:
    def __init__(self, x, y, seed):
        self.x = x
        self.y = y
        self.radius = random.randint(50, 120)
        self.seed = seed
        random.seed(seed)
        
        # Генерируем разные оттенки зеленого для острова
        self.color = (
            max(20, min(80, ISLAND_GREEN[0] + random.randint(-15, 15))),
            max(80, min(160, ISLAND_GREEN[1] + random.randint(-20, 20))),
            max(10, min(60, ISLAND_GREEN[2] + random.randint(-10, 10)))
        )
        
        self.points = self.generate_shape()
        self.structures = self.generate_structures()
        self.decorations = self.generate_decorations()
        
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
    
    def generate_structures(self):
        """Генерация основных структур на острове"""
        structures = []
        num_structures = random.randint(0, 2)  # 0-2 основные структуры
        
        for _ in range(num_structures):
            # Случайная позиция на острове
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0.3, 0.7) * self.radius
            x = self.x + math.cos(angle) * distance
            y = self.y + math.sin(angle) * distance
            
            # Выбираем тип структуры
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
    
    def generate_decorations(self):
        """Генерация мелких декоративных элементов"""
        decorations = []
        num_decorations = random.randint(3, 8)  # 3-8 мелких объектов
        
        for _ in range(num_decorations):
            # Случайная позиция на острове
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0.2, 0.8) * self.radius
            x = self.x + math.cos(angle) * distance
            y = self.y + math.sin(angle) * distance
            
            # Выбираем тип декорации
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
        adjusted_points = [(int(p[0]), int(p[1] - camera_y)) for p in self.points]
        
        # Проверка видимости
        min_y = min(p[1] for p in adjusted_points)
        max_y = max(p[1] for p in adjusted_points)
        
        # Если остров полностью вне видимой области, не рисуем его
        if max_y < -200 or min_y > SCREEN_HEIGHT + 200:
            return
            
        # Рисуем остров с уникальным цветом
        pygame.draw.polygon(screen, self.color, adjusted_points)
        pygame.draw.polygon(screen, DARK_GREEN, adjusted_points, 3)
        
        # Рисуем основные структуры
        for structure in self.structures:
            self.draw_structure(screen, camera_y, structure)
        
        # Рисуем мелкие декорации
        for decor in self.decorations:
            self.draw_decoration(screen, camera_y, decor)
    
    def draw_structure(self, screen, camera_y, structure):
        """Отрисовка основной структуры"""
        x_screen = int(structure['x'])
        y_screen = int(structure['y'] - camera_y)
        size = structure['size']
        
        # Проверяем видимость
        if y_screen < -100 or y_screen > SCREEN_HEIGHT + 100:
            return
        
        if structure['type'] == 'lighthouse':
            # Маяк
            pygame.draw.rect(screen, (139, 69, 19), 
                           (x_screen - 8*size, y_screen - 35*size, 16*size, 35*size))
            pygame.draw.polygon(screen, RED, [
                (x_screen, y_screen - 45*size),
                (x_screen - 12*size, y_screen - 35*size),
                (x_screen + 12*size, y_screen - 35*size)
            ])
            # Огонь маяка
            if random.random() < 0.5:  # Мигающий огонь
                pygame.draw.circle(screen, GOLD, (x_screen, int(y_screen - 45*size)), int(5*size))
        
        elif structure['type'] == 'hut':
            # Хижина
            pygame.draw.polygon(screen, BROWN, [
                (x_screen - 15*size, y_screen),
                (x_screen + 15*size, y_screen),
                (x_screen + 15*size, y_screen - 25*size),
                (x_screen, y_screen - 35*size),
                (x_screen - 15*size, y_screen - 25*size)
            ])
            # Дверь
            pygame.draw.rect(screen, (100, 50, 0), 
                           (x_screen - 5*size, y_screen - 10*size, 10*size, 10*size))
        
        elif structure['type'] == 'palm':
            # Пальма с небольшим колебанием
            sway = math.sin(pygame.time.get_ticks() / 300 + structure['angle']) * 3 * size
            
            # Ствол
            pygame.draw.rect(screen, (101, 67, 33), 
                           (x_screen - 3*size, y_screen, 6*size, -30*size))
            
            # Листья
            pygame.draw.circle(screen, (0, 100, 0), (int(x_screen + sway), int(y_screen - 30*size)), int(15*size))
            pygame.draw.circle(screen, (0, 120, 0), (int(x_screen + 10*size + sway/2), int(y_screen - 25*size)), int(10*size))
            pygame.draw.circle(screen, (0, 120, 0), (int(x_screen - 10*size + sway/2), int(y_screen - 25*size)), int(10*size))
        
        elif structure['type'] == 'rock':
            # Скала
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
        
        elif structure['type'] == 'shipwreck':
            # Корабль-призрак
            # Корпус
            pygame.draw.ellipse(screen, (70, 50, 30), 
                              (x_screen - 20*size, y_screen - 5*size, 40*size, 15*size))
            # Мачта
            pygame.draw.rect(screen, (80, 60, 40), 
                           (x_screen - 2*size, y_screen - 25*size, 4*size, 20*size))
            # Парус (рваный)
            pygame.draw.polygon(screen, (200, 200, 200, 100), [
                (x_screen, y_screen - 25*size),
                (x_screen + 15*size, y_screen - 15*size),
                (x_screen, y_screen - 5*size)
            ], 1)
        
        elif structure['type'] == 'chest':
            # Сундук с сокровищами
            # Корпус
            pygame.draw.rect(screen, GOLD, 
                           (x_screen - 10*size, y_screen - 5*size, 20*size, 10*size))
            # Крышка
            pygame.draw.polygon(screen, (150, 100, 50), [
                (x_screen - 12*size, y_screen - 5*size),
                (x_screen + 12*size, y_screen - 5*size),
                (x_screen + 10*size, y_screen - 15*size),
                (x_screen - 10*size, y_screen - 15*size)
            ])
            # Замок
            pygame.draw.circle(screen, (50, 50, 50), (x_screen, y_screen - 10*size), int(3*size))
    
    def draw_decoration(self, screen, camera_y, decor):
        """Отрисовка мелкой декорации"""
        x_screen = int(decor['x'])
        y_screen = int(decor['y'] - camera_y)
        size = decor['size']
        
        # Проверяем видимость
        if y_screen < -50 or y_screen > SCREEN_HEIGHT + 50:
            return
        
        if decor['type'] == 'bush':
            # Куст
            pygame.draw.circle(screen, (0, 100, 0), (x_screen, y_screen), int(8*size))
            pygame.draw.circle(screen, (0, 80, 0), (x_screen, y_screen), int(6*size), 1)
        
        elif decor['type'] == 'flower':
            # Цветок
            pygame.draw.circle(screen, (255, 100, 150), (x_screen, y_screen), int(5*size))
            pygame.draw.circle(screen, (255, 255, 0), (x_screen, y_screen), int(2*size))
        
        elif decor['type'] == 'stone':
            # Камень
            points = [
                (x_screen - 5*size, y_screen),
                (x_screen + 3*size, y_screen - 3*size),
                (x_screen + 5*size, y_screen + 2*size),
                (x_screen, y_screen + 5*size),
                (x_screen - 4*size, y_screen + 2*size)
            ]
            pygame.draw.polygon(screen, (120, 120, 120), points)
        
        elif decor['type'] == 'coconut':
            # Кокос
            pygame.draw.circle(screen, (101, 67, 33), (x_screen, y_screen), int(4*size))
            pygame.draw.circle(screen, (50, 30, 15), (x_screen, y_screen), int(2*size))
    
    def collides_with(self, x, y, radius=25):
        """Проверка столкновения с островом"""
        dx = x - self.x
        dy = y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        return dist < self.radius * 0.8 + radius