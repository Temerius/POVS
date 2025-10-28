# enemy_hard.py - Серьезные корабли (требуют нескольких выстрелов)
import pygame
import math
import random
from config import SCREEN_WIDTH, SCREEN_HEIGHT

class HardEnemy:
    """Серьезный корабль - убивается с трех выстрелов"""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed_y = random.uniform(1.2, 2.0)  # медленнее, чем простые
        self.speed_x = random.uniform(-0.6, 0.6)  # меньше горизонтальной скорости
        self.health = 3
        self.max_health = 3
        self.shoot_cooldown = 0
        self.shoot_delay = 240  # кадры между выстрелами (4 секунды при 60 FPS)
        self.size = 60  # Размер врага
        self.radius = self.size // 2  # радиус для коллизии
        self.points = 300  # очки за уничтожение
        self.armor_timer = 0  # таймер мигания при получении урона
        self.current_direction = 'down'
        
        # Загрузка изображений с масштабированием
        try:
            self.images = {
                'up': pygame.image.load('img/enemy_hard/enemy_hard_up.png').convert_alpha(),
                'down': pygame.image.load('img/enemy_hard/enemy_hard_down.png').convert_alpha(),
                'left': pygame.image.load('img/enemy_hard/enemy_hard_left.png').convert_alpha(),
                'right': pygame.image.load('img/enemy_hard/enemy_hard_right.png').convert_alpha()
            }
            # Масштабируем все изображения
            for key in self.images:
                self.images[key] = pygame.transform.scale(self.images[key], (self.size, self.size))
            self.image = self.images[self.current_direction]
        except pygame.error:
            # Создаем заглушку
            self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, (180, 0, 0), [
                (self.size//2, 0),
                (self.size, self.size),
                (self.size//2, self.size*0.8),
                (0, self.size)
            ])
            pygame.draw.rect(self.image, (100, 100, 100), 
                           (self.size//4, self.size//3, self.size//2, self.size//4))
    
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
        
        # Плавное изменение горизонтального движения
        if random.random() < 0.02:  # 2% шанс изменить направление за кадр
            self.speed_x += random.uniform(-0.2, 0.2)
            self.speed_x = max(min(self.speed_x, 0.8), -0.8)  # Ограничение скорости
        
        # Смена направления при достижении краев экрана
        if self.x < 200:
            self.speed_x = abs(self.speed_x) * 1.1
            self.current_direction = 'right'
        elif self.x > SCREEN_WIDTH - 200:
            self.speed_x = -abs(self.speed_x) * 1.1
            self.current_direction = 'left'
        
        # Проверка на столкновение с островами
        for island in islands:
            if self.collides_with_island(island):
                # Возвращаемся на предыдущую позицию
                self.x, self.y = prev_x, prev_y
                # Меняем направление
                self.speed_x = -self.speed_x * 1.2
                self.speed_y = self.speed_y * 0.8
                break
        
        # Проверка на столкновение с берегами
        for shore in shores:
            if shore.collides_with(self.x, self.y, self.radius):
                # Возвращаемся на предыдущую позицию
                self.x, self.y = prev_x, prev_y
                # Меняем направление
                self.speed_x = -self.speed_x * 1.2
                break
        
        # Обновление изображения в зависимости от направления
        if abs(self.speed_x) > 0.2:
            if self.speed_x < 0:
                self.current_direction = 'left'
            else:
                self.current_direction = 'right'
        else:
            self.current_direction = 'down'
        
        if hasattr(self, 'images'):
            self.image = self.images[self.current_direction]
        
        # Обновление таймера брони (мигание при получении урона)
        if self.armor_timer > 0:
            self.armor_timer -= 1
        
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
        Стреляет тремя снарядами веером
        
        Returns:
            list: список снарядов
        """
        self.shoot_cooldown = self.shoot_delay
        
        projectiles = []
        base_angle = math.atan2(player.y - self.y, player.x - self.x)
        
        # Создаем три снаряда с небольшим угловым отклонением
        for i in range(-1, 2):
            angle = base_angle + i * 0.15  # небольшое отклонение
            from projectile import Projectile
            projectiles.append(
                Projectile(self.x, self.y, angle, speed=2.8, color=(220, 50, 50), is_player_shot=False)
            )
        
        return projectiles
    
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
            
        # Эффект мигания при получении урона
        if self.armor_timer > 0 and self.armor_timer % 4 < 2:
            # Создаем поверхностность для мигания
            flash_surf = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
            flash_surf.fill((255, 200, 200, 100))
            img = self.image.copy()
            img.blit(flash_surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            rect = img.get_rect(center=(x_screen, y_screen))
            
            # Проверяем, что координаты прямоугольника в допустимом диапазоне
            if (-2147483640 < rect.x < 2147483640 and -2147483640 < rect.y < 2147483640):
                screen.blit(img, rect.topleft)
        else:
            rect = self.image.get_rect(center=(x_screen, y_screen))
            
            # Проверяем, что координаты прямоугольника в допустимом диапазоне
            if (-2147483640 < rect.x < 2147483640 and -2147483640 < rect.y < 2147483640):
                screen.blit(self.image, rect.topleft)
    
    def take_damage(self, amount):
        """Получение урона"""
        self.health -= amount
        self.armor_timer = 20  # Время мигания при получении урона
        return self.health <= 0
    
    def get_torpedo_damage(self):
        """Урон при таране - мгновенное уничтожение игрока"""
        return 1000  # Достаточно для мгновенного проигрыша