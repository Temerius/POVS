# enemy_hard.py - Серьезные корабли с улучшенным патрулированием
import pygame
import math
import random
from config import SCREEN_WIDTH, SCREEN_HEIGHT

class HardEnemy:
    """Серьезный корабль с улучшенным поведением"""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.initial_y = y
        self.base_speed = 1.6  # Медленнее простых
        self.speed_x = 0
        self.speed_y = 0
        self.target_angle = math.radians(90)
        self.health = 3
        self.max_health = 3
        self.shoot_cooldown = 0
        self.shoot_delay = 240
        self.size = 60
        self.radius = self.size // 2
        self.points = 300
        self.armor_timer = 0
        self.current_direction = 'down'
        self.active = False
        
        # AI параметры
        self.detection_range = 300  # Больше дальность обнаружения
        self.avoidance_force = 0.2
        self.wander_timer = 0
        self.wander_angle = random.uniform(-math.pi/6, math.pi/6)
        self.patrol_points = []  # Точки патрулирования
        self.pursuit_timer = 0  # Таймер преследования после потери игрока
        self.pursuit_direction = 0
        self.current_strategy = None
        self.last_patrol_point_time = 0  # Время последней генерации точек
        self.min_patrol_distance = 300  # Минимальное расстояние между точками
        
        # Загрузка изображений
        try:
            self.images = {
                'up': pygame.image.load('img/enemy_hard/enemy_hard_up.png').convert_alpha(),
                'down': pygame.image.load('img/enemy_hard/enemy_hard_down.png').convert_alpha(),
                'left': pygame.image.load('img/enemy_hard/enemy_hard_left.png').convert_alpha(),
                'right': pygame.image.load('img/enemy_hard/enemy_hard_right.png').convert_alpha()
            }
            for key in self.images:
                self.images[key] = pygame.transform.scale(self.images[key], (self.size, self.size))
            self.image = self.images[self.current_direction]
        except pygame.error:
            self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, (180, 0, 0), [
                (self.size//2, 0), (self.size, self.size),
                (self.size//2, self.size*0.8), (0, self.size)
            ])
            pygame.draw.rect(self.image, (100, 100, 100),
                           (self.size//4, self.size//3, self.size//2, self.size//4))
    
    def detect_obstacles_ahead(self, islands, shores):
        """Продвинутое обнаружение препятствий"""
        avoid_vector = [0, 0]
        
        # Проверяем 5 лучей для лучшего избегания
        for angle_offset in [-45, -22, 0, 22, 45]:
            check_angle = self.target_angle + math.radians(angle_offset)
            check_dist = self.detection_range
            
            check_x = self.x + math.cos(check_angle) * check_dist
            check_y = self.y + math.sin(check_angle) * check_dist
            
            # Проверка островов
            for island in islands:
                if island.collides_with(check_x, check_y, 30):
                    dx = self.x - island.x
                    dy = self.y - island.y
                    dist = math.sqrt(dx*dx + dy*dy)
                    if dist > 0:
                        strength = 1.2 / max(dist / 100, 0.3)
                        avoid_vector[0] += (dx / dist) * strength
                        avoid_vector[1] += (dy / dist) * strength
            
            # Проверка берегов
            for shore in shores:
                if shore.collides_with(check_x, check_y, 30):
                    if shore.side == 'left':
                        avoid_vector[0] += 2.0
                    else:
                        avoid_vector[0] -= 2.0
        
        return avoid_vector
    
    def update(self, islands, shores, player, world_top):
        """Обновление с улучшенным поведением"""
        # Активация и фиксация стратегии
        if not self.active and self.y > player.y - SCREEN_HEIGHT * 2:
            self.active = True
            # Фиксируем стратегию при активации
            if random.random() < 0.7:  # 70% шанс агрессивной тактики
                self.current_strategy = 'aggressive'
                self.pursuit_timer = 0
            else:  # 30% шанс патрульной тактики
                self.current_strategy = 'patrol'
                self._generate_patrol_points(player)
        
        if not self.active:
            return []
        
        # Удаление если слишком далеко
        if self.y > player.y + 3000:
            return None
        
        # Определение видимости игрока
        can_see_player = abs(self.x - player.x) < 500 and abs(self.y - player.y) < 400
        
        # 1. ОПРЕДЕЛЕНИЕ ЦЕЛИ В ЗАВИСИМОСТИ ОТ ФИКСИРОВАННОЙ СТРАТЕГИИ
        target_angle = None
        
        if self.current_strategy == 'aggressive':
            if can_see_player:
                # Преследуем игрока с предсказанием движения
                predict_x = player.x + (player.hull_angle / 45) * 50
                predict_y = player.y - 50
                
                dx = predict_x - self.x
                dy = predict_y - self.y
                target_angle = math.atan2(dy, dx)
                
                # Сброс таймера преследования
                self.pursuit_timer = 120
                self.pursuit_direction = target_angle
            elif self.pursuit_timer > 0:
                # Продолжаем преследовать в последнем известном направлении
                self.pursuit_timer -= 1
                target_angle = self.pursuit_direction
            else:
                # Если не видим игрока и таймер истек - плавное возвращение к базовому движению
                target_angle = math.radians(90) + self.wander_angle
                self.wander_timer -= 1
                if self.wander_timer <= 0:
                    self.wander_timer = random.randint(180, 300)
                    # Небольшое изменение направления в пределах допустимого угла
                    self.wander_angle += random.uniform(-0.05, 0.05)
                    # Ограничиваем wander_angle, чтобы не было резких поворотов
                    self.wander_angle = max(-math.pi/6, min(math.pi/6, self.wander_angle))
        
        else:  # patrol стратегия
            # Проверяем, нужно ли обновить точки патрулирования
            if not self.patrol_points or len(self.patrol_points) == 0:
                self._generate_patrol_points(player)
            
            # Двигаемся к ближайшей точке патрулирования
            target_x, target_y = self.patrol_points[0]
            dx = target_x - self.x
            dy = target_y - self.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Если достигли точки, удаляем её и идём к следующей
            if distance < self.min_patrol_distance:
                self.patrol_points.pop(0)
                if not self.patrol_points:
                    self._generate_patrol_points(player)
            else:
                target_angle = math.atan2(dy, dx)
        
        # Если target_angle не был установлен (например, нет точек патрулирования)
        if target_angle is None:
            # Базовое движение вниз с небольшим отклонением
            target_angle = math.radians(90) + self.wander_angle
        
        # 2. ОБНАРУЖЕНИЕ ПРЕПЯТСТВИЙ
        avoid_vector = self.detect_obstacles_ahead(islands, shores)
        
        # # 3. КОМБИНИРОВАНИЕ НАПРАВЛЕНИЙ
        # if avoid_vector[0] != 0 or avoid_vector[1] != 0:
        #     # При обнаружении препятствий полностью переключаемся на уклонение
        #     avoid_angle = math.atan2(avoid_vector[1], avoid_vector[0])
        #     self.target_angle = avoid_angle
        # else:
        #     # Плавное изменение направления к цели
        angle_diff = target_angle - self.target_angle
        # Нормализуем разницу углов
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi
        # Очень медленное и плавное изменение направления
        self.target_angle += angle_diff * 0.03
        
        # 4. ПРИМЕНЯЕМ ДВИЖЕНИЕ
        self.speed_x = math.cos(self.target_angle) * self.base_speed
        self.speed_y = math.sin(self.target_angle) * self.base_speed
        
        # Сохраняем позицию для отката
        prev_x, prev_y = self.x, self.y
        self.x += self.speed_x
        self.y += self.speed_y
        
        # 5. ПРОВЕРКА СТОЛКНОВЕНИЙ
        collision = False
        for island in islands:
            if island.collides_with(self.x, self.y, self.radius):
                collision = True
                break
        
        if not collision:
            for shore in shores:
                if shore.collides_with(self.x, self.y, self.radius):
                    collision = True
                    break
        
        if collision:
            # Откатываем позицию
            self.x, self.y = prev_x, prev_y
            # При столкновении меняем направление более целенаправленно и на дольше
            turn_angle = math.radians(random.choice([90, -90]))
            self.target_angle += turn_angle
            # Закрепляем новое направление на некоторое время
            self.wander_angle = self.target_angle - math.radians(90)
        
        # Ограничения экрана
        if self.x < 150:
            self.x = 150
            self.target_angle = math.radians(random.randint(30, 150))
            # Корректируем wander_angle для плавного продолжения движения
            self.wander_angle = self.target_angle - math.radians(90)
        elif self.x > SCREEN_WIDTH - 150:
            self.x = SCREEN_WIDTH - 150
            self.target_angle = math.radians(random.randint(210, 330))
            # Корректируем wander_angle для плавного продолжения движения
            self.wander_angle = self.target_angle - math.radians(90)
        
        # 6. ОБНОВЛЕНИЕ АНИМАЦИИ
        if abs(self.speed_x) > abs(self.speed_y) * 0.7:
            self.current_direction = 'right' if self.speed_x > 0 else 'left'
        else:
            self.current_direction = 'down' if self.speed_y > 0 else 'up'
        
        if hasattr(self, 'images'):
            self.image = self.images[self.current_direction]
        
        # 7. ТАЙМЕРЫ
        if self.armor_timer > 0:
            self.armor_timer -= 1
        
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        
        # 8. СТРЕЛЬБА
        if self.shoot_cooldown == 0 and can_see_player:
            return self.shoot(player)
        
        return []
    
    def _generate_patrol_points(self, player):
        """Генерация точек для патрулирования с учетом расстояния"""
        self.patrol_points = []
        
        # Базовая позиция для генерации - текущая позиция врага
        start_x = self.x
        start_y = self.y
        
        # Если это первая генерация, выбираем начальную точку немного впереди
        if not self.patrol_points:
            start_y += 200
        
        # Создаем 2-3 точки патрулирования
        num_points = random.randint(2, 2)
        for i in range(num_points):
            # Генерируем точку с учетом минимального расстояния от предыдущей
            min_x = max(200, start_x - 400)
            max_x = min(SCREEN_WIDTH - 300, start_x + 400)
            
            # Увеличиваем расстояние по Y для более протяженного патрулирования
            y_offset = random.randint(400, 800)
            x_offset = random.randint(-300, 300)
            
            x = max(300, min(SCREEN_WIDTH - 300, start_x + x_offset))
            y = start_y + y_offset
            
            # Проверяем расстояние до игрока, чтобы не генерировать точки слишком близко к нему
            if math.sqrt((x - player.x)**2 + (y - player.y)**2) < 300:
                # Сдвигаем точку подальше от игрока
                dx = x - player.x
                dy = y - player.y
                dist = math.sqrt(dx*dx + dy*dy)
                if dist > 0:
                    x += (dx / dist) * 300
                    y += (dy / dist) * 300
            
            self.patrol_points.append((x, y))
            start_x, start_y = x, y
        
        # Добавляем финальную точку для продолжения патрулирования
        final_x = random.randint(300, SCREEN_WIDTH - 300)
        final_y = start_y + random.randint(400, 800)
        self.patrol_points.append((final_x, final_y))
        
        self.last_patrol_point_time = 0
    
    def shoot(self, player):
        """Стрельба веером из трех снарядов"""
        self.shoot_cooldown = self.shoot_delay
        
        projectiles = []
        base_angle = math.atan2(player.y - self.y, player.x - self.x)
        
        for i in range(-1, 2):
            angle = base_angle + i * 0.15
            from projectile import Projectile
            projectiles.append(
                Projectile(self.x, self.y, angle, speed=2.8, color=(220, 50, 50), is_player_shot=False)
            )
        
        return projectiles
    
    def draw(self, screen, camera_y):
        """Отрисовка с эффектом брони"""
        if not hasattr(self, 'image') or not self.image:
            return
        
        if abs(self.x) > 1000000 or abs(self.y) > 1000000:
            return
        
        x_screen = int(self.x)
        y_screen = int(self.y - camera_y)
        
        if y_screen < -1000 or y_screen > SCREEN_HEIGHT + 1000:
            return
        
        if not (-2147483640 < x_screen < 2147483640 and -2147483640 < y_screen < 2147483640):
            return
        
        # Эффект мигания при уроне
        if self.armor_timer > 0 and self.armor_timer % 4 < 2:
            flash_surf = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
            flash_surf.fill((255, 200, 200, 100))
            img = self.image.copy()
            img.blit(flash_surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            rect = img.get_rect(center=(x_screen, y_screen))
            
            if (-2147483640 < rect.x < 2147483640 and -2147483640 < rect.y < 2147483640):
                screen.blit(img, rect.topleft)
        else:
            rect = self.image.get_rect(center=(x_screen, y_screen))
            
            if (-2147483640 < rect.x < 2147483640 and -2147483640 < rect.y < 2147483640):
                screen.blit(self.image, rect.topleft)
    
    def take_damage(self, amount):
        """Получение урона"""
        self.health -= amount
        self.armor_timer = 20
        return self.health <= 0
    
    def get_torpedo_damage(self):
        """Урон при таране"""
        return 1000