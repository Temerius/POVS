# player.py - Исправленная обработка коллизий
import pygame
import math
from config import SCREEN_WIDTH
from utils import load_image

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
        self.health = 100
        self.max_health = 100
        self.shoot_cooldown = 0
        self.combo = 0
        self.score = 0
        self.power_up_time = 0
        self.speed_up_time = 0
        
        # ТОЛЬКО player_up.png - одна картинка, которую вращаем!
        self.image = load_image('img/player/player_up.png', (self.size, self.size))
        
    def update(self, keys, obstacles):
        # Скорость
        actual_speed = self.base_speed
        if self.speed_up_time > 0:
            actual_speed = self.base_speed * 1.5
            self.speed_up_time -= 1
        
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
        
        # ДВИЖЕНИЕ: вперёд + БОКОВОЕ СМЕЩЕНИЕ от угла поворота!
        self.y -= actual_speed  # Вперёд всегда (игрок движется вверх)
        
        # ВОТ ОНО! Боковое движение в зависимости от угла
        side_speed = (self.hull_angle / self.max_angle) * 3.0
        self.x += side_speed
        
        # Ограничение краёв с небольшим отступом
        self.x = max(80, min(SCREEN_WIDTH - 80, self.x))
        
        # Столкновения с препятствиями
        for obstacle in obstacles:
            if obstacle.collides_with(self.x, self.y, self.size // 2):
                self.health -= 2
                self.y += 15  # Откат назад (вниз)
                
                # Корректируем позицию, чтобы выйти из коллизии
                if hasattr(obstacle, 'side'):
                    if obstacle.side == 'left':
                        self.x += 5
                    else:
                        self.x -= 5
                break
        
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
            
        if self.power_up_time > 0:
            self.power_up_time -= 1
    
    def shoot(self):
        """Выстрел ВВЕРХ-ВБОК в ПРОТИВОПОЛОЖНУЮ сторону от поворота"""
        if self.shoot_cooldown == 0:
            self.shoot_cooldown = 20 if self.power_up_time > 0 else 35
            
            from projectile import Projectile
            projectiles = []
            
            # Корпус влево -> стреляем ВПРАВО-ВВЕРХ
            # Корпус вправо -> стреляем ВЛЕВО-ВВЕРХ
            if self.hull_angle < -5:
                # Стреляем вправо-вверх (угол примерно -30 градусов)
                shoot_angle = -math.pi / 6  # -30 градусов
                offset_x = self.size // 2
                offset_y = -10
            elif self.hull_angle > 5:
                # Стреляем влево-вверх (угол примерно -150 градусов)
                shoot_angle = -5 * math.pi / 6  # -150 градусов
                offset_x = -self.size // 2
                offset_y = -10
            else:
                return []
            
            if self.power_up_time > 0:
                # Тройной залп
                projectiles.append(Projectile(self.x + offset_x, self.y + offset_y, shoot_angle, 14))
                projectiles.append(Projectile(self.x + offset_x - 15, self.y + offset_y, shoot_angle, 14))
                projectiles.append(Projectile(self.x + offset_x + 15, self.y + offset_y, shoot_angle, 14))
            else:
                projectiles.append(Projectile(self.x + offset_x, self.y + offset_y, shoot_angle, 12))
            
            return projectiles
        return []
    
    def draw(self, screen, camera_y):
        y_screen = int(self.y - camera_y)
        
        # ПРОСТО ПОВОРАЧИВАЕМ player_up.png на нужный угол!
        rotated = pygame.transform.rotate(self.image, -self.hull_angle)
        rect = rotated.get_rect(center=(int(self.x), y_screen))
        
        # Эффект усиления
        if self.power_up_time > 0 and self.power_up_time % 10 < 5:
            glow_surf = pygame.Surface((self.size + 20, self.size + 20), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 50, 50, 100), 
                             (self.size // 2 + 10, self.size // 2 + 10), self.size // 2 + 10)
            screen.blit(glow_surf, (int(self.x) - self.size // 2 - 10, y_screen - self.size // 2 - 10))
        
        screen.blit(rotated, rect)