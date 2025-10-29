# whirlpool.py - Водовороты с гарантированной системой телепортации
import pygame
import math
import random
from config import SCREEN_HEIGHT, CYAN, SCREEN_WIDTH

class Whirlpool:
    """Водоворот - телепортирует игрока в другой водоворот"""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 45
        self.rotation = 0
        self.used_recently = False
        self.cooldown_timer = 0
        self.animation_phase = 0
        
    def update(self):
        """Обновление анимации и cooldown"""
        self.rotation = (self.rotation + 8) % 360
        self.animation_phase = (self.animation_phase + 0.1) % (2 * math.pi)
        
        # Уменьшаем cooldown
        if self.cooldown_timer > 0:
            self.cooldown_timer -= 1
            if self.cooldown_timer == 0:
                self.used_recently = False
    
    def draw(self, screen, camera_y):
        """Отрисовка водоворота с анимацией"""
        y_screen = int(self.y - camera_y)
        
        # Проверка видимости
        if y_screen < -150 or y_screen > SCREEN_HEIGHT + 150:
            return
        
        # Пульсация размера
        pulse = math.sin(self.animation_phase) * 5
        current_radius = self.radius + pulse
        
        # Рисуем спиральный водоворот (4 слоя)
        for i in range(4):
            r = current_radius - i * 10
            angle_offset = self.rotation + i * 30
            color_val = 60 + i * 40
            
            # 8 линий в каждом слое
            for j in range(8):
                angle = math.radians(j * 45 + angle_offset)
                x1 = self.x + math.cos(angle) * r
                y1 = y_screen + math.sin(angle) * r
                x2 = self.x + math.cos(angle) * (r - 8)
                y2 = y_screen + math.sin(angle) * (r - 8)
                
                color = (color_val, color_val, 255)
                pygame.draw.line(screen, color, (x1, y1), (x2, y2), 3)
        
        # Центр водоворота
        center_color = (30, 30, 150) if not self.used_recently else (100, 100, 100)
        pygame.draw.circle(screen, center_color, (int(self.x), y_screen), 12)
        
        # Индикатор cooldown
        if self.used_recently and self.cooldown_timer > 0:
            # Прогресс-бар вокруг водоворота
            progress = self.cooldown_timer / 180  # 180 = 3 секунды при 60 FPS
            arc_angle = progress * 360
            
            # Рисуем дугу cooldown
            points = [(int(self.x), y_screen)]
            for angle in range(0, int(arc_angle), 10):
                rad = math.radians(angle - 90)  # -90 чтобы начать сверху
                px = self.x + math.cos(rad) * (current_radius + 8)
                py = y_screen + math.sin(rad) * (current_radius + 8)
                points.append((int(px), int(py)))
            
            if len(points) > 2:
                pygame.draw.polygon(screen, (255, 100, 100, 100), points)
    
    def collides_with(self, x, y, radius=25):
        """Проверка столкновения с водоворотом"""
        if self.used_recently:
            return False  # Нельзя использовать водоворот в cooldown
        
        dx = x - self.x
        dy = y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        return dist < self.radius + radius
    
    @staticmethod
    def can_place_whirlpool(x, y, islands, shores, existing_whirlpools, min_distance=170):
        """
        Проверка, можно ли разместить водоворот в данной точке
        
        Args:
            x, y: координаты для размещения
            islands: список островов
            shores: список берегов
            existing_whirlpools: существующие водовороты
            min_distance: минимальное расстояние до препятствий
        
        Returns:
            bool: можно ли разместить
        """
        # Проверка расстояния до островов с большим запасом
        for island in islands:
            # Используем радиус + дополнительный запас для водоворота
            safe_distance = island.radius + 75  # Увеличенный запас
            dist = math.sqrt((island.x - x)**2 + (island.y - y)**2)
            if dist < safe_distance:
                return False
        
        # Дополнительная проверка: убедиться, что точка не внутри острова
        for island in islands:
            if island.collides_with(x, y, 0):  # Проверяем коллизию с нулевым радиусом
                return False
        
        # Проверка расстояния до берегов (увеличенный отступ от краев)
        if x < 300 or x > SCREEN_WIDTH - 300:
            return False
        
        # Проверка расстояния до других водоворотов
        for whirlpool in existing_whirlpools:
            dist = math.sqrt((whirlpool.x - x)**2 + (whirlpool.y - y)**2)
            if dist < min_distance * 2.5:
                return False
        
        return True
    
    @staticmethod
    def find_teleport_target(current_whirlpool, all_whirlpools, world_top, islands, shores, min_distance=1200):
        """
        Найти подходящий водоворот для телепортации, гарантируя его наличие
        
        Args:
            current_whirlpool: текущий водоворот
            all_whirlpools: список всех водоворотов
            world_top: верхняя граница сгенерированного мира
            islands: список островов
            shores: список берегов
            min_distance: минимальное расстояние телепортации
        
        Returns:
            Whirlpool: целевой водоворот
        """
        candidates = []
        
        for whirlpool in all_whirlpools:
            # Условия для подходящего водоворота:
            if (whirlpool != current_whirlpool and  # Не тот же самый
                not whirlpool.used_recently and  # Не в cooldown
                whirlpool.y < current_whirlpool.y - min_distance and  # Только вверх!
                whirlpool.y > world_top and  # В сгенерированной области
                whirlpool in all_whirlpools):  # Ещё существует
                
                candidates.append(whirlpool)
        
        # Если нет подходящих водоворотов, создаем новый
        if not candidates:
            # Ищем место для нового водоворота
            attempts = 0
            max_attempts = 10
            new_y = current_whirlpool.y - min_distance - random.randint(0, 500)
            
            while attempts < max_attempts:
                new_x = random.randint(300, SCREEN_WIDTH - 300)
                
                if Whirlpool.can_place_whirlpool(new_x, new_y, islands, shores, all_whirlpools):
                    new_whirlpool = Whirlpool(new_x, new_y)
                    all_whirlpools.append(new_whirlpool)
                    print(f"✨ Создан новый водоворот для телепортации в ({new_x}, {new_y})")
                    return new_whirlpool
                
                attempts += 1
                # Сдвигаем позицию для следующей попытки
                new_y -= 100
            
            # Если не удалось найти место, используем последнюю позицию
            if attempts == max_attempts:
                new_x = random.randint(300, SCREEN_WIDTH - 300)
                new_whirlpool = Whirlpool(new_x, new_y)
                all_whirlpools.append(new_whirlpool)
                print(f"⚠️ Создан водоворот без проверки в ({new_x}, {new_y})")
                return new_whirlpool
        
        # Если кандидаты есть, выбираем случайный
        return random.choice(candidates)
    
    def teleport_player(self, target_whirlpool):
        """
        Телепортировать игрока в другой водоворот
        
        Args:
            target_whirlpool: целевой водоворот
        
        Returns:
            tuple: координаты для телепортации (x, y)
        """
        if target_whirlpool is None:
            return None
        
        # Новые координаты для телепортации
        new_x = target_whirlpool.x
        new_y = target_whirlpool.y - 150  # Чуть выше водоворота (по направлению движения)
        
        # Устанавливаем cooldown для обоих водоворотов
        self.used_recently = True
        self.cooldown_timer = 180  # 3 секунды при 60 FPS
        
        target_whirlpool.used_recently = True
        target_whirlpool.cooldown_timer = 180
        
        return (new_x, new_y)


class WhirlpoolManager:
    """Менеджер для управления всеми водоворотами"""
    
    def __init__(self, max_whirlpools=6):
        self.whirlpools = []
        self.max_whirlpools = max_whirlpools
    
    def update(self, player, world_top, islands, shores):
        """
        Обновить все водовороты и проверить столкновения с игроком
        
        Args:
            player: объект игрока
            world_top: верхняя граница сгенерированного мира
            islands: список островов
            shores: список берегов
        
        Returns:
            tuple or None: координаты для телепортации (x, y) или None
        """
        # Сначала обновляем анимацию водоворотов
        for whirlpool in self.whirlpools:
            whirlpool.update()
        
        # Затем проверяем столкновения
        for whirlpool in self.whirlpools:
            if whirlpool.collides_with(player.x, player.y):
                # Ищем цель для телепортации (гарантированно находим)
                target = Whirlpool.find_teleport_target(
                    whirlpool, 
                    self.whirlpools, 
                    world_top,
                    islands,
                    shores,
                    min_distance=1200
                )
                
                # Выполняем телепортацию и получаем координаты
                teleport_pos = whirlpool.teleport_player(target)
                if teleport_pos:
                    print(f"🌀 ТЕЛЕПОРТАЦИЯ! {player.y:.0f} → {teleport_pos[1]:.0f} (прыжок: {player.y - teleport_pos[1]:.0f})")
                return teleport_pos
        
        return None
    
    def draw(self, screen, camera_y):
        """Отрисовать все водовороты"""
        for whirlpool in self.whirlpools:
            whirlpool.draw(screen, camera_y)
    
    def add_whirlpool(self, x, y, islands, shores):
        """
        Добавить новый водоворот, если возможно
        
        Returns:
            bool: был ли добавлен водоворот
        """
        # Проверка лимита
        if len(self.whirlpools) >= self.max_whirlpools:
            return False
        
        # Проверка возможности размещения
        if not Whirlpool.can_place_whirlpool(x, y, islands, shores, self.whirlpools):
            return False
        
        # Добавляем водоворот
        whirlpool = Whirlpool(x, y)
        self.whirlpools.append(whirlpool)
        print(f"➕ Водоворот добавлен в ({x}, {y}), всего: {len(self.whirlpools)}")
        return True
    
    def cleanup(self, cleanup_threshold):
        """Удалить водовороты, которые позади игрока"""
        before = len(self.whirlpools)
        self.whirlpools = [w for w in self.whirlpools if w.y < cleanup_threshold]
        
        if len(self.whirlpools) < before:
            print(f"🗑️ Удалено водоворотов: {before - len(self.whirlpools)}, осталось: {len(self.whirlpools)}")