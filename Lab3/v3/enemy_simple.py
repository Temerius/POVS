# enemy_simple.py - Простые шлюпки с фиксированной тактикой
import pygame
import math
import random
from config import SCREEN_WIDTH, SCREEN_HEIGHT

class SimpleEnemy:
    """Простая шлюпка с фиксированной тактикой поведения"""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.initial_y = y
        self.base_speed = 2.2  # Базовая скорость
        self.speed_x = 0
        self.speed_y = 0
        self.target_angle = math.radians(90)  # Целевой угол движения
        self.health = 1
        self.max_health = 1
        self.shoot_cooldown = 0
        self.shoot_delay = 150
        self.size = 40
        self.radius = self.size // 2
        self.points = 100
        self.current_direction = 'down'
        self.active = False
        
        # Параметры AI
        self.detection_range = 250  # Дальность обнаружения препятствий
        self.avoidance_force = 0.15  # Сила уклонения
        self.wander_timer = 0
        self.wander_angle = random.uniform(0, 2 * math.pi)
        self.current_strategy = None  # Тактика фиксируется при активации
        
        # Загрузка изображений
        try:
            self.images = {
                'up': pygame.image.load('img/enemy_simple/enemy_simple_up.png').convert_alpha(),
                'down': pygame.image.load('img/enemy_simple/enemy_simple_down.png').convert_alpha(),
                'left': pygame.image.load('img/enemy_simple/enemy_simple_left.png').convert_alpha(),
                'right': pygame.image.load('img/enemy_simple/enemy_simple_right.png').convert_alpha()
            }
            for key in self.images:
                self.images[key] = pygame.transform.scale(self.images[key], (self.size, self.size))
            self.image = self.images[self.current_direction]
        except pygame.error:
            self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, (255, 0, 0), [
                (self.size//2, 0), (self.size, self.size),
                (self.size//2, self.size*0.7), (0, self.size)
            ])
    
    def detect_obstacles_ahead(self, islands, shores):
        """Обнаружение препятствий впереди с помощью raycast"""
        avoid_vector = [0, 0]
        
        # Проверяем несколько лучей впереди
        for angle_offset in [-30, 0, 30]:
            check_angle = self.target_angle + math.radians(angle_offset)
            check_dist = self.detection_range
            
            check_x = self.x + math.cos(check_angle) * check_dist
            check_y = self.y + math.sin(check_angle) * check_dist
            
            # Проверка островов
            for island in islands:
                if island.collides_with(check_x, check_y, 20):
                    # Вектор от препятствия
                    dx = self.x - island.x
                    dy = self.y - island.y
                    dist = math.sqrt(dx*dx + dy*dy)
                    if dist > 0:
                        # Сила уклонения обратно пропорциональна расстоянию
                                # Сила уклонения обратно пропорциональна расстоянию
                        strength = 1.0 / max(dist / 100, 0.5)
                        avoid_vector[0] += (dx / dist) * strength
                        avoid_vector[1] += (dy / dist) * strength

                        # Проверка берегов
                        for shore in shores:
                            if shore.collides_with(check_x, check_y, 20):
                                # Уклоняемся от берега к центру
                                if shore.side == 'left':
                                    avoid_vector[0] += 1.5
                                else:
                                    avoid_vector[0] -= 1.5
                    
        return avoid_vector
    
    def update(self, islands, shores, player, world_top):
        """Обновление с фиксированной тактикой поведения"""
        # Активация при приближении к игроку
        if not self.active and self.y > player.y - SCREEN_HEIGHT * 2:
            self.active = True
            # Фиксируем тактику при активации
            if random.random() < 0.8:  # 80% шанс атаковать
                self.current_strategy = 'attack'
            else:
                self.current_strategy = 'patrol'
        
        if not self.active:
            return []
        
        # Удаление если слишком далеко
        if self.y > player.y + 3000:
            return None
        
        # Определение, видит ли игрок (для стрельбы)
        can_see_player = abs(self.x - player.x) < 400 and self.y > player.y - 300
        
        # 1. ЦЕЛЕВОЕ НАПРАВЛЕНИЕ В ЗАВИСИМОСТИ ОТ ФИКСИРОВАННОЙ ТАКТИКИ
        if self.current_strategy == 'attack':
            # Движение к игроку
            dx = player.x - self.x
            dy = player.y - self.y
            target_angle = math.atan2(dy, dx)
        else:  # patrol
            # Базовое движение вниз с редким и плавным блужданием
            self.wander_timer -= 1
            if self.wander_timer <= 0:
                self.wander_timer = random.randint(90, 180)  # Дольше сохраняем направление
                # Небольшое отклонение от прямого движения вниз
                self.wander_angle = random.uniform(-math.pi/6, math.pi/6)
            
            target_angle = math.radians(90) + self.wander_angle
        
        # 2. ОБНАРУЖЕНИЕ ПРЕПЯТСТВИЙ
        avoid_vector = self.detect_obstacles_ahead(islands, shores)
        
        # 3. КОМБИНИРОВАНИЕ НАПРАВЛЕНИЙ
        # if avoid_vector[0] != 0 or avoid_vector[1] != 0:
        #     # Есть препятствие - применяем уклонение
        #     avoid_angle = math.atan2(avoid_vector[1], avoid_vector[0])
        #     # Более сильное уклонение при обнаружении препятствий
        #     self.target_angle = avoid_angle
        # else:
            # Нет препятствий - плавно движемся к цели
        angle_diff = target_angle - self.target_angle
        # Нормализуем разницу углов
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi
        # Плавный поворот к целевому углу
        self.target_angle += angle_diff * 0.05  # Замедлил поворот для плавности
        
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
            # При столкновении меняем направление более радикально
            self.target_angle += math.radians(random.choice([90, -90, 180]))
        
        # Ограничиваем по краям экрана
        if self.x < 120:
            self.x = 120
            self.target_angle = math.radians(random.randint(30, 150))
        elif self.x > SCREEN_WIDTH - 120:
            self.x = SCREEN_WIDTH - 120
            self.target_angle = math.radians(random.randint(210, 330))
        
        # 6. ОБНОВЛЕНИЕ АНИМАЦИИ
        if abs(self.speed_x) > abs(self.speed_y):
            self.current_direction = 'right' if self.speed_x > 0 else 'left'
        else:
            self.current_direction = 'down' if self.speed_y > 0 else 'up'
        
        if hasattr(self, 'images'):
            self.image = self.images[self.current_direction]
        
        # 7. СТРЕЛЬБА
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        
        if self.shoot_cooldown == 0 and can_see_player:
            return self.shoot(player)
        
        return []
    
    def shoot(self, player):
        """Стрельба в игрока"""
        self.shoot_cooldown = self.shoot_delay
        dx = player.x - self.x
        dy = player.y - self.y
        angle = math.atan2(dy, dx)
        
        from projectile import Projectile
        return [Projectile(self.x, self.y, angle, speed=3.5, color=(255, 50, 50), is_player_shot=False)]
    
    def draw(self, screen, camera_y):
        """Отрисовка врага"""
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
        
        rect = self.image.get_rect(center=(x_screen, y_screen))
        
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