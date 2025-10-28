# enemy_simple.py - Простые шлюпки (убиваются с одного выстрела)
import pygame
import math
import random
from config import SCREEN_WIDTH, SCREEN_HEIGHT

class SimpleEnemy:
    """Простая шлюпка - убивается с одного выстрела"""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed_y = random.uniform(1.8, 2.8)  # вертикальная скорость
        self.speed_x = random.uniform(-1.0, 1.0)  # горизонтальная скорость
        self.health = 1
        self.max_health = 1
        self.shoot_cooldown = 0
        self.shoot_delay = 150  # кадры между выстрелами (2.5 секунды при 60 FPS)
        self.size = 40  # Размер врага
        self.radius = self.size // 2  # радиус для коллизии
        self.points = 100  # очки за уничтожение
        self.current_direction = 'down'
        
        # Загрузка изображений с масштабированием
        try:
            self.images = {
                'up': pygame.image.load('img/enemy_simple/enemy_simple_up.png').convert_alpha(),
                'down': pygame.image.load('img/enemy_simple/enemy_simple_down.png').convert_alpha(),
                'left': pygame.image.load('img/enemy_simple/enemy_simple_left.png').convert_alpha(),
                'right': pygame.image.load('img/enemy_simple/enemy_simple_right.png').convert_alpha()
            }
            # Масштабируем все изображения
            for key in self.images:
                self.images[key] = pygame.transform.scale(self.images[key], (self.size, self.size))
            self.image = self.images[self.current_direction]
        except pygame.error:
            # Создаем заглушку
            self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, (255, 0, 0), [
                (self.size//2, 0),
                (self.size, self.size),
                (self.size//2, self.size*0.7),
                (0, self.size)
            ])
    
    def update(self, islands, shores, player, world_top):
        """
        Обновление состояния врага
        
        Args:
            islands: список островов
            shores: список берегов
            player: объект игрока
            world_top: верхняя граница сгенерированного мира
        
        Returns:
            list: список новых снарядов
        """
        # Сохраняем предыдущую позицию для коррекции при коллизии
        prev_x, prev_y = self.x, self.y
        
        # Обновление позиции
        self.x += self.speed_x
        self.y += self.speed_y
        
        # Проверка на выход за пределы мира
        if self.y > player.y + 3000:  # Если слишком далеко от игрока
            return None
        
        # Смена направления при достижении краев экрана
        if self.x < 150:
            self.speed_x = abs(self.speed_x) * 1.2  # Ускоряем при отскоке
            self.current_direction = 'right'
        elif self.x > SCREEN_WIDTH - 150:
            self.speed_x = -abs(self.speed_x) * 1.2
            self.current_direction = 'left'
        
        # Проверка на столкновение с островами
        for island in islands:
            if self.collides_with_island(island):
                # Возвращаемся на предыдущую позицию
                self.x, self.y = prev_x, prev_y
                # Меняем направление
                self.speed_x = -self.speed_x * 1.1
                self.speed_y = self.speed_y * 0.9
                break
        
        # Проверка на столкновение с берегами
        for shore in shores:
            if shore.collides_with(self.x, self.y, self.radius):
                # Возвращаемся на предыдущую позицию
                self.x, self.y = prev_x, prev_y
                # Меняем направление
                self.speed_x = -self.speed_x * 1.1
                break
        
        # Обновление изображения в зависимости от направления
        if abs(self.speed_x) > 0.3:
            if self.speed_x < 0:
                self.current_direction = 'left'
            else:
                self.current_direction = 'right'
        else:
            self.current_direction = 'down'
        
        if hasattr(self, 'images'):
            self.image = self.images[self.current_direction]
        
        # Обновление таймера стрельбы
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        
        # Стрельба в игрока
        if self.shoot_cooldown == 0:
            return self.shoot(player)
        return []
    
    def collides_with_island(self, island):
        """Проверка столкновения с островом"""
        dx = self.x - island.x
        dy = self.y - island.y
        distance = math.sqrt(dx*dx + dy*dy)
        return distance < self.radius + island.radius
    
    def shoot(self, player):
        """
        Стреляет в направлении игрока
        
        Returns:
            list: список снарядов
        """
        self.shoot_cooldown = self.shoot_delay
        
        # Расчет направления к игроку
        dx = player.x - self.x
        dy = player.y - self.y
        angle = math.atan2(dy, dx)
        
        from projectile import Projectile
        return [Projectile(self.x, self.y, angle, speed=3.5, color=(255, 50, 50), is_player_shot=False)]
    
    def draw(self, screen, camera_y):
        """Отрисовка врага с окончательным исправлением координат"""
        # Проверка, что изображение существует
        if not hasattr(self, 'image') or not self.image:
            return
            
        # Проверяем, что координаты врага в разумных пределах
        if abs(self.x) > 1000000 or abs(self.y) > 1000000:
            return
        
        # Вычисляем экранные координаты
        x_screen = int(self.x)
        y_screen = int(self.y - camera_y)
        
        # Проверка видимости
        if y_screen < -1000 or y_screen > SCREEN_HEIGHT + 1000:
            return
            
        # Проверяем, что экранные координаты в допустимом диапазоне для pygame
        if not (-2147483640 < x_screen < 2147483640 and -2147483640 < y_screen < 2147483640):
            return
            
        # Создаем прямоугольник для отрисовки
        rect = self.image.get_rect(center=(x_screen, y_screen))
        
        # Проверяем, что координаты прямоугольника в допустимом диапазоне
        if not (-2147483640 < rect.x < 2147483640 and -2147483640 < rect.y < 2147483640):
            return
            
        screen.blit(self.image, rect.topleft)
    
    def take_damage(self, amount):
        """Получение урона"""
        self.health -= amount
        return self.health <= 0
    
    def get_torpedo_damage(self):
        """Урон при таране"""
        return 30