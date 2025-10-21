"""
Space Defender Game - MVC Architecture
Визуализация игры на Pygame с возможностью интеграции STM32
"""

import pygame
import random
import math
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional

# ============================================================================
# MODEL - Игровая логика (может быть перенесена на STM32)
# ============================================================================

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
    enemy_type: int = 0  # 0=астероид, 1=враг, 2=босс
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
            enemy_type = random.choices([0, 1], weights=[70, 30])[0]
            
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
                    self.bullets.remove(bullet)
                    
                    if enemy.hp <= 0:
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


# ============================================================================
# VIEW - Визуализация (Pygame)
# ============================================================================

class GameView:
    """Отрисовка игры"""
    
    def __init__(self, screen_width=800, screen_height=600):
        pygame.init()
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Space Defender")
        self.clock = pygame.time.Clock()
        
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Шрифты
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
        
        # Цвета
        self.COLOR_BG = (10, 10, 30)
        self.COLOR_WHITE = (255, 255, 255)
        self.COLOR_RED = (255, 50, 50)
        self.COLOR_GREEN = (50, 255, 50)
        self.COLOR_YELLOW = (255, 255, 50)
        self.COLOR_CYAN = (50, 255, 255)
        self.COLOR_ORANGE = (255, 150, 50)
        
        # Звёзды на фоне
        self.stars = [
            (random.randint(0, screen_width), random.randint(0, screen_height), 
             random.uniform(0.5, 2.0))
            for _ in range(100)
        ]
        
    def render(self, model: GameModel):
        """Отрисовка всего"""
        self.screen.fill(self.COLOR_BG)
        
        # Звёзды
        self._draw_stars()
        
        if model.state == GameState.MENU:
            self._draw_menu(model)
        elif model.state == GameState.PLAYING:
            self._draw_game(model)
        elif model.state == GameState.PAUSED:
            self._draw_game(model)
            self._draw_pause()
        elif model.state == GameState.GAME_OVER:
            self._draw_game_over(model)
            
        pygame.display.flip()
        
    def _draw_stars(self):
        """Рисуем звёзды"""
        for i, (x, y, speed) in enumerate(self.stars):
            y += speed
            if y > self.screen_height:
                y = 0
                x = random.randint(0, self.screen_width)
            self.stars[i] = (x, y, speed)
            
            brightness = int(150 + 105 * (speed / 2.0))
            pygame.draw.circle(self.screen, (brightness, brightness, brightness), 
                             (int(x), int(y)), 1)
            
    def _draw_game(self, model: GameModel):
        """Отрисовка игрового процесса"""
        # Игрок
        self._draw_player(model.player)
        
        # Пули
        for bullet in model.bullets:
            self._draw_bullet(bullet, self.COLOR_CYAN)
        for bullet in model.enemy_bullets:
            self._draw_bullet(bullet, self.COLOR_RED)
            
        # Враги
        for enemy in model.enemies:
            self._draw_enemy(enemy)
            
        # Взрывы
        for explosion in model.explosions:
            self._draw_explosion(explosion)
            
        # HUD
        self._draw_hud(model)
        
    def _draw_player(self, player: Player):
        """Рисуем игрока (треугольный корабль)"""
        x, y = int(player.position.x), int(player.position.y)
        w, h = player.width, player.height
        
        # Корабль - треугольник
        points = [
            (x, y - h // 2),           # Нос
            (x - w // 2, y + h // 2),  # Левое крыло
            (x + w // 2, y + h // 2)   # Правое крыло
        ]
        pygame.draw.polygon(self.screen, self.COLOR_CYAN, points)
        pygame.draw.polygon(self.screen, self.COLOR_WHITE, points, 2)
        
        # Щит
        if player.shield_active:
            pygame.draw.circle(self.screen, self.COLOR_GREEN, (x, y), w // 2 + 10, 2)
            
    def _draw_bullet(self, bullet: Bullet, color):
        """Рисуем пулю"""
        x, y = int(bullet.position.x), int(bullet.position.y)
        pygame.draw.rect(self.screen, color, 
                        (x - bullet.width // 2, y - bullet.height // 2, 
                         bullet.width, bullet.height))
        
    def _draw_enemy(self, enemy: Enemy):
        """Рисуем врага"""
        x, y = int(enemy.position.x), int(enemy.position.y)
        w, h = enemy.width, enemy.height
        
        if enemy.enemy_type == 0:  # Астероид
            color = self.COLOR_ORANGE
            pygame.draw.circle(self.screen, color, (x, y), w // 2)
            pygame.draw.circle(self.screen, self.COLOR_WHITE, (x, y), w // 2, 2)
        else:  # Вражеский корабль
            color = self.COLOR_RED
            points = [
                (x, y + h // 2),           # Низ
                (x - w // 2, y - h // 2),  # Левое крыло
                (x + w // 2, y - h // 2)   # Правое крыло
            ]
            pygame.draw.polygon(self.screen, color, points)
            pygame.draw.polygon(self.screen, self.COLOR_WHITE, points, 2)
            
        # HP bar
        if enemy.hp < enemy.max_hp:
            hp_ratio = enemy.hp / enemy.max_hp
            bar_width = w
            pygame.draw.rect(self.screen, self.COLOR_RED, 
                           (x - bar_width // 2, y - h // 2 - 10, bar_width, 4))
            pygame.draw.rect(self.screen, self.COLOR_GREEN, 
                           (x - bar_width // 2, y - h // 2 - 10, 
                            int(bar_width * hp_ratio), 4))
            
    def _draw_explosion(self, explosion: Explosion):
        """Рисуем взрыв"""
        x, y = int(explosion.position.x), int(explosion.position.y)
        progress = explosion.frame / explosion.max_frames
        radius = int(explosion.radius * (1 + progress * 2))
        alpha = int(255 * (1 - progress))
        
        # Несколько окружностей для эффекта
        colors = [self.COLOR_YELLOW, self.COLOR_ORANGE, self.COLOR_RED]
        for i, color in enumerate(colors):
            r = radius - i * 5
            if r > 0:
                pygame.draw.circle(self.screen, color, (x, y), r, 2)
                
    def _draw_hud(self, model: GameModel):
        """HUD - очки, здоровье, уровень"""
        # Очки
        score_text = self.font_medium.render(f"Score: {model.score}", True, self.COLOR_WHITE)
        self.screen.blit(score_text, (10, 10))
        
        # Уровень
        level_text = self.font_small.render(f"Level: {model.level}", True, self.COLOR_WHITE)
        self.screen.blit(level_text, (10, 50))
        
        # HP Bar
        hp_ratio = model.player.hp / model.player.max_hp
        bar_width = 200
        bar_height = 20
        bar_x = self.screen_width - bar_width - 10
        bar_y = 10
        
        # Фон HP
        pygame.draw.rect(self.screen, self.COLOR_RED, (bar_x, bar_y, bar_width, bar_height))
        
        # Текущий HP
        if hp_ratio > 0.5:
            color = self.COLOR_GREEN
        elif hp_ratio > 0.3:
            color = self.COLOR_YELLOW
        else:
            color = self.COLOR_RED
        pygame.draw.rect(self.screen, color, 
                        (bar_x, bar_y, int(bar_width * hp_ratio), bar_height))
        
        # Рамка
        pygame.draw.rect(self.screen, self.COLOR_WHITE, (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Текст HP
        hp_text = self.font_small.render(f"HP: {model.player.hp}/{model.player.max_hp}", 
                                         True, self.COLOR_WHITE)
        self.screen.blit(hp_text, (bar_x + 5, bar_y + 2))
        
    def _draw_menu(self, model: GameModel):
        """Меню"""
        title = self.font_large.render("SPACE DEFENDER", True, self.COLOR_CYAN)
        title_rect = title.get_rect(center=(self.screen_width // 2, 200))
        self.screen.blit(title, title_rect)
        
        start = self.font_medium.render("Press SPACE to Start", True, self.COLOR_WHITE)
        start_rect = start.get_rect(center=(self.screen_width // 2, 350))
        self.screen.blit(start, start_rect)
        
        controls = self.font_small.render("Controls: Arrow Keys + Space to Shoot", 
                                         True, self.COLOR_WHITE)
        controls_rect = controls.get_rect(center=(self.screen_width // 2, 450))
        self.screen.blit(controls, controls_rect)
        
    def _draw_pause(self):
        """Пауза"""
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        text = self.font_large.render("PAUSED", True, self.COLOR_YELLOW)
        text_rect = text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        self.screen.blit(text, text_rect)
        
    def _draw_game_over(self, model: GameModel):
        """Game Over"""
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        title = self.font_large.render("GAME OVER", True, self.COLOR_RED)
        title_rect = title.get_rect(center=(self.screen_width // 2, 200))
        self.screen.blit(title, title_rect)
        
        score = self.font_medium.render(f"Final Score: {model.score}", True, self.COLOR_WHITE)
        score_rect = score.get_rect(center=(self.screen_width // 2, 300))
        self.screen.blit(score, score_rect)
        
        restart = self.font_small.render("Press R to Restart", True, self.COLOR_WHITE)
        restart_rect = restart.get_rect(center=(self.screen_width // 2, 400))
        self.screen.blit(restart, restart_rect)


# ============================================================================
# CONTROLLER - Управление вводом (клавиатура / STM32)
# ============================================================================

class InputController:
    """Контроллер ввода - легко заменить на USART"""
    
    def __init__(self):
        self.left_pressed = False
        self.right_pressed = False
        self.shoot_pressed = False
        self.shoot_last_state = False
        
    def update_keyboard(self, model: GameModel):
        """Обновление с клавиатуры (текущий метод)"""
        keys = pygame.key.get_pressed()
        
        # Движение
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            model.player_move_left()
            self.left_pressed = True
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            model.player_move_right()
            self.right_pressed = True
        else:
            model.player_stop()
            self.left_pressed = False
            self.right_pressed = False
            
        # Выстрел (только при нажатии, не зажатии)
        self.shoot_pressed = keys[pygame.K_SPACE]
        if self.shoot_pressed and not self.shoot_last_state:
            if model.state == GameState.PLAYING:
                model.player_shoot()
        self.shoot_last_state = self.shoot_pressed
        
    def update_stm32(self, model: GameModel, stm32_data: dict):
        """
        Обновление с STM32 (для будущей интеграции)
        
        Формат stm32_data:
        {
            'button_left': bool,
            'button_right': bool,
            'button_fire': bool,
            'state': int
        }
        """
        # TODO: Реализовать после интеграции USART
        pass


# ============================================================================
# MAIN - Главный цикл
# ============================================================================

def main():
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    FPS = 60
    
    model = GameModel(SCREEN_WIDTH, SCREEN_HEIGHT)
    view = GameView(SCREEN_WIDTH, SCREEN_HEIGHT)
    controller = InputController()
    
    running = True
    
    while running:
        dt = view.clock.tick(FPS) / 1000.0  # Секунды
        
        # События
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_p:
                    model.toggle_pause()
                elif event.key == pygame.K_SPACE and model.state == GameState.MENU:
                    model.start_game()
                elif event.key == pygame.K_r and model.state == GameState.GAME_OVER:
                    model.start_game()
                    
        # Обновление ввода
        controller.update_keyboard(model)
        
        # Обновление логики
        model.update(dt)
        
        # Отрисовка
        view.render(model)
        
    pygame.quit()

if __name__ == "__main__":
    main()