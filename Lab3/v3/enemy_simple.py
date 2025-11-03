# enemy_simple.py - Простые враги с базовым AI

import pygame
import math
import random
from config import *

class SimpleEnemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.initial_y = y
        self.base_speed = ENEMY_SIMPLE_BASE_SPEED
        self.speed_x = 0
        self.speed_y = 0
        self.target_angle = math.radians(90)
        self.health = ENEMY_SIMPLE_HEALTH
        self.max_health = ENEMY_SIMPLE_HEALTH
        self.shoot_cooldown = 0
        self.shoot_delay = ENEMY_SIMPLE_SHOOT_DELAY
        self.size = ENEMY_SIMPLE_SIZE
        self.radius = COLLISION_RADIUS_ENEMY_SIMPLE
        self.points = ENEMY_SIMPLE_POINTS
        self.current_direction = 'down'
        self.active = False
        
        # AI параметры
        self.detection_range = ENEMY_SIMPLE_DETECTION_RANGE
        self.avoidance_force = ENEMY_SIMPLE_AVOIDANCE_FORCE
        self.wander_timer = 0
        self.wander_angle = random.uniform(0, 2 * math.pi)
        self.current_strategy = None
        
        self._load_images()
    
    def _load_images(self):
        """Загрузка спрайтов врага"""
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
            self.image = self._create_fallback_image()
    
    def _create_fallback_image(self):
        """Создание заглушки"""
        surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.polygon(surf, (255, 0, 0), [
            (self.size//2, 0), (self.size, self.size),
            (self.size//2, self.size*0.7), (0, self.size)
        ])
        return surf
    
    def detect_obstacles_ahead(self, islands, shores):
        """Обнаружение препятствий впереди"""
        avoid_vector = [0, 0]
        
        for angle_offset in [-30, 0, 30]:
            check_angle = self.target_angle + math.radians(angle_offset)
            check_dist = self.detection_range
            
            check_x = self.x + math.cos(check_angle) * check_dist
            check_y = self.y + math.sin(check_angle) * check_dist
            
            # Проверка островов
            for island in islands:
                if island.collides_with(check_x, check_y, 20):
                    dx = self.x - island.x
                    dy = self.y - island.y
                    dist = math.sqrt(dx*dx + dy*dy)
                    if dist > 0:
                        strength = 1.0 / max(dist / 100, 0.5)
                        avoid_vector[0] += (dx / dist) * strength
                        avoid_vector[1] += (dy / dist) * strength
            
            # Проверка берегов
            for shore in shores:
                if shore.collides_with(check_x, check_y, 20):
                    if shore.side == 'left':
                        avoid_vector[0] += 1.5
                    else:
                        avoid_vector[0] -= 1.5
        
        return avoid_vector
    
    def update(self, islands, shores, player, world_top):
        """Обновление врага"""
        # Активация при приближении
        if not self.active and self.y > player.y + ENEMY_ACTIVATION_DISTANCE * SCREEN_HEIGHT:
            self.active = True
            self.current_strategy = 'attack' if random.random() < ENEMY_SIMPLE_ATTACK_CHANCE else 'patrol'
        
        if not self.active:
            return []
        
        # Удаление если далеко позади
        if self.y > player.y + ENEMY_DELETE_DISTANCE:
            return None
        
        # Проверка видимости игрока
        can_see_player = (abs(self.x - player.x) < ENEMY_SIMPLE_CAN_SEE_RANGE_X and 
                         self.y > player.y - ENEMY_SIMPLE_CAN_SEE_RANGE_Y)
        
        # Определение целевого направления
        if self.current_strategy == 'attack':
            dx = player.x - self.x
            dy = player.y - self.y
            target_angle = math.atan2(dy, dx)
        else:
            self.wander_timer -= 1
            if self.wander_timer <= 0:
                self.wander_timer = random.randint(90, 180)
                self.wander_angle = random.uniform(-math.pi/6, math.pi/6)
            target_angle = math.radians(90) + self.wander_angle
        
        # Плавный поворот к цели
        angle_diff = target_angle - self.target_angle
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi
        self.target_angle += angle_diff * ENEMY_SIMPLE_TURN_SMOOTHNESS
        
        # Применение движения
        self.speed_x = math.cos(self.target_angle) * self.base_speed
        self.speed_y = math.sin(self.target_angle) * self.base_speed
        
        prev_x, prev_y = self.x, self.y
        self.x += self.speed_x
        self.y += self.speed_y
        
        # Проверка коллизий
        if self._check_collision(islands, shores):
            self.x, self.y = prev_x, prev_y
            self.target_angle += math.radians(random.choice([90, -90, 180]))
        
        # Ограничение по краям
        if self.x < SHORE_EDGE_MARGIN - 80:
            self.x = SHORE_EDGE_MARGIN - 80
            self.target_angle = math.radians(random.randint(30, 150))
        elif self.x > SCREEN_WIDTH - SHORE_EDGE_MARGIN + 80:
            self.x = SCREEN_WIDTH - SHORE_EDGE_MARGIN + 80
            self.target_angle = math.radians(random.randint(210, 330))
        
        # Обновление анимации
        self._update_animation()
        
        # Стрельба
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        
        if self.shoot_cooldown == 0 and can_see_player:
            return self.shoot(player)
        
        return []
    
    def _check_collision(self, islands, shores):
        """Проверка столкновений"""
        for island in islands:
            if island.collides_with(self.x, self.y, self.radius):
                return True
        for shore in shores:
            if shore.collides_with(self.x, self.y, self.radius):
                return True
        return False
    
    def _update_animation(self):
        """Обновление направления спрайта"""
        if abs(self.speed_x) > abs(self.speed_y):
            self.current_direction = 'right' if self.speed_x > 0 else 'left'
        else:
            self.current_direction = 'down' if self.speed_y > 0 else 'up'
        
        if hasattr(self, 'images'):
            self.image = self.images[self.current_direction]
    
    def shoot(self, player):
        """Стрельба в игрока"""
        self.shoot_cooldown = self.shoot_delay
        dx = player.x - self.x
        dy = player.y - self.y
        angle = math.atan2(dy, dx)
        
        from projectile import Projectile
        return [Projectile(self.x, self.y, angle, 
                          speed=ENEMY_SIMPLE_PROJECTILE_SPEED, 
                          color=PROJECTILE_COLOR_ENEMY, 
                          is_player_shot=False)]
    
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
        return ENEMY_SIMPLE_TORPEDO_DAMAGE