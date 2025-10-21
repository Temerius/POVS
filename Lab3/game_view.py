"""
game_view.py
VIEW - Визуализация игры на Pygame
"""

import pygame
import random
import os
from game_model import GameModel, GameState

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
        
        # Загрузка изображений
        self._load_images()

    def load_image(self, path, size=None, colorkey=(255, 255, 255)):
        try:
            image = pygame.image.load(path).convert() 
            image.set_colorkey(colorkey)
            image.set_colorkey((0, 0, 0))
            if size:
                image = pygame.transform.smoothscale(image, size)
            return image
        except Exception as e:
            print(f"⚠ {path} not found ({e}), using placeholder")
            return None



    def _load_images(self):
        """Загрузка спрайтов"""
        self.img_player = self.load_image('player_ship.png', (60, 40))
        print(self.img_player.get_bitsize(), self.img_player.get_masks())
        self.img_asteroid = self.load_image('enemy_asteroid.png', (40, 40))
        self.img_enemy_ship = self.load_image('enemy_ship.png', (40, 40))

        
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
        
    def _draw_player(self, player):
        """Рисуем игрока"""
        x, y = int(player.position.x), int(player.position.y)
        
        if self.img_player:
            # Отрисовка спрайта
            rect = self.img_player.get_rect(center=(x, y))
            self.screen.blit(self.img_player, rect)
        else:
            # Fallback - треугольник
            w, h = player.width, player.height
            points = [
                (x, y - h // 2),
                (x - w // 2, y + h // 2),
                (x + w // 2, y + h // 2)
            ]
            pygame.draw.polygon(self.screen, self.COLOR_CYAN, points)
            pygame.draw.polygon(self.screen, self.COLOR_WHITE, points, 2)
        
        # Щит
        if player.shield_active:
            pygame.draw.circle(self.screen, self.COLOR_GREEN, (x, y), 
                             player.width // 2 + 10, 2)
            
    def _draw_bullet(self, bullet, color):
        """Рисуем пулю"""
        x, y = int(bullet.position.x), int(bullet.position.y)
        pygame.draw.rect(self.screen, color, 
                        (x - bullet.width // 2, y - bullet.height // 2, 
                         bullet.width, bullet.height))
        
    def _draw_enemy(self, enemy):
        """Рисуем врага"""
        x, y = int(enemy.position.x), int(enemy.position.y)
        w, h = enemy.width, enemy.height
        
        if enemy.enemy_type == 0:  # Астероид
            if self.img_asteroid:
                rect = self.img_asteroid.get_rect(center=(x, y))
                self.screen.blit(self.img_asteroid, rect)
            else:
                # Fallback
                pygame.draw.circle(self.screen, self.COLOR_ORANGE, (x, y), w // 2)
                pygame.draw.circle(self.screen, self.COLOR_WHITE, (x, y), w // 2, 2)
        else:  # Вражеский корабль
            if self.img_enemy_ship:
                rect = self.img_enemy_ship.get_rect(center=(x, y))
                self.screen.blit(self.img_enemy_ship, rect)
            else:
                # Fallback
                points = [
                    (x, y + h // 2),
                    (x - w // 2, y - h // 2),
                    (x + w // 2, y - h // 2)
                ]
                pygame.draw.polygon(self.screen, self.COLOR_RED, points)
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
            
    def _draw_explosion(self, explosion):
        """Рисуем взрыв (процедурная анимация)"""
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
        pygame.draw.rect(self.screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        
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
        
        controls1 = self.font_small.render("Controls: Arrow Keys to Move", 
                                          True, self.COLOR_WHITE)
        controls1_rect = controls1.get_rect(center=(self.screen_width // 2, 430))
        self.screen.blit(controls1, controls1_rect)
        
        controls2 = self.font_small.render("SPACE - Shoot | P - Pause | ESC - Quit", 
                                          True, self.COLOR_WHITE)
        controls2_rect = controls2.get_rect(center=(self.screen_width // 2, 460))
        self.screen.blit(controls2, controls2_rect)
        
    def _draw_pause(self):
        """Пауза"""
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        text = self.font_large.render("PAUSED", True, self.COLOR_YELLOW)
        text_rect = text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        self.screen.blit(text, text_rect)
        
        hint = self.font_small.render("Press P to Resume", True, self.COLOR_WHITE)
        hint_rect = hint.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 50))
        self.screen.blit(hint, hint_rect)
        
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
        
        restart = self.font_small.render("Press R to Restart | ESC to Quit", True, self.COLOR_WHITE)
        restart_rect = restart.get_rect(center=(self.screen_width // 2, 400))
        self.screen.blit(restart, restart_rect)