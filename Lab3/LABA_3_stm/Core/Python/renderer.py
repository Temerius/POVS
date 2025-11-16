 

import pygame
import math
from config import *


class GameRenderer:
    """Класс для отрисовки всех элементов игры"""
    
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.big_font = pygame.font.Font(None, 48)
        self.wave_offset = 0
        
         
        self._load_sprites()
    
    def _load_sprites(self):
        """Загрузка спрайтов"""
        try:
            self.player_sprite = pygame.image.load('img/player/player_up.png').convert_alpha()
            self.player_sprite = pygame.transform.scale(self.player_sprite, (PLAYER_SIZE, PLAYER_SIZE))
        except:
            self.player_sprite = self._create_player_sprite()
        
        try:
            self.enemy_simple_sprite = pygame.image.load('img/enemy_simple/enemy_simple_down.png').convert_alpha()
            self.enemy_simple_sprite = pygame.transform.scale(self.enemy_simple_sprite, (ENEMY_SIMPLE_SIZE, ENEMY_SIMPLE_SIZE))
        except:
            self.enemy_simple_sprite = self._create_enemy_sprite(ENEMY_SIMPLE_SIZE, RED)
        
        try:
            self.enemy_hard_sprite = pygame.image.load('img/enemy_hard/enemy_hard_down.png').convert_alpha()
            self.enemy_hard_sprite = pygame.transform.scale(self.enemy_hard_sprite, (ENEMY_HARD_SIZE, ENEMY_HARD_SIZE))
        except:
            self.enemy_hard_sprite = self._create_enemy_sprite(ENEMY_HARD_SIZE, (180, 0, 0))
    
    def _create_player_sprite(self):
        """Создание спрайта игрока по умолчанию"""
        surf = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE), pygame.SRCALPHA)
        pygame.draw.polygon(surf, (0, 100, 255), [
            (PLAYER_SIZE//2, 0), (PLAYER_SIZE, PLAYER_SIZE),
            (PLAYER_SIZE//2, PLAYER_SIZE*0.7), (0, PLAYER_SIZE)
        ])
        return surf
    
    def _create_enemy_sprite(self, size, color):
        """Создание спрайта врага по умолчанию"""
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.polygon(surf, color, [
            (size//2, 0), (size, size),
            (size//2, size*0.7), (0, size)
        ])
        return surf
    
    def draw_waves(self):
        """Рисуем волны на море"""
        for layer in range(-2, SCREEN_HEIGHT // 35 + 3):
            base_y = layer * 35 + self.wave_offset
            color = (10 + (layer % 3) * 5, 95 + (layer % 3) * 5, 170)
            
            points = []
            for x in range(0, SCREEN_WIDTH + 80, 5):
                y = base_y + 12 * math.sin((2 * math.pi * x / 80) + (self.wave_offset * 0.03))
                y += 12 * 0.3 * math.sin((4 * math.pi * x / 80) + (self.wave_offset * 0.045))
                points.append((x, y))
            
            if len(points) > 1:
                pygame.draw.lines(self.screen, color, False, points, 2)
        
        self.wave_offset = (self.wave_offset + 2) % 40
    
    def draw_whirlpools(self, whirlpools, camera_y):
        """Рисуем водовороты из данных STM32"""
        rotation = (pygame.time.get_ticks() / 10) % 360
        
        for whirlpool in whirlpools:
            x = int(whirlpool['x'])
            y_screen = int(whirlpool['y'] - camera_y)
            
            if y_screen < -150 or y_screen > SCREEN_HEIGHT + 150:
                continue
            
            for i in range(4):
                r = WHIRLPOOL_RADIUS - i * 10
                for j in range(8):
                    angle = math.radians(j * 45 + rotation + i * 30)
                    x1 = x + math.cos(angle) * r
                    y1 = y_screen + math.sin(angle) * r
                    x2 = x + math.cos(angle) * (r - 8)
                    y2 = y_screen + math.sin(angle) * (r - 8)
                    
                    color = (60 + i * 40, 60 + i * 40, 255)
                    pygame.draw.line(self.screen, color, (x1, y1), (x2, y2), 3)
            
            center_color = (100, 100, 100) if whirlpool['used'] else (30, 30, 150)
            pygame.draw.circle(self.screen, center_color, (x, y_screen), 12)
    
    def draw_enemies(self, enemies, camera_y):
        """Рисуем врагов из данных STM32"""
        for enemy in enemies:
            x = int(enemy['x'])
            y_screen = int(enemy['y'] - camera_y)
            
            if y_screen < -100 or y_screen > SCREEN_HEIGHT + 100:
                continue
            
             
            base_sprite = self.enemy_simple_sprite if enemy['type'] == 0 else self.enemy_hard_sprite
            
             
            direction = enemy.get('direction', 2)
            
            if direction == 0:   
                sprite = pygame.transform.rotate(base_sprite, 0)
            elif direction == 1:   
                sprite = pygame.transform.rotate(base_sprite, -90)
            elif direction == 2:   
                sprite = base_sprite
            elif direction == 3:   
                sprite = pygame.transform.rotate(base_sprite, 90)
            else:
                sprite = base_sprite
            
            rect = sprite.get_rect(center=(x, y_screen))
            self.screen.blit(sprite, rect.topleft)
    
    def draw_projectiles(self, projectiles, camera_y):
        """Рисуем снаряды"""
        for proj in projectiles:
            x = int(proj['x'])
            y_screen = int(proj['y'] - camera_y)
            
            color = PROJECTILE_COLOR_PLAYER if proj['is_player_shot'] else PROJECTILE_COLOR_ENEMY
            pygame.draw.circle(self.screen, color, (x, y_screen), PROJECTILE_RADIUS)
    
    def draw_player(self, player_x, player_y, player_angle, camera_y):
        """Рисуем игрока"""
        x = int(player_x)
        y_screen = int(player_y - camera_y)
        
        rotated = pygame.transform.rotate(self.player_sprite, -player_angle)
        rect = rotated.get_rect(center=(x, y_screen))
        self.screen.blit(rotated, rect.topleft)
    
    def draw_ui(self, game_state, islands_count):
        """Рисуем UI"""
         
        health_text = self.font.render(
            f"HP: {max(0, game_state.player_health)}/{PLAYER_MAX_HEALTH}", 
            True, WHITE
        )
        self.screen.blit(health_text, (UI_PADDING, UI_PADDING))
        
        health_ratio = max(0, game_state.player_health) / PLAYER_MAX_HEALTH
        
        pygame.draw.rect(self.screen, (100, 0, 0), 
                        (UI_PADDING, 60, UI_HEALTH_BAR_WIDTH, UI_HEALTH_BAR_HEIGHT))
        pygame.draw.rect(self.screen, (0, 200, 0), 
                        (UI_PADDING, 60, int(UI_HEALTH_BAR_WIDTH * health_ratio), UI_HEALTH_BAR_HEIGHT))
        pygame.draw.rect(self.screen, WHITE, 
                        (UI_PADDING, 60, UI_HEALTH_BAR_WIDTH, UI_HEALTH_BAR_HEIGHT), 3)
        
         
        score_text = self.font.render(f"Счёт: {game_state.player_score}", True, GOLD)
        self.screen.blit(score_text, (SCREEN_WIDTH - 250, UI_PADDING))
        
         
        miles = int(abs(game_state.player_y) / 10)
        miles_text = self.font.render(f"Мили: {miles}", True, WHITE)
        self.screen.blit(miles_text, (SCREEN_WIDTH - 250, 60))
        
         
        angle_text = self.big_font.render(f"Угол: {int(game_state.player_angle)}°", True, CYAN)
        self.screen.blit(angle_text, (SCREEN_WIDTH // 2 - 100, UI_PADDING))
        
         
        if abs(game_state.player_angle) > 5:
            direction = "↖ ЗАЛП ВЛЕВО-ВВЕРХ" if game_state.player_angle > 5 else "ЗАЛП ВПРАВО-ВВЕРХ ↗"
            dir_color = RED if game_state.player_shoot_cooldown == 0 else (100, 100, 100)
            dir_text = self.font.render(direction, True, dir_color)
            self.screen.blit(dir_text, (SCREEN_WIDTH // 2 - 200, 75))
        
         
        self._draw_controls()
        
         
        self._draw_stats(game_state, islands_count)
    
    def _draw_controls(self):
        """Отрисовка подсказок управления"""
        controls = [
            "Управление:",
            "A - Лево (плывёшь влево, стреляешь вправо)",
            "D - Право (плывёшь вправо, стреляешь влево)",
            "SPACE - Залп вверх-вбок",
            "ESC - Выход"
        ]
        
        pygame.draw.rect(self.screen, (0, 0, 0, 180), 
                        (SCREEN_WIDTH - 450, SCREEN_HEIGHT - 160, 440, 150))
        pygame.draw.rect(self.screen, WHITE, 
                        (SCREEN_WIDTH - 450, SCREEN_HEIGHT - 160, 440, 150), 2)
        
        for i, text in enumerate(controls):
            color = GOLD if i == 0 else WHITE
            control_text = self.small_font.render(text, True, color)
            self.screen.blit(control_text, (SCREEN_WIDTH - 440, SCREEN_HEIGHT - 145 + i * 28))
    
    def _draw_stats(self, game_state, islands_count):
        """Отрисовка статистики"""
        whirlpool_count = len(game_state.whirlpools)
        enemy_count = len(game_state.enemies)
        
        stats_text = self.small_font.render(
            f"Островов: {islands_count} | Врагов: {enemy_count} | Водоворотов: {whirlpool_count}", 
            True, (255, 200, 100))
        self.screen.blit(stats_text, (UI_PADDING, SCREEN_HEIGHT - 40))
        
         
        active_whirlpools = sum(1 for w in game_state.whirlpools if not w['used'])
        if whirlpool_count > 0:
            whirlpool_info = self.small_font.render(
                f"🌀 Активных водоворотов: {active_whirlpools}/{whirlpool_count}", 
                True, CYAN)
            self.screen.blit(whirlpool_info, (UI_PADDING, SCREEN_HEIGHT - 70))
        
         
        simple_enemies = sum(1 for e in game_state.enemies if e['type'] == 0)
        hard_enemies = sum(1 for e in game_state.enemies if e['type'] == 1)
        if enemy_count > 0:
            enemy_info = self.small_font.render(
                f"⚔️ Враги: {simple_enemies} простых | {hard_enemies} серьезных", 
                True, (255, 100, 100))
            self.screen.blit(enemy_info, (UI_PADDING, SCREEN_HEIGHT - 100))
    
    def draw_waiting_screen(self):
        """Экран ожидания подключения STM32"""
        self.screen.fill(BLACK)
        text = self.font.render("Ожидание STM32...", True, WHITE)
        self.screen.blit(text, (SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2))
    
    def draw_game_over(self, game_state):
        """Экран окончания игры"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(220)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        game_over_font = pygame.font.Font(None, 84)
        game_over_text = game_over_font.render("ИГРА ОКОНЧЕНА", True, RED)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
        
        score_text = self.big_font.render(f"Финальный счёт: {game_state.player_score}", True, GOLD)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        
        miles = int(abs(game_state.player_y) / 10)
        distance_text = self.font.render(f"Пройдено: {miles} морских миль", 
                                        True, WHITE)
        distance_rect = distance_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
        
        restart_text = self.font.render("Нажмите R для перезапуска", True, CYAN)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 120))
        
        self.screen.blit(game_over_text, game_over_rect)
        self.screen.blit(score_text, score_rect)
        self.screen.blit(distance_text, distance_rect)
        self.screen.blit(restart_text, restart_rect)


    def draw_benchmark(self, screen, benchmark_stats, x=10, y=120):
        """Отрисовка статистики бенчмарка от STM32"""
        if not benchmark_stats:
            return
        
         
        bg_rect = pygame.Rect(x, y, 250, 80)
        bg_surf = pygame.Surface((250, 80))
        bg_surf.set_alpha(180)
        bg_surf.fill((0, 0, 0))
        screen.blit(bg_surf, (x, y))
        
         
        pygame.draw.rect(screen, (100, 255, 100), bg_rect, 2)
        
         
        title = self.small_font.render("STM32 Performance", True, (100, 255, 100))
        screen.blit(title, (x + 10, y + 5))
        
         
        stats_text = self.small_font.render(benchmark_stats, True, (255, 255, 255))
        screen.blit(stats_text, (x + 10, y + 30))
        
         
        if "FPS:" in benchmark_stats:
            try:
                fps_str = benchmark_stats.split("FPS:")[1].split()[0]
                fps = int(fps_str)
                if fps < 50:
                    warning = self.small_font.render("⚠ LOW FPS", True, (255, 100, 100))
                    screen.blit(warning, (x + 10, y + 55))
            except:
                pass