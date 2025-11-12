# enemy_hard.py - Сложные враги с продвинутым AI

import pygame
import math
import random
from config import *

class HardEnemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.initial_y = y
        self.base_speed = ENEMY_HARD_BASE_SPEED
        self.speed_x = 0
        self.speed_y = 0
        self.target_angle = math.radians(90)
        self.health = ENEMY_HARD_HEALTH
        self.max_health = ENEMY_HARD_HEALTH
        self.shoot_cooldown = 0
        self.shoot_delay = ENEMY_HARD_SHOOT_DELAY
        self.size = ENEMY_HARD_SIZE
        self.radius = COLLISION_RADIUS_ENEMY_HARD
        self.points = ENEMY_HARD_POINTS
        self.armor_timer = 0
        self.current_direction = 'down'
        self.active = False
        
        # AI параметры
        self.detection_range = ENEMY_HARD_DETECTION_RANGE
        self.avoidance_force = ENEMY_HARD_AVOIDANCE_FORCE
        self.wander_timer = 0
        self.wander_angle = random.uniform(-math.pi/6, math.pi/6)
        self.patrol_points = []
        self.pursuit_timer = 0
        self.pursuit_direction = 0
        self.current_strategy = None
        self.last_patrol_point_time = 0
        self.min_patrol_distance = ENEMY_HARD_MIN_PATROL_DISTANCE
        
        self._load_images()
    
    def _load_images(self):
        """Загрузка спрайтов врага"""
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
            self.image = self._create_fallback_image()
    
    def _create_fallback_image(self):
        """Создание заглушки"""
        surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.polygon(surf, (180, 0, 0), [
            (self.size//2, 0), (self.size, self.size),
            (self.size//2, self.size*0.8), (0, self.size)
        ])
        pygame.draw.rect(surf, (100, 100, 100),
                       (self.size//4, self.size//3, self.size//2, self.size//4))
        return surf
    
    def detect_obstacles_ahead(self, islands, shores):
        """Продвинутое обнаружение препятствий"""
        avoid_vector = [0, 0]
        
        for angle_offset in [-45, -22, 0, 22, 45]:
            check_angle = self.target_angle + math.radians(angle_offset)
            check_dist = self.detection_range
            
            check_x = self.x + math.cos(check_angle) * check_dist
            check_y = self.y + math.sin(check_angle) * check_dist
            
            for island in islands:
                if island.collides_with(check_x, check_y, 30):
                    dx = self.x - island.x
                    dy = self.y - island.y
                    dist = math.sqrt(dx*dx + dy*dy)
                    if dist > 0:
                        strength = 1.2 / max(dist / 100, 0.3)
                        avoid_vector[0] += (dx / dist) * strength
                        avoid_vector[1] += (dy / dist) * strength
            
            for shore in shores:
                if shore.collides_with(check_x, check_y, 30):
                    if shore.side == 'left':
                        avoid_vector[0] += 2.0
                    else:
                        avoid_vector[0] -= 2.0
        
        return avoid_vector
    
    def update(self, islands, shores, player, world_top):
        """Обновление врага"""
        # Активация и фиксация стратегии
        if not self.active and self.y > player.y + ENEMY_ACTIVATION_DISTANCE * SCREEN_HEIGHT:
            self.active = True
            if random.random() < ENEMY_HARD_AGGRESSIVE_CHANCE:
                self.current_strategy = 'aggressive'
                self.pursuit_timer = 0
            else:
                self.current_strategy = 'patrol'
                self._generate_patrol_points(player)
        
        if not self.active:
            return []
        
        if self.y > player.y + ENEMY_DELETE_DISTANCE:
            return None
        
        # Проверка видимости игрока
        can_see_player = (abs(self.x - player.x) < ENEMY_HARD_CAN_SEE_RANGE_X and 
                         abs(self.y - player.y) < ENEMY_HARD_CAN_SEE_RANGE_Y)
        
        # Определение целевого направления
        target_angle = self._calculate_target_angle(can_see_player, player)
        
        # Плавный поворот
        angle_diff = target_angle - self.target_angle
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi
        self.target_angle += angle_diff * ENEMY_HARD_TURN_SMOOTHNESS
        
        # Применение движения
        self.speed_x = math.cos(self.target_angle) * self.base_speed
        self.speed_y = math.sin(self.target_angle) * self.base_speed
        
        prev_x, prev_y = self.x, self.y
        self.x += self.speed_x
        self.y += self.speed_y
        
        # Проверка коллизий
        if self._check_collision(islands, shores):
            self.x, self.y = prev_x, prev_y
            turn_angle = math.radians(random.choice([90, -90]))
            self.target_angle += turn_angle
            self.wander_angle = self.target_angle - math.radians(90)
        
        # Ограничение по краям
        if self.x < SHORE_WIDTH:
            self.x = SHORE_WIDTH
            self.target_angle = math.radians(random.randint(30, 150))
            self.wander_angle = self.target_angle - math.radians(90)
        elif self.x > SCREEN_WIDTH - SHORE_WIDTH:
            self.x = SCREEN_WIDTH - SHORE_WIDTH
            self.target_angle = math.radians(random.randint(210, 330))
            self.wander_angle = self.target_angle - math.radians(90)
        
        # Обновление анимации и таймеров
        self._update_animation()
        self._update_timers()
        
        # Стрельба
        if self.shoot_cooldown == 0 and can_see_player:
            return self.shoot(player)
        
        return []
    
    def _calculate_target_angle(self, can_see_player, player):
        """Расчёт целевого угла движения"""
        if self.current_strategy == 'aggressive':
            if can_see_player:
                predict_x = player.x + (player.hull_angle / 45) * 50
                predict_y = player.y - 50
                dx = predict_x - self.x
                dy = predict_y - self.y
                target_angle = math.atan2(dy, dx)
                self.pursuit_timer = ENEMY_HARD_PURSUIT_TIMER
                self.pursuit_direction = target_angle
            elif self.pursuit_timer > 0:
                self.pursuit_timer -= 1
                target_angle = self.pursuit_direction
            else:
                target_angle = math.radians(90) + self.wander_angle
                self.wander_timer -= 1
                if self.wander_timer <= 0:
                    self.wander_timer = random.randint(180, 300)
                    self.wander_angle += random.uniform(-0.05, 0.05)
                    self.wander_angle = max(-math.pi/6, min(math.pi/6, self.wander_angle))
        else:  # patrol
            if not self.patrol_points:
                self._generate_patrol_points(player)
            
            target_x, target_y = self.patrol_points[0]
            dx = target_x - self.x
            dy = target_y - self.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance < self.min_patrol_distance:
                self.patrol_points.pop(0)
                if not self.patrol_points:
                    self._generate_patrol_points(player)
                target_x, target_y = self.patrol_points[0]
                dx = target_x - self.x
                dy = target_y - self.y
            
            target_angle = math.atan2(dy, dx)
        
        return target_angle
    
    def _generate_patrol_points(self, player):
        """Генерация точек патрулирования"""
        self.patrol_points = []
        start_x = self.x
        start_y = self.y + 200 if not self.patrol_points else self.y
        
        num_points = random.randint(ENEMY_HARD_PATROL_POINTS_MIN, ENEMY_HARD_PATROL_POINTS_MAX)
        for _ in range(num_points):
            y_offset = random.randint(400, 800)
            x_offset = random.randint(-300, 300)
            
            x = max(300, min(SCREEN_WIDTH - 300, start_x + x_offset))
            y = start_y + y_offset
            
            # Избегаем близости к игроку
            if math.sqrt((x - player.x)**2 + (y - player.y)**2) < 300:
                dx = x - player.x
                dy = y - player.y
                dist = math.sqrt(dx*dx + dy*dy)
                if dist > 0:
                    x += (dx / dist) * 300
                    y += (dy / dist) * 300
            
            self.patrol_points.append((x, y))
            start_x, start_y = x, y
        
        final_x = random.randint(300, SCREEN_WIDTH - 300)
        final_y = start_y + random.randint(400, 800)
        self.patrol_points.append((final_x, final_y))
    
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
        if abs(self.speed_x) > abs(self.speed_y) * 0.7:
            self.current_direction = 'right' if self.speed_x > 0 else 'left'
        else:
            self.current_direction = 'down' if self.speed_y > 0 else 'up'
        
        if hasattr(self, 'images'):
            self.image = self.images[self.current_direction]
    
    def _update_timers(self):
        """Обновление таймеров"""
        if self.armor_timer > 0:
            self.armor_timer -= 1
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
    
    def shoot(self, player):
        """Стрельба веером из трех снарядов"""
        self.shoot_cooldown = self.shoot_delay
        
        projectiles = []
        base_angle = math.atan2(player.y - self.y, player.x - self.x)
        
        for i in range(-1, 2):
            angle = base_angle + i * ENEMY_HARD_PROJECTILE_SPREAD
            from projectile import Projectile
            projectiles.append(
                Projectile(self.x, self.y, angle, 
                          speed=ENEMY_HARD_PROJECTILE_SPEED, 
                          color=PROJECTILE_COLOR_ENEMY, 
                          is_player_shot=False)
            )
        
        return projectiles
    
    def draw(self, screen, camera_y):
        """Отрисовка врага с эффектом брони"""
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
        self.armor_timer = ENEMY_HARD_ARMOR_FLASH_DURATION
        return self.health <= 0
    
    def get_torpedo_damage(self):
        """Урон при таране"""
        return ENEMY_HARD_TORPEDO_DAMAGE