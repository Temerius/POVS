# player.py - Игрок с управлением и стрельбой

import pygame
import math
from config import *

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.hull_angle = 0
        self.size = PLAYER_SIZE
        self.base_speed = PLAYER_BASE_SPEED
        self.health = PLAYER_MAX_HEALTH
        self.max_health = PLAYER_MAX_HEALTH
        self.shoot_cooldown = 0
        self.score = 0
        self.radius = COLLISION_RADIUS_PLAYER
        
        self._load_image()
    
    def _load_image(self):
        """Загрузка спрайта игрока"""
        try:
            self.image = pygame.image.load('img/player/player_up.png').convert_alpha()
            self.image = pygame.transform.scale(self.image, (self.size, self.size))
        except pygame.error:
            self.image = self._create_fallback_image()
    
    def _create_fallback_image(self):
        """Создание заглушки если спрайт не найден"""
        surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.polygon(surf, (0, 100, 255), [
            (self.size//2, 0),
            (self.size, self.size),
            (self.size//2, self.size*0.7),
            (0, self.size)
        ])
        return surf
    
    def update(self, keys, obstacles):
        """Обновление состояния игрока"""
        self._handle_rotation(keys)
        self._handle_movement(obstacles)
        self._update_cooldown()
    
    def _handle_rotation(self, keys):
        """Обработка поворота корпуса"""
        if keys[pygame.K_a] and self.hull_angle > -PLAYER_MAX_ANGLE:
            self.hull_angle -= PLAYER_ROTATION_SPEED
        elif keys[pygame.K_d] and self.hull_angle < PLAYER_MAX_ANGLE:
            self.hull_angle += PLAYER_ROTATION_SPEED
        else:
            # Автовозврат к прямому курсу
            if abs(self.hull_angle) < PLAYER_AUTO_RETURN_SPEED:
                self.hull_angle = 0
            elif self.hull_angle > 0:
                self.hull_angle -= PLAYER_AUTO_RETURN_SPEED
            else:
                self.hull_angle += PLAYER_AUTO_RETURN_SPEED
        
        self.hull_angle = max(-PLAYER_MAX_ANGLE, min(PLAYER_MAX_ANGLE, self.hull_angle))
    
    def _handle_movement(self, obstacles):
        """Обработка движения и коллизий"""
        old_x, old_y = self.x, self.y
        
        # Движение вперёд и боковое смещение
        self.y -= self.base_speed
        side_speed = (self.hull_angle / PLAYER_MAX_ANGLE) * PLAYER_SIDE_SPEED_MULTIPLIER
        self.x += side_speed
        
        # Ограничение краёв экрана
        self.x = max(PLAYER_EDGE_MARGIN, min(SCREEN_WIDTH - PLAYER_EDGE_MARGIN, self.x))
        
        # Проверка коллизий
        if self._check_collisions(obstacles):
            self._handle_collision(old_x, old_y)
    
    def _check_collisions(self, obstacles):
        """Проверка столкновений с препятствиями"""
        for obstacle in obstacles:
            # Острова
            if hasattr(obstacle, 'collides_with'):
                if obstacle.collides_with(self.x, self.y, self.radius):
                    return True
            # Берега
            elif hasattr(obstacle, 'contains_point'):
                if obstacle.contains_point(self.x, self.y, self.radius):
                    return True
        return False
    
    def _handle_collision(self, old_x, old_y):
        """Обработка столкновения"""
        self.health -= PLAYER_COLLISION_DAMAGE
        self.x, self.y = old_x, old_y
        self.y += PLAYER_COLLISION_PUSHBACK
    
    def _update_cooldown(self):
        """Обновление таймера перезарядки"""
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
    
    def collides_with(self, x, y, radius):
        """Проверка столкновения с точкой"""
        dx = self.x - x
        dy = self.y - y
        distance = math.sqrt(dx*dx + dy*dy)
        return distance < self.radius + radius
    
    def shoot(self):
        """Стрельба с учетом угла поворота"""
        if self.shoot_cooldown > 0:
            return []
        
        self.shoot_cooldown = PLAYER_SHOOT_COOLDOWN
        
        # Базовый угол - вверх
        angle = math.radians(-90)
        
        # Корректировка угла в зависимости от поворота
        if self.hull_angle > PLAYER_MIN_ANGLE_FOR_SIDE_SHOT:
            angle += math.radians(PLAYER_SHOOT_ANGLE_OFFSET)
        elif self.hull_angle < -PLAYER_MIN_ANGLE_FOR_SIDE_SHOT:
            angle -= math.radians(PLAYER_SHOOT_ANGLE_OFFSET)
        
        from projectile import Projectile
        return [Projectile(self.x, self.y, angle)]
    
    def take_damage(self, amount):
        """Получение урона"""
        self.health -= amount
        return self.health <= 0
    
    def draw(self, screen, camera_y):
        """Отрисовка игрока"""
        y_screen = int(self.y - camera_y)
        rotated = pygame.transform.rotate(self.image, -self.hull_angle)
        rect = rotated.get_rect(center=(int(self.x), y_screen))
        screen.blit(rotated, rect.topleft)