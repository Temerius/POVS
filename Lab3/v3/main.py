import pygame
import random
import math
import sys
import os
from dataclasses import dataclass
from typing import List, Tuple, Optional

# Инициализация
pygame.init()

# Константы
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# Цвета
WATER_BLUE = (20, 105, 180)
ISLAND_GREEN = (34, 139, 34)
DARK_GREEN = (25, 100, 25)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 20, 20)
GOLD = (255, 215, 0)
CYAN = (0, 255, 255)

def load_image(path, default_size=(60, 60)):
    """Загрузка изображения с fallback на цветной прямоугольник"""
    try:
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, default_size)
    except:
        # Если файл не найден, создаём цветной квадрат
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
        if -50 < screen_y < SCREEN_HEIGHT + 50:
            pygame.draw.circle(screen, BLACK, (int(self.x), screen_y), self.radius)
            pygame.draw.circle(screen, (255, 150, 0), (int(self.x), screen_y), self.radius - 2)

class Island:
    def __init__(self, x, y, seed):
        self.x = x
        self.y = y
        self.radius = random.randint(80, 180)
        self.seed = seed
        self.points = self.generate_shape()
        self.has_structure = random.random() < 0.25
        
    def generate_shape(self):
        """Генерация органичной формы острова"""
        points = []
        num_points = 20
        random.seed(self.seed)
        
        for i in range(num_points):
            angle = (i / num_points) * 2 * math.pi
            noise = random.uniform(0.5, 1.3)
            r = self.radius * noise
            x = self.x + math.cos(angle) * r
            y = self.y + math.sin(angle) * r
            points.append((x, y))
        
        return points
    
    def draw(self, screen, camera_y):
        adjusted_points = [(p[0], p[1] - camera_y) for p in self.points]
        
        # Проверка видимости
        if any(-200 < p[1] < SCREEN_HEIGHT + 200 for p in adjusted_points):
            pygame.draw.polygon(screen, ISLAND_GREEN, adjusted_points)
            pygame.draw.polygon(screen, DARK_GREEN, adjusted_points, 4)
            
            # Текстура острова (точки)
            for _ in range(15):
                px = self.x + random.randint(-int(self.radius * 0.7), int(self.radius * 0.7))
                py = self.y - camera_y + random.randint(-int(self.radius * 0.7), int(self.radius * 0.7))
                if self.point_in_polygon((px, py + camera_y)):
                    pygame.draw.circle(screen, DARK_GREEN, (int(px), int(py)), 2)
            
            if self.has_structure:
                # Маяк
                struct_x = int(self.x)
                struct_y = int(self.y - camera_y)
                if -100 < struct_y < SCREEN_HEIGHT + 100:
                    pygame.draw.rect(screen, (139, 69, 19), 
                                   (struct_x - 10, struct_y - 40, 20, 40))
                    pygame.draw.polygon(screen, RED, [
                        (struct_x, struct_y - 50),
                        (struct_x - 15, struct_y - 40),
                        (struct_x + 15, struct_y - 40)
                    ])
    
    def point_in_polygon(self, point):
        x, y = point
        n = len(self.points)
        inside = False
        p1x, p1y = self.points[0]
        for i in range(1, n + 1):
            p2x, p2y = self.points[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside
    
    def collides_with(self, x, y, radius=25):
        # Простая проверка по расстоянию до центра
        dx = x - self.x
        dy = y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        return dist < self.radius * 0.8 + radius

class Whirlpool:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 45
        self.rotation = 0
        self.used_recently = False
        
    def update(self):
        self.rotation = (self.rotation + 8) % 360
        
    def draw(self, screen, camera_y):
        y_screen = int(self.y - camera_y)
        if -150 < y_screen < SCREEN_HEIGHT + 150:
            # Рисуем спиральный водоворот
            for i in range(4):
                r = self.radius - i * 10
                angle_offset = self.rotation + i * 30
                color_val = 80 + i * 40
                
                for j in range(8):
                    angle = math.radians(j * 45 + angle_offset)
                    x1 = self.x + math.cos(angle) * r
                    y1 = y_screen + math.sin(angle) * r
                    x2 = self.x + math.cos(angle) * (r - 8)
                    y2 = y_screen + math.sin(angle) * (r - 8)
                    
                    pygame.draw.line(screen, (color_val, color_val, 255), 
                                   (x1, y1), (x2, y2), 3)
            
            pygame.draw.circle(screen, (30, 30, 150), 
                             (int(self.x), y_screen), 12)
    
    def collides_with(self, x, y):
        dx = x - self.x
        dy = y - self.y
        return math.sqrt(dx*dx + dy*dy) < self.radius

class Treasure:
    def __init__(self, x, y, treasure_type):
        self.x = x
        self.y = y
        self.type = treasure_type  # 'repair', 'power', 'speed'
        self.collected = False
        self.bob = 0
        
    def update(self):
        self.bob = (self.bob + 0.1) % (2 * math.pi)
        
    def draw(self, screen, camera_y):
        if not self.collected:
            y_screen = int(self.y - camera_y + math.sin(self.bob) * 5)
            if -50 < y_screen < SCREEN_HEIGHT + 50:
                # Сундук
                pygame.draw.rect(screen, GOLD, (self.x - 18, y_screen - 12, 36, 24))
                pygame.draw.rect(screen, (184, 134, 11), (self.x - 18, y_screen - 12, 36, 24), 3)
                pygame.draw.rect(screen, (139, 69, 19), (self.x - 20, y_screen - 8, 40, 4))
                
                # Иконка типа
                if self.type == 'repair':
                    pygame.draw.line(screen, RED, (self.x - 8, y_screen), (self.x + 8, y_screen), 3)
                    pygame.draw.line(screen, RED, (self.x, y_screen - 8), (self.x, y_screen + 8), 3)
                elif self.type == 'power':
                    points = [(self.x, y_screen - 8), (self.x - 6, y_screen + 2), 
                             (self.x - 2, y_screen + 2), (self.x - 8, y_screen + 8),
                             (self.x, y_screen + 4), (self.x + 8, y_screen + 8),
                             (self.x + 2, y_screen + 2), (self.x + 6, y_screen + 2)]
                    pygame.draw.polygon(screen, (255, 255, 0), points)
                elif self.type == 'speed':
                    pygame.draw.polygon(screen, CYAN, [
                        (self.x + 6, y_screen), (self.x - 6, y_screen - 6),
                        (self.x - 6, y_screen + 6)
                    ])

class Enemy:
    def __init__(self, x, y, enemy_type, target_x):
        self.x = x
        self.y = y
        self.type = enemy_type  # 'simple' or 'hard'
        self.target_x = target_x
        self.health = 1 if enemy_type == 'simple' else 3
        self.max_health = self.health
        self.speed = 3.5 if enemy_type == 'simple' else 2.0
        self.size = 40 if enemy_type == 'simple' else 60
        self.shoot_cooldown = 0
        self.angle = 0
        
        # Загрузка изображений
        direction = 'down'
        if enemy_type == 'simple':
            self.image = load_image(f'img/enemy_simple/enemy_simple_{direction}.png', (self.size, self.size))
        else:
            self.image = load_image(f'img/enemy_hard/enemy_hard_{direction}.png', (self.size, self.size))
        
    def update(self, player_x, player_y):
        # Движение к игроку
        dx = self.target_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist > 20:
            move_x = (dx / dist) * self.speed
            move_y = (dy / dist) * self.speed
            self.x += move_x
            self.y += move_y
            self.angle = math.degrees(math.atan2(dy, dx)) + 90
        
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
            
    def can_shoot(self, player_x, player_y):
        if self.type == 'hard' and self.shoot_cooldown == 0:
            dist = math.sqrt((player_x - self.x)**2 + (player_y - self.y)**2)
            if 120 < dist < 400:
                self.shoot_cooldown = 90
                return True
        return False
    
    def shoot_projectile(self, player_x, player_y):
        # Галеоны стреляют перпендикулярно направлению на игрока
        angle_to_player = math.atan2(player_y - self.y, player_x - self.x)
        
        # Стреляем вбок (перпендикулярно)
        side_angle = angle_to_player + math.pi / 2
        if random.random() < 0.5:
            side_angle = angle_to_player - math.pi / 2
            
        return Projectile(self.x, self.y, side_angle, 7)
    
    def draw(self, screen, camera_y):
        y_screen = int(self.y - camera_y)
        if -150 < y_screen < SCREEN_HEIGHT + 150:
            # Поворот изображения
            rotated = pygame.transform.rotate(self.image, -self.angle)
            rect = rotated.get_rect(center=(int(self.x), y_screen))
            screen.blit(rotated, rect)
            
            # Полоска здоровья
            bar_width = self.size
            bar_height = 6
            health_ratio = self.health / self.max_health
            
            pygame.draw.rect(screen, RED, 
                           (self.x - bar_width//2, y_screen - self.size//2 - 15, 
                            bar_width, bar_height))
            pygame.draw.rect(screen, (0, 255, 0), 
                           (self.x - bar_width//2, y_screen - self.size//2 - 15, 
                            int(bar_width * health_ratio), bar_height))
            pygame.draw.rect(screen, BLACK, 
                           (self.x - bar_width//2, y_screen - self.size//2 - 15, 
                            bar_width, bar_height), 1)

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.hull_angle = 0  # Угол поворота корпуса (-45 до 45)
        self.max_angle = 45
        self.rotation_speed = 3
        self.auto_return_speed = 1.5
        self.size = 60
        self.base_speed = 3
        self.speed = self.base_speed
        self.health = 100
        self.max_health = 100
        self.shoot_cooldown = 0
        self.combo = 0
        self.score = 0
        self.power_up_time = 0
        self.speed_up_time = 0
        
        # Загрузка изображений
        self.images = {
            'down': load_image('img/player/player_down.png', (self.size, self.size)),
            'up': load_image('img/player/player_up.png', (self.size, self.size)),
            'left': load_image('img/player/player_left.png', (self.size, self.size)),
            'right': load_image('img/player/player_right.png', (self.size, self.size))
        }
        
    def update(self, keys, islands):
        # Автоматическое движение вперёд
        actual_speed = self.base_speed
        if self.speed_up_time > 0:
            actual_speed = self.base_speed * 1.5
            self.speed_up_time -= 1
        
        self.y -= actual_speed
        
        # Управление поворотом корпуса
        if keys[pygame.K_a] and self.hull_angle > -self.max_angle:
            self.hull_angle -= self.rotation_speed
        elif keys[pygame.K_d] and self.hull_angle < self.max_angle:
            self.hull_angle += self.rotation_speed
        else:
            # Автоматический возврат к нулю
            if abs(self.hull_angle) < self.auto_return_speed:
                self.hull_angle = 0
            elif self.hull_angle > 0:
                self.hull_angle -= self.auto_return_speed
            else:
                self.hull_angle += self.auto_return_speed
        
        # Ограничение угла
        self.hull_angle = max(-self.max_angle, min(self.max_angle, self.hull_angle))
        
        # Проверка столкновений с островами
        for island in islands:
            if island.collides_with(self.x, self.y, self.size // 2):
                self.health -= 2
                self.y += 8  # Отталкивание назад
                break
        
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
            
        if self.power_up_time > 0:
            self.power_up_time -= 1
    
    def shoot(self):
        """Выстрел в сторону, ПРОТИВОПОЛОЖНУЮ повороту корпуса"""
        if self.shoot_cooldown == 0:
            self.shoot_cooldown = 20 if self.power_up_time > 0 else 35
            
            projectiles = []
            
            # Определяем направление выстрела (противоположное повороту!)
            if self.hull_angle < -5:  # Корпус повёрнут влево -> стреляем ВПРАВО
                shoot_angle = 0  # Вправо
                offset_x = self.size // 2
            elif self.hull_angle > 5:  # Корпус повёрнут вправо -> стреляем ВЛЕВО
                shoot_angle = math.pi  # Влево
                offset_x = -self.size // 2
            else:
                return []  # Не стреляем, если корпус прямо
            
            # Создаём снаряды
            if self.power_up_time > 0:
                # Усиленный залп - три снаряда
                projectiles.append(Projectile(self.x + offset_x, self.y, shoot_angle, 14))
                projectiles.append(Projectile(self.x + offset_x, self.y - 20, shoot_angle, 14))
                projectiles.append(Projectile(self.x + offset_x, self.y + 20, shoot_angle, 14))
            else:
                # Обычный выстрел
                projectiles.append(Projectile(self.x + offset_x, self.y, shoot_angle, 12))
            
            return projectiles
        return []
    
    def draw(self, screen, camera_y):
        y_screen = int(self.y - camera_y)
        
        # Выбор изображения в зависимости от угла поворота
        if abs(self.hull_angle) < 10:
            img = self.images['down']
        elif self.hull_angle > 0:
            img = self.images['right']
        else:
            img = self.images['left']
        
        # Поворот изображения
        rotated = pygame.transform.rotate(img, -self.hull_angle)
        rect = rotated.get_rect(center=(int(self.x), y_screen))
        
        # Эффект усиления
        if self.power_up_time > 0 and self.power_up_time % 10 < 5:
            # Свечение
            glow_surf = pygame.Surface((self.size + 20, self.size + 20), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 50, 50, 100), 
                             (self.size // 2 + 10, self.size // 2 + 10), self.size // 2 + 10)
            screen.blit(glow_surf, (int(self.x) - self.size // 2 - 10, y_screen - self.size // 2 - 10))
        
        screen.blit(rotated, rect)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Бескрайнее море — боевой корабль")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.big_font = pygame.font.Font(None, 48)
        
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150)
        self.camera_y = self.player.y - SCREEN_HEIGHT + 200
        
        self.islands = []
        self.whirlpools = []
        self.enemies = []
        self.projectiles = []
        self.enemy_projectiles = []
        self.treasures = []
        
        self.world_top = 0  # Самая верхняя сгенерированная точка
        self.difficulty = 1.0
        self.last_combo_time = pygame.time.get_ticks()
        self.wave_offset = 0
        
        # Начальная генерация мира
        self.generate_world_segment()
        
    def generate_world_segment(self):
        """Генерация нового сегмента мира"""
        segment_start = self.world_top - 1500
        segment_end = self.world_top
        
        current_y = segment_start
        
        while current_y < segment_end:
            # Острова - чаще
            if random.random() < 0.4:
                x = random.randint(150, SCREEN_WIDTH - 150)
                # Проверка, чтобы острова не были слишком близко
                too_close = False
                for island in self.islands:
                    if abs(island.y - current_y) < 150 and abs(island.x - x) < 200:
                        too_close = True
                        break
                
                if not too_close:
                    island = Island(x, current_y, random.randint(0, 100000))
                    self.islands.append(island)
            
            # Водовороты
            if random.random() < 0.08:
                x = random.randint(150, SCREEN_WIDTH - 150)
                self.whirlpools.append(Whirlpool(x, current_y))
            
            # Сокровища
            if random.random() < 0.12:
                x = random.randint(100, SCREEN_WIDTH - 100)
                t_type = random.choice(['repair', 'power', 'speed'])
                self.treasures.append(Treasure(x, current_y, t_type))
            
            # Враги - чаще и разнообразнее
            enemy_chance = 0.25 * self.difficulty
            if random.random() < enemy_chance:
                enemy_type = 'simple' if random.random() < 0.65 else 'hard'
                side = random.choice(['left', 'right'])
                
                if side == 'left':
                    x = random.randint(30, 100)
                    target_x = random.randint(SCREEN_WIDTH - 200, SCREEN_WIDTH - 100)
                else:
                    x = random.randint(SCREEN_WIDTH - 100, SCREEN_WIDTH - 30)
                    target_x = random.randint(100, 200)
                
                self.enemies.append(Enemy(x, current_y, enemy_type, target_x))
            
            current_y += random.randint(100, 250)
        
        self.world_top = segment_start
        
    def update(self):
        keys = pygame.key.get_pressed()
        
        # Обновление камеры
        self.camera_y = self.player.y - SCREEN_HEIGHT + 200
        
        # Генерация нового мира при продвижении
        if self.player.y < self.world_top + 1000:
            self.generate_world_segment()
            self.difficulty = min(3.0, self.difficulty + 0.05)
        
        # Обновление игрока
        self.player.update(keys, self.islands)
        
        # Стрельба по SPACE
        if keys[pygame.K_SPACE]:
            new_projectiles = self.player.shoot()
            if new_projectiles:
                self.projectiles.extend(new_projectiles)
        
        # Обновление волн
        self.wave_offset = (self.wave_offset + 2) % 80
        
        # Обновление снарядов игрока
        for proj in self.projectiles[:]:
            proj.update()
            if proj.lifetime <= 0 or proj.x < 0 or proj.x > SCREEN_WIDTH:
                self.projectiles.remove(proj)
        
        # Обновление сокровищ
        for treasure in self.treasures:
            treasure.update()
            if not treasure.collected:
                dx = self.player.x - treasure.x
                dy = self.player.y - treasure.y
                if math.sqrt(dx*dx + dy*dy) < 40:
                    treasure.collected = True
                    if treasure.type == 'repair':
                        self.player.health = min(self.player.max_health, 
                                               self.player.health + 35)
                    elif treasure.type == 'power':
                        self.player.power_up_time = 360
                    elif treasure.type == 'speed':
                        self.player.speed_up_time = 300
        
        # Обновление врагов
        for enemy in self.enemies[:]:
            enemy.update(self.player.x, self.player.y)
            
            # Враги стреляют
            if enemy.can_shoot(self.player.x, self.player.y):
                proj = enemy.shoot_projectile(self.player.x, self.player.y)
                self.enemy_projectiles.append(proj)
            
            # Проверка попаданий снарядов игрока
            for proj in self.projectiles[:]:
                dx = proj.x - enemy.x
                dy = proj.y - enemy.y
                if math.sqrt(dx*dx + dy*dy) < enemy.size // 2:
                    enemy.health -= 1
                    if proj in self.projectiles:
                        self.projectiles.remove(proj)
                    
                    if enemy.health <= 0:
                        points = 15 if enemy.type == 'simple' else 30
                        self.player.score += points
                        self.player.combo += 1
                        self.last_combo_time = pygame.time.get_ticks()
                        if enemy in self.enemies:
                            self.enemies.remove(enemy)
                    break
            
            # Таран
            if enemy in self.enemies:
                dx = self.player.x - enemy.x
                dy = self.player.y - enemy.y
                if math.sqrt(dx*dx + dy*dy) < (enemy.size + self.player.size) // 2:
                    damage = 8 if enemy.type == 'simple' else 15
                    self.player.health -= damage
                    self.enemies.remove(enemy)
        
        # Снаряды врагов
        for proj in self.enemy_projectiles[:]:
            proj.update()
            if proj.lifetime <= 0:
                self.enemy_projectiles.remove(proj)
                continue
            
            dx = proj.x - self.player.x
            dy = proj.y - self.player.y
            if math.sqrt(dx*dx + dy*dy) < self.player.size // 2:
                self.player.health -= 12
                if proj in self.enemy_projectiles:
                    self.enemy_projectiles.remove(proj)
        
        # Водовороты
        for whirlpool in self.whirlpools:
            whirlpool.update()
            if not whirlpool.used_recently and whirlpool.collides_with(self.player.x, self.player.y):
                # Телепорт
                other_pools = [w for w in self.whirlpools 
                              if w != whirlpool and not w.used_recently]
                if other_pools:
                    target = random.choice(other_pools)
                    self.player.x = target.x
                    self.player.y = target.y - 150
                    whirlpool.used_recently = True
                    target.used_recently = True
                    
                    # Сброс флага через некоторое время
                    pygame.time.set_timer(pygame.USEREVENT + 1, 2000, True)
        
        # Сброс комбо
        if pygame.time.get_ticks() - self.last_combo_time > 4000:
            self.player.combo = 0
        
        # Очистка старых объектов
        cleanup_threshold = self.camera_y - 500
        self.islands = [i for i in self.islands if i.y > cleanup_threshold]
        self.treasures = [t for t in self.treasures if t.y > cleanup_threshold]
        self.enemies = [e for e in self.enemies if e.y > cleanup_threshold - 200]
        self.whirlpools = [w for w in self.whirlpools if w.y > cleanup_threshold]
    
    def draw(self):
        # Фон (море)
        self.screen.fill(WATER_BLUE)
        
        # Волны
        for i in range(-1, SCREEN_HEIGHT // 40 + 2):
            y = i * 40 + (int(self.camera_y / 3) % 40) + self.wave_offset % 40
            color = (10, 95, 170) if (i + self.wave_offset // 40) % 2 == 0 else (15, 100, 175)
            pygame.draw.line(self.screen, color, (0, y), (SCREEN_WIDTH, y), 2)
        
        # Острова
        for island in self.islands:
            island.draw(self.screen, self.camera_y)
        
        # Водовороты
        for whirlpool in self.whirlpools:
            whirlpool.draw(self.screen, self.camera_y)
        
        # Сокровища
        for treasure in self.treasures:
            treasure.draw(self.screen, self.camera_y)
        
        # Враги
        for enemy in self.enemies:
            enemy.draw(self.screen, self.camera_y)
        
        # Снаряды
        for proj in self.projectiles + self.enemy_projectiles:
            proj.draw(self.screen, self.camera_y)
        
        # Игрок
        self.player.draw(self.screen, self.camera_y)
        
        # UI
        self.draw_ui()
        
        pygame.display.flip()
    
    def draw_ui(self):
        # Здоровье
        health_text = self.font.render(f"HP: {max(0, self.player.health)}/{self.player.max_health}", True, WHITE)
        self.screen.blit(health_text, (20, 20))
        
        bar_width = 250
        bar_height = 30
        health_ratio = max(0, self.player.health) / self.player.max_health
        
        pygame.draw.rect(self.screen, (100, 0, 0), (20, 60, bar_width, bar_height))
        pygame.draw.rect(self.screen, RED, (20, 60, bar_width, bar_height))
        pygame.draw.rect(self.screen, (0, 200, 0), 
                        (20, 60, int(bar_width * health_ratio), bar_height))
        pygame.draw.rect(self.screen, WHITE, (20, 60, bar_width, bar_height), 3)
        
        # Счёт
        score_text = self.font.render(f"Счёт: {self.player.score}", True, GOLD)
        self.screen.blit(score_text, (SCREEN_WIDTH - 250, 20))
        
        # Угол поворота корпуса
        angle_text = self.font.render(f"Угол: {int(self.player.hull_angle)}°", True, CYAN)
        self.screen.blit(angle_text, (SCREEN_WIDTH // 2 - 80, 20))
        
        # Индикатор направления выстрела
        if abs(self.player.hull_angle) > 5:
            direction = "← ВЛЕВО" if self.player.hull_angle > 5 else "ВПРАВО →"
            dir_color = RED if self.player.shoot_cooldown == 0 else (100, 100, 100)
            dir_text = self.font.render(f"Выстрел: {direction}", True, dir_color)
            self.screen.blit(dir_text, (SCREEN_WIDTH // 2 - 150, 60))
        
        # Комбо
        if self.player.combo > 1:
            combo_text = self.big_font.render(f"COMBO x{self.player.combo}!", True, GOLD)
            combo_rect = combo_text.get_rect(center=(SCREEN_WIDTH // 2, 120))
            
            # Тень
            shadow = self.big_font.render(f"COMBO x{self.player.combo}!", True, BLACK)
            shadow_rect = shadow.get_rect(center=(SCREEN_WIDTH // 2 + 2, 122))
            self.screen.blit(shadow, shadow_rect)
            self.screen.blit(combo_text, combo_rect)
        
        # Бонусы
        bonus_y = 110
        if self.player.power_up_time > 0:
            power_text = self.small_font.render(f"⚡ УСИЛЕННЫЙ ЗАЛП ({self.player.power_up_time // 60}s)", True, RED)
            
            # Мигающий эффект
            if self.player.power_up_time % 20 < 10:
                pygame.draw.rect(self.screen, (50, 0, 0, 128), (15, bonus_y - 5, 320, 30))
            
            self.screen.blit(power_text, (20, bonus_y))
            bonus_y += 35
        
        if self.player.speed_up_time > 0:
            speed_text = self.small_font.render(f"🚀 УСКОРЕНИЕ ({self.player.speed_up_time // 60}s)", True, CYAN)
            
            if self.player.speed_up_time % 20 < 10:
                pygame.draw.rect(self.screen, (0, 50, 50, 128), (15, bonus_y - 5, 280, 30))
            
            self.screen.blit(speed_text, (20, bonus_y))
        
        # Информация о перезарядке
        if self.player.shoot_cooldown > 0:
            cooldown_text = self.small_font.render(f"Перезарядка...", True, (150, 150, 150))
            self.screen.blit(cooldown_text, (SCREEN_WIDTH // 2 - 70, 100))
        
        # Управление (в правом нижнем углу)
        controls = [
            "Управление:",
            "A/D - Поворот корпуса",
            "SPACE - Выстрел",
            "ESC - Выход"
        ]
        
        # Фон для управления
        pygame.draw.rect(self.screen, (0, 0, 0, 180), 
                        (SCREEN_WIDTH - 260, SCREEN_HEIGHT - 130, 250, 120))
        pygame.draw.rect(self.screen, WHITE, 
                        (SCREEN_WIDTH - 260, SCREEN_HEIGHT - 130, 250, 120), 2)
        
        for i, text in enumerate(controls):
            color = GOLD if i == 0 else WHITE
            font = self.small_font if i > 0 else self.font
            control_text = font.render(text, True, color)
            self.screen.blit(control_text, 
                           (SCREEN_WIDTH - 250, SCREEN_HEIGHT - 120 + i * 28))
        
        # Счётчики врагов
        enemy_simple = len([e for e in self.enemies if e.type == 'simple'])
        enemy_hard = len([e for e in self.enemies if e.type == 'hard'])
        
        enemy_info = self.small_font.render(f"Враги: Шлюпки {enemy_simple} | Галеоны {enemy_hard}", 
                                           True, (255, 200, 100))
        self.screen.blit(enemy_info, (20, SCREEN_HEIGHT - 40))
    
    def run(self):
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                if event.type == pygame.USEREVENT + 1:
                    # Сброс флага водоворотов
                    for w in self.whirlpools:
                        w.used_recently = False
            
            if self.player.health <= 0:
                self.game_over()
                running = False
            
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()
    
    def game_over(self):
        # Экран окончания игры
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(220)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        game_over_font = pygame.font.Font(None, 84)
        game_over_text = game_over_font.render("ИГРА ОКОНЧЕНА", True, RED)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
        
        score_text = self.big_font.render(f"Финальный счёт: {self.player.score}", True, GOLD)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        
        distance_text = self.font.render(f"Пройдено: {int(abs(self.player.y) / 10)} морских миль", 
                                        True, WHITE)
        distance_rect = distance_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
        
        # Тени для текста
        shadow_offset = 3
        game_over_shadow = game_over_font.render("ИГРА ОКОНЧЕНА", True, (50, 0, 0))
        self.screen.blit(game_over_shadow, 
                        (game_over_rect.x + shadow_offset, game_over_rect.y + shadow_offset))
        self.screen.blit(game_over_text, game_over_rect)
        
        self.screen.blit(score_text, score_rect)
        self.screen.blit(distance_text, distance_rect)
        
        pygame.display.flip()
        pygame.time.wait(4000)

if __name__ == "__main__":
    game = Game()
    game.run()