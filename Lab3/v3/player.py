# player.py - Исправленная обработка коллизий с островами
import pygame
import math
from config import *

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.hull_angle = 0  # Угол поворота корпуса (-45 до 45)
        self.max_angle = 45
        self.rotation_speed = 1
        self.auto_return_speed = 1.5
        self.size = 50  # Размер корабля
        self.base_speed = 3
        self.health = 100
        self.max_health = 100
        self.shoot_cooldown = 0
        self.cooldown_time = 30  # 0.5 секунды при 60 FPS
        self.score = 0
        self.radius = self.size // 2  # радиус для коллизии
        
        # Загружаем ТОЛЬКО player_up.png и масштабируем
        try:
            self.image = pygame.image.load('img/player/player_up.png').convert_alpha()
            self.image = pygame.transform.scale(self.image, (self.size, self.size))
        except pygame.error:
            # Создаем заглушку, если изображение не найдено
            self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, (0, 100, 255), [
                (self.size//2, 0),
                (self.size, self.size),
                (self.size//2, self.size*0.7),
                (0, self.size)
            ])
    
    def update(self, keys, obstacles):
        # Управление поворотом корпуса
        if keys[pygame.K_a] and self.hull_angle > -self.max_angle:
            self.hull_angle -= self.rotation_speed
        elif keys[pygame.K_d] and self.hull_angle < self.max_angle:
            self.hull_angle += self.rotation_speed
        else:
            # Автовозврат к прямому курсу
            if abs(self.hull_angle) < self.auto_return_speed:
                self.hull_angle = 0
            elif self.hull_angle > 0:
                self.hull_angle -= self.auto_return_speed
            else:
                self.hull_angle += self.auto_return_speed
        
        self.hull_angle = max(-self.max_angle, min(self.max_angle, self.hull_angle))
        
        # Сохраняем старую позицию для отката при коллизии
        old_x, old_y = self.x, self.y
        
        # ДВИЖЕНИЕ: вперёд + БОКОВОЕ СМЕЩЕНИЕ от угла поворота!
        self.y -= self.base_speed  # Вперёд всегда (игрок движется вверх)
        
        # ВОТ ОНО! Боковое движение в зависимости от угла
        side_speed = (self.hull_angle / self.max_angle) * 3.0
        self.x += side_speed
        
        # Ограничение краёв с небольшим отступом
        self.x = max(100, min(SCREEN_WIDTH - 100, self.x))
        
        # Проверка столкновений с препятствиями
        collision_happened = False
        
        for obstacle in obstacles:
            # Проверяем столкновение с островами
            if hasattr(obstacle, 'collides_with'):
                if obstacle.collides_with(self.x, self.y, self.radius):
                    collision_happened = True
                    self.health -= 2
                    # Откатываем позицию
                    self.x, self.y = old_x, old_y
                    # Отталкиваемся назад
                    self.y += 15
                    break
            
            # Проверяем столкновение с берегами
            elif hasattr(obstacle, 'contains_point'):
                if obstacle.contains_point(self.x, self.y, self.radius):
                    collision_happened = True
                    self.health -= 2
                    # Откатываем позицию
                    self.x, self.y = old_x, old_y
                    # Отталкиваемся от берега
                    self.y += 15
                    
                    # Корректируем позицию в зависимости от стороны берега
                    if hasattr(obstacle, 'side'):
                        if obstacle.side == 'left':
                            self.x = max(self.x + 5, 120)
                        else:
                            self.x = min(self.x - 5, SCREEN_WIDTH - 120)
                    break
        
        # Обновление таймера перезарядки
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
    
    def collides_with(self, x, y, radius):
        """Проверка столкновения с объектом"""
        dx = self.x - x
        dy = self.y - y
        distance = math.sqrt(dx*dx + dy*dy)
        return distance < self.radius + radius
    
    def shoot(self):
        """Стрельба ВВЕРХ-ВБОК в ПРОТИВОПОЛОЖНУЮ сторону от поворота"""
        if self.shoot_cooldown > 0:
            return []
        
        self.shoot_cooldown = self.cooldown_time
        
        # Расчет угла стрельбы с учетом поворота корпуса
        angle = math.radians(-90)  # стандартный угол (вверх)
        
        if self.hull_angle > 5:  # Левый наклон
            angle += math.radians(20)
        elif self.hull_angle < -5:  # Правый наклон
            angle -= math.radians(20)
        
        from projectile import Projectile
        return [Projectile(self.x, self.y, angle)]
    
    def take_damage(self, amount):
        """Получение урона"""
        self.health -= amount
        return self.health <= 0
    
    def draw(self, screen, camera_y):
        y_screen = int(self.y - camera_y)
        
        # ПРОСТО ПОВОРАЧИВАЕМ player_up.png на нужный угол!
        rotated = pygame.transform.rotate(self.image, -self.hull_angle)
        rect = rotated.get_rect(center=(int(self.x), y_screen))
        
        screen.blit(rotated, rect.topleft)# player.py - Исправленная обработка коллизий с островами
import pygame
import math
from config import *

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.hull_angle = 0  # Угол поворота корпуса (-45 до 45)
        self.max_angle = 45
        self.rotation_speed = 1
        self.auto_return_speed = 1.5
        self.size = 50  # Размер корабля
        self.base_speed = 3
        self.health = 100
        self.max_health = 100
        self.shoot_cooldown = 0
        self.cooldown_time = 30  # 0.5 секунды при 60 FPS
        self.score = 0
        self.radius = self.size // 2  # радиус для коллизии
        
        # Загружаем ТОЛЬКО player_up.png и масштабируем
        try:
            self.image = pygame.image.load('img/player/player_up.png').convert_alpha()
            self.image = pygame.transform.scale(self.image, (self.size, self.size))
        except pygame.error:
            # Создаем заглушку, если изображение не найдено
            self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, (0, 100, 255), [
                (self.size//2, 0),
                (self.size, self.size),
                (self.size//2, self.size*0.7),
                (0, self.size)
            ])
    
    def update(self, keys, obstacles):
        # Управление поворотом корпуса
        if keys[pygame.K_a] and self.hull_angle > -self.max_angle:
            self.hull_angle -= self.rotation_speed
        elif keys[pygame.K_d] and self.hull_angle < self.max_angle:
            self.hull_angle += self.rotation_speed
        else:
            # Автовозврат к прямому курсу
            if abs(self.hull_angle) < self.auto_return_speed:
                self.hull_angle = 0
            elif self.hull_angle > 0:
                self.hull_angle -= self.auto_return_speed
            else:
                self.hull_angle += self.auto_return_speed
        
        self.hull_angle = max(-self.max_angle, min(self.max_angle, self.hull_angle))
        
        # Сохраняем старую позицию для отката при коллизии
        old_x, old_y = self.x, self.y
        
        # ДВИЖЕНИЕ: вперёд + БОКОВОЕ СМЕЩЕНИЕ от угла поворота!
        self.y -= self.base_speed  # Вперёд всегда (игрок движется вверх)
        
        # ВОТ ОНО! Боковое движение в зависимости от угла
        side_speed = (self.hull_angle / self.max_angle) * 3.0
        self.x += side_speed
        
        # Ограничение краёв с небольшим отступом
        self.x = max(100, min(SCREEN_WIDTH - 100, self.x))
        
        # Проверка столкновений с препятствиями
        collision_happened = False
        
        for obstacle in obstacles:
            # Проверяем столкновение с островами
            if hasattr(obstacle, 'collides_with'):
                if obstacle.collides_with(self.x, self.y, self.radius):
                    collision_happened = True
                    self.health -= 2
                    # Откатываем позицию
                    self.x, self.y = old_x, old_y
                    # Отталкиваемся назад
                    self.y += 15
                    break
            
            # Проверяем столкновение с берегами
            elif hasattr(obstacle, 'contains_point'):
                if obstacle.contains_point(self.x, self.y, self.radius):
                    collision_happened = True
                    self.health -= 2
                    # Откатываем позицию
                    self.x, self.y = old_x, old_y
                    # Отталкиваемся от берега
                    self.y += 15
                    
                    # Корректируем позицию в зависимости от стороны берега
                    if hasattr(obstacle, 'side'):
                        if obstacle.side == 'left':
                            self.x = max(self.x + 5, 120)
                        else:
                            self.x = min(self.x - 5, SCREEN_WIDTH - 120)
                    break
        
        # Обновление таймера перезарядки
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
    
    def collides_with(self, x, y, radius):
        """Проверка столкновения с объектом"""
        dx = self.x - x
        dy = self.y - y
        distance = math.sqrt(dx*dx + dy*dy)
        return distance < self.radius + radius
    
    def shoot(self):
        """Стрельба ВВЕРХ-ВБОК в ПРОТИВОПОЛОЖНУЮ сторону от поворота"""
        if self.shoot_cooldown > 0:
            return []
        
        self.shoot_cooldown = self.cooldown_time
        
        # Расчет угла стрельбы с учетом поворота корпуса
        angle = math.radians(-90)  # стандартный угол (вверх)
        
        if self.hull_angle > 5:  # Левый наклон
            angle += math.radians(20)
        elif self.hull_angle < -5:  # Правый наклон
            angle -= math.radians(20)
        
        from projectile import Projectile
        return [Projectile(self.x, self.y, angle)]
    
    def take_damage(self, amount):
        """Получение урона"""
        self.health -= amount
        return self.health <= 0
    
    def draw(self, screen, camera_y):
        y_screen = int(self.y - camera_y)
        
        # ПРОСТО ПОВОРАЧИВАЕМ player_up.png на нужный угол!
        rotated = pygame.transform.rotate(self.image, -self.hull_angle)
        rect = rotated.get_rect(center=(int(self.x), y_screen))
        
        screen.blit(rotated, rect.topleft)