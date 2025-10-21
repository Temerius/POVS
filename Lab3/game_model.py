"""
game_model.py
MODEL - Игровая логика Space Defender
Может быть перенесена на STM32
"""

import random
from enum import Enum
from dataclasses import dataclass
from typing import List

class GameState(Enum):
    MENU = 0
    PLAYING = 1
    PAUSED = 2
    GAME_OVER = 3
    LEVEL_COMPLETE = 4

@dataclass
class Vector2:
    x: float
    y: float
    
    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)
    
    def __mul__(self, scalar):
        return Vector2(self.x * scalar, self.y * scalar)

@dataclass
class Player:
    position: Vector2
    velocity: Vector2
    width: int = 60
    height: int = 40
    hp: int = 100
    max_hp: int = 100
    speed: float = 5.0
    shoot_cooldown: float = 0.0
    shield_active: bool = False
    shield_time: float = 0.0

@dataclass
class Bullet:
    position: Vector2
    velocity: Vector2
    damage: int = 10
    is_player: bool = True
    width: int = 4
    height: int = 12

@dataclass
class Enemy:
    position: Vector2
    velocity: Vector2
    hp: int = 30
    max_hp: int = 30
    enemy_type: int = 0  # 0=астероид, 1=враг
    width: int = 40
    height: int = 40
    shoot_cooldown: float = 0.0

@dataclass
class Explosion:
    position: Vector2
    frame: int = 0
    max_frames: int = 10
    radius: float = 20.0

class GameModel:
    """Игровая логика - чистая модель без отрисовки"""
    
    def __init__(self, screen_width=800, screen_height=600):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.state = GameState.MENU
        
        self.player = Player(
            position=Vector2(screen_width // 2, screen_height - 80),
            velocity=Vector2(0, 0)
        )
        
        self.bullets: List[Bullet] = []
        self.enemy_bullets: List[Bullet] = []
        self.enemies: List[Enemy] = []
        self.explosions: List[Explosion] = []
        
        self.score = 0
        self.level = 1
        self.spawn_timer = 0.0
        self.spawn_interval = 2.0
        
    def start_game(self):
        """Начать новую игру"""
        self.state = GameState.PLAYING
        self.player.hp = self.player.max_hp
        self.player.position = Vector2(self.screen_width // 2, self.screen_height - 80)
        self.bullets.clear()
        self.enemy_bullets.clear()
        self.enemies.clear()
        self.explosions.clear()
        self.score = 0
        self.level = 1
        
    def toggle_pause(self):
        """Переключить паузу"""
        if self.state == GameState.PLAYING:
            self.state = GameState.PAUSED
        elif self.state == GameState.PAUSED:
            self.state = GameState.PLAYING
            
    def update(self, dt: float):
        """Обновление игровой логики"""
        if self.state != GameState.PLAYING:
            return
            
        # Обновление игрока
        self._update_player(dt)
        
        # Обновление пуль
        self._update_bullets(dt)
        
        # Обновление врагов
        self._update_enemies(dt)
        
        # Спавн врагов
        self._spawn_enemies(dt)
        
        # Обновление взрывов
        self._update_explosions(dt)
        
        # Проверка коллизий
        self._check_collisions()
        
        # Проверка Game Over
        if self.player.hp <= 0:
            self.state = GameState.GAME_OVER
            
    def _update_player(self, dt: float):
        """Обновление состояния игрока"""
        # Движение
        self.player.position = self.player.position + self.player.velocity
        
        # Ограничение по границам
        self.player.position.x = max(self.player.width // 2, 
                                     min(self.screen_width - self.player.width // 2, 
                                         self.player.position.x))
        
        # Кулдаун выстрела
        if self.player.shoot_cooldown > 0:
            self.player.shoot_cooldown -= dt
            
        # Щит
        if self.player.shield_active:
            self.player.shield_time -= dt
            if self.player.shield_time <= 0:
                self.player.shield_active = False
                
    def _update_bullets(self, dt: float):
        """Обновление пуль"""
        # Пули игрока
        for bullet in self.bullets[:]:
            bullet.position = bullet.position + bullet.velocity
            if bullet.position.y < -20:
                self.bullets.remove(bullet)
                
        # Пули врагов
        for bullet in self.enemy_bullets[:]:
            bullet.position = bullet.position + bullet.velocity
            if bullet.position.y > self.screen_height + 20:
                self.enemy_bullets.remove(bullet)
                
    def _update_enemies(self, dt: float):
        """Обновление врагов"""
        for enemy in self.enemies[:]:
            enemy.position = enemy.position + enemy.velocity
            
            # Враги стреляют
            if enemy.enemy_type == 1:  # Только корабли стреляют
                enemy.shoot_cooldown -= dt
                if enemy.shoot_cooldown <= 0:
                    self._enemy_shoot(enemy)
                    enemy.shoot_cooldown = random.uniform(2.0, 4.0)
            
            # Удаление врагов за экраном
            if enemy.position.y > self.screen_height + 50:
                self.enemies.remove(enemy)
                
    def _update_explosions(self, dt: float):
        """Обновление взрывов"""
        for explosion in self.explosions[:]:
            explosion.frame += 1
            if explosion.frame >= explosion.max_frames:
                self.explosions.remove(explosion)
                
    def _spawn_enemies(self, dt: float):
        """Спавн врагов"""
        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0
            
            # Случайный тип врага
            enemy_type = random.choices([0, 1], weights=[60, 40])[0]
            
            enemy = Enemy(
                position=Vector2(random.randint(50, self.screen_width - 50), -50),
                velocity=Vector2(random.uniform(-1, 1), random.uniform(1.5, 3.0)),
                enemy_type=enemy_type,
                hp=20 if enemy_type == 0 else 40,
                max_hp=20 if enemy_type == 0 else 40
            )
            self.enemies.append(enemy)
            
    def _check_collisions(self):
        """Проверка столкновений"""
        # Пули игрока vs враги
        for bullet in self.bullets[:]:
            for enemy in self.enemies[:]:
                if self._rect_collision(
                    bullet.position.x, bullet.position.y, bullet.width, bullet.height,
                    enemy.position.x, enemy.position.y, enemy.width, enemy.height
                ):
                    enemy.hp -= bullet.damage
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    
                    if enemy.hp <= 0:
                        if enemy in self.enemies:
                            self.enemies.remove(enemy)
                        self.score += 10 if enemy.enemy_type == 0 else 25
                        self._create_explosion(enemy.position)
                    break
                    
        # Пули врагов vs игрок
        if not self.player.shield_active:
            for bullet in self.enemy_bullets[:]:
                if self._rect_collision(
                    bullet.position.x, bullet.position.y, bullet.width, bullet.height,
                    self.player.position.x, self.player.position.y, 
                    self.player.width, self.player.height
                ):
                    self.player.hp -= 10
                    self.enemy_bullets.remove(bullet)
                    
        # Враги vs игрок
        if not self.player.shield_active:
            for enemy in self.enemies[:]:
                if self._rect_collision(
                    enemy.position.x, enemy.position.y, enemy.width, enemy.height,
                    self.player.position.x, self.player.position.y,
                    self.player.width, self.player.height
                ):
                    self.player.hp -= 20
                    if enemy in self.enemies:
                        self.enemies.remove(enemy)
                    self._create_explosion(enemy.position)
                    
    def _rect_collision(self, x1, y1, w1, h1, x2, y2, w2, h2):
        """Проверка прямоугольного столкновения"""
        return (abs(x1 - x2) < (w1 + w2) / 2 and 
                abs(y1 - y2) < (h1 + h2) / 2)
                
    def _create_explosion(self, position: Vector2):
        """Создать взрыв"""
        self.explosions.append(Explosion(position=Vector2(position.x, position.y)))
        
    def _enemy_shoot(self, enemy: Enemy):
        """Враг стреляет"""
        bullet = Bullet(
            position=Vector2(enemy.position.x, enemy.position.y + enemy.height // 2),
            velocity=Vector2(0, 4.0),
            is_player=False,
            damage=10
        )
        self.enemy_bullets.append(bullet)
        
    def player_shoot(self):
        """Игрок стреляет"""
        if self.player.shoot_cooldown <= 0:
            bullet = Bullet(
                position=Vector2(self.player.position.x, self.player.position.y - 20),
                velocity=Vector2(0, -8.0),
                is_player=True
            )
            self.bullets.append(bullet)
            self.player.shoot_cooldown = 0.3
            
    def player_move_left(self):
        """Игрок движется влево"""
        self.player.velocity.x = -self.player.speed
        
    def player_move_right(self):
        """Игрок движется вправо"""
        self.player.velocity.x = self.player.speed
        
    def player_stop(self):
        """Остановить игрока"""
        self.player.velocity.x = 0