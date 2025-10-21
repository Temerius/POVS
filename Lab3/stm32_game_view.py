"""
stm32_game_view.py - С ПОДДЕРЖКОЙ МЕНЮ И ВЗРЫВОВ
Визуализация игры, получающей данные от STM32
"""

import pygame
import random
import time
from protocol import GameStatePacket, MenuStatePacket

class STM32GameView:
    """Отрисовка игры на основе данных от STM32"""
    
    def __init__(self, screen_width=800, screen_height=600):
        pygame.init()
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Space Defender - STM32 Mode")
        self.clock = pygame.time.Clock()
        
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Шрифты
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
        self.font_tiny = pygame.font.Font(None, 18)
        
        # Цвета
        self.COLOR_BG = (10, 10, 30)
        self.COLOR_WHITE = (255, 255, 255)
        self.COLOR_RED = (255, 50, 50)
        self.COLOR_GREEN = (50, 255, 50)
        self.COLOR_YELLOW = (255, 255, 50)
        self.COLOR_CYAN = (50, 255, 255)
        self.COLOR_ORANGE = (255, 150, 50)
        
        # Звёзды
        self.stars = [
            (random.randint(0, screen_width), random.randint(0, screen_height), 
             random.uniform(0.5, 2.0))
            for _ in range(100)
        ]
        
        # Загрузка спрайтов
        self._load_images()
        
    def _load_images(self):
        """Загрузка спрайтов"""
        try:
            self.img_player = pygame.image.load('player_ship.png').convert_alpha()
            self.img_player = pygame.transform.scale(self.img_player, (60, 40))
        except:
            self.img_player = None
            
        try:
            self.img_asteroid = pygame.image.load('enemy_asteroid.png').convert_alpha()
            self.img_asteroid = pygame.transform.scale(self.img_asteroid, (40, 40))
        except:
            self.img_asteroid = None
            
        try:
            self.img_enemy_ship = pygame.image.load('enemy_ship.png').convert_alpha()
            self.img_enemy_ship = pygame.transform.scale(self.img_enemy_ship, (40, 40))
        except:
            self.img_enemy_ship = None
            
    def render(self, packet: GameStatePacket = None, menu: MenuStatePacket = None, explosions=None):
        """Отрисовка кадра"""
        self.screen.fill(self.COLOR_BG)
        
        # Звёзды
        self._draw_stars()
        
        if packet:
            # Игровой процесс
            self._draw_game(packet, explosions or [])
        elif menu:
            # Меню
            self._draw_menu(menu)
        else:
            # Ожидание подключения
            self._draw_waiting()
            
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
                             
    def _draw_game(self, packet: GameStatePacket, explosions):
        """Отрисовка игрового процесса"""
        # Игрок
        self._draw_player(packet.player_x, packet.player_y, packet.player_hp)
        
        # Враги
        for ex, ey, etype, ehp in packet.enemies:
            self._draw_enemy(ex, ey, etype, ehp)
            
        # Пули игрока
        for bx, by in packet.bullets:
            self._draw_bullet(bx, by, self.COLOR_CYAN)
            
        # Пули врагов
        for bx, by in packet.enemy_bullets:
            self._draw_bullet(bx, by, self.COLOR_RED)
            
        # Взрывы
        current_time = time.time()
        for ex, ey, exp_time in explosions:
            age = current_time - exp_time
            if age < 0.5:  # Взрыв длится 0.5 секунды
                self._draw_explosion(ex, ey, age)
            
        # HUD
        self._draw_hud(packet)
        
    def _draw_menu(self, menu: MenuStatePacket):
        """Отрисовка меню"""
        # Заголовок
        if menu.game_state == 0:  # GAME_MENU
            title = "SPACE DEFENDER"
            subtitle = "Press FIRE to start"
        elif menu.game_state == 2:  # GAME_PAUSED
            title = "PAUSED"
            subtitle = "Select option with LEFT/RIGHT"
        elif menu.game_state == 3:  # GAME_OVER
            title = "GAME OVER"
            subtitle = f"Final Score: {menu.score}"
        else:
            title = "MENU"
            subtitle = ""
            
        title_text = self.font_large.render(title, True, self.COLOR_CYAN)
        title_rect = title_text.get_rect(center=(self.screen_width // 2, 150))
        self.screen.blit(title_text, title_rect)
        
        if subtitle:
            subtitle_text = self.font_small.render(subtitle, True, self.COLOR_WHITE)
            subtitle_rect = subtitle_text.get_rect(center=(self.screen_width // 2, 220))
            self.screen.blit(subtitle_text, subtitle_rect)
        
        # Пункты меню
        menu_items = []
        if menu.game_state == 0:  # GAME_MENU
            menu_items = ["START GAME"]
        elif menu.game_state == 2:  # GAME_PAUSED
            menu_items = ["CONTINUE", "RESTART", "EXIT"]
        elif menu.game_state == 3:  # GAME_OVER
            menu_items = ["RESTART", "EXIT"]
            
        y_start = 300
        y_spacing = 50
        
        for i, item in enumerate(menu_items):
            color = self.COLOR_YELLOW if i == menu.selected_item else self.COLOR_WHITE
            text = self.font_medium.render(item, True, color)
            text_rect = text.get_rect(center=(self.screen_width // 2, y_start + i * y_spacing))
            self.screen.blit(text, text_rect)
            
            # Стрелка для выбранного пункта
            if i == menu.selected_item:
                arrow = self.font_medium.render(">", True, self.COLOR_YELLOW)
                arrow_rect = arrow.get_rect(midright=(text_rect.left - 20, text_rect.centery))
                self.screen.blit(arrow, arrow_rect)
        
        # Подсказки управления
        hint = "Controls: LEFT/RIGHT - select, FIRE - confirm"
        hint_text = self.font_tiny.render(hint, True, self.COLOR_WHITE)
        hint_rect = hint_text.get_rect(center=(self.screen_width // 2, self.screen_height - 50))
        self.screen.blit(hint_text, hint_rect)
        
    def _draw_player(self, x, y, hp):
        """Отрисовка игрока"""
        if self.img_player:
            rect = self.img_player.get_rect(center=(x, y))
            self.screen.blit(self.img_player, rect)
        else:
            w, h = 60, 40
            points = [
                (x, y - h // 2),
                (x - w // 2, y + h // 2),
                (x + w // 2, y + h // 2)
            ]
            pygame.draw.polygon(self.screen, self.COLOR_CYAN, points)
            pygame.draw.polygon(self.screen, self.COLOR_WHITE, points, 2)
            
    def _draw_enemy(self, x, y, etype, hp):
        """Отрисовка врага"""
        if etype == 0:  # Asteroid
            if self.img_asteroid:
                rect = self.img_asteroid.get_rect(center=(x, y))
                self.screen.blit(self.img_asteroid, rect)
            else:
                pygame.draw.circle(self.screen, self.COLOR_ORANGE, (x, y), 20)
                pygame.draw.circle(self.screen, self.COLOR_WHITE, (x, y), 20, 2)
        else:  # Enemy ship
            if self.img_enemy_ship:
                rect = self.img_enemy_ship.get_rect(center=(x, y))
                self.screen.blit(self.img_enemy_ship, rect)
            else:
                w, h = 40, 40
                points = [
                    (x, y + h // 2),
                    (x - w // 2, y - h // 2),
                    (x + w // 2, y - h // 2)
                ]
                pygame.draw.polygon(self.screen, self.COLOR_RED, points)
                pygame.draw.polygon(self.screen, self.COLOR_WHITE, points, 2)
                
        # HP bar
        if hp < 100:
            hp_ratio = hp / 100.0
            bar_width = 40
            pygame.draw.rect(self.screen, self.COLOR_RED, 
                           (x - bar_width // 2, y - 25, bar_width, 4))
            pygame.draw.rect(self.screen, self.COLOR_GREEN, 
                           (x - bar_width // 2, y - 25, 
                            int(bar_width * hp_ratio), 4))
                            
    def _draw_bullet(self, x, y, color):
        """Отрисовка пули"""
        pygame.draw.rect(self.screen, color, (x - 2, y - 6, 4, 12))
        
    def _draw_explosion(self, x, y, age):
        """Отрисовка взрыва"""
        # age от 0 до 0.5 секунд
        progress = age / 0.5
        radius = int(20 * (1 + progress * 2))
        alpha = int(255 * (1 - progress))
        
        # Несколько окружностей для эффекта
        colors = [self.COLOR_YELLOW, self.COLOR_ORANGE, self.COLOR_RED]
        for i, color in enumerate(colors):
            r = radius - i * 5
            if r > 0:
                pygame.draw.circle(self.screen, color, (x, y), r, 2)
        
    def _draw_hud(self, packet: GameStatePacket):
        """HUD"""
        # Score
        score_text = self.font_medium.render(f"Score: {packet.score}", True, self.COLOR_WHITE)
        self.screen.blit(score_text, (10, 10))
        
        # Level
        level_text = self.font_small.render(f"Level: {packet.level}", True, self.COLOR_WHITE)
        self.screen.blit(level_text, (10, 50))
        
        # HP Bar
        hp_ratio = packet.player_hp / 100.0
        bar_width = 200
        bar_height = 20
        bar_x = self.screen_width - bar_width - 10
        bar_y = 10
        
        pygame.draw.rect(self.screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        
        if hp_ratio > 0.5:
            color = self.COLOR_GREEN
        elif hp_ratio > 0.3:
            color = self.COLOR_YELLOW
        else:
            color = self.COLOR_RED
        pygame.draw.rect(self.screen, color, 
                        (bar_x, bar_y, int(bar_width * hp_ratio), bar_height))
        
        pygame.draw.rect(self.screen, self.COLOR_WHITE, (bar_x, bar_y, bar_width, bar_height), 2)
        
        hp_text = self.font_small.render(f"HP: {packet.player_hp}/100", True, self.COLOR_WHITE)
        self.screen.blit(hp_text, (bar_x + 5, bar_y + 2))
        
        # STM32 indicator
        stm32_text = self.font_tiny.render("STM32 Connected", True, self.COLOR_GREEN)
        self.screen.blit(stm32_text, (self.screen_width - 150, self.screen_height - 25))
        
    def _draw_waiting(self):
        """Ожидание подключения"""
        text = self.font_large.render("Waiting for STM32...", True, self.COLOR_YELLOW)
        text_rect = text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        self.screen.blit(text, text_rect)
        
        hint = self.font_small.render("Check USART connection", True, self.COLOR_WHITE)
        hint_rect = hint.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 50))
        self.screen.blit(hint, hint_rect)