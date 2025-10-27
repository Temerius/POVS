# game.py - ГЛАВНЫЙ ФАЙЛ ИГРЫ
import pygame
import random
import math
import sys
from config import *
from player import Player
from island import Island
from shore import Shore

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Бескрайнее море — боевой корабль")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.big_font = pygame.font.Font(None, 48)
        
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150)
        
        # Камера следует за игроком
        self.camera_y = self.player.y - SCREEN_HEIGHT + 200
        
        self.islands = []
        self.projectiles = []
        self.left_shores = []  # Левые берега
        self.right_shores = []  # Правые берега
        
        # ВЕРХНЯЯ ГРАНИЦА МИРА (меньшие значения y = выше в мире)
        self.world_top = self.player.y - SCREEN_HEIGHT * 2
        
        self.wave_offset = 0
        
        # Начальная генерация мира - несколько сегментов ВВЕРХ (с меньшими y)
        self.generate_world_segment()
        self.generate_world_segment()
        self.generate_world_segment()
        
    def generate_world_segment(self):
        """Генерация сегмента мира ВВЕРХ от текущей верхней границы"""
        segment_height = 2000  # Высота сегмента
        segment_start = self.world_top - segment_height
        segment_end = self.world_top
        
        print(f"Генерация нового сегмента: {segment_start} -> {segment_end}")
        
        # БЕРЕГА ПО КРАЯМ
        self.left_shores.append(Shore('left', segment_start, segment_end))
        self.right_shores.append(Shore('right', segment_start, segment_end))
        
        current_y = segment_start
        islands_generated = 0
        
        # Генерируем острова СВЕРХУ ВНИЗ (от меньших y к большим)
        while current_y < segment_end:
            # КУЧА ОСТРОВОВ - 85% вероятность!!!
            if random.random() < 0.85:
                # Острова в центральной части (не у краёв)
                x = random.randint(150, SCREEN_WIDTH - 150)
                
                # Проверка близости (только с недавними островами)
                too_close = False
                for island in self.islands[-30:]:
                    dist = math.sqrt((island.x - x)**2 + (island.y - current_y)**2)
                    if dist < 120:
                        too_close = True
                        break
                
                if not too_close:
                    island = Island(x, current_y, random.randint(0, 1000000))
                    self.islands.append(island)
                    islands_generated += 1
            
            # Двигаемся ВНИЗ (y увеличивается)
            current_y += random.randint(60, 120)
        
        # Обновляем верхнюю границу мира
        self.world_top = segment_start
        print(f"Сгенерировано островов: {islands_generated}, всего: {len(self.islands)}")
        
    def update(self):
        keys = pygame.key.get_pressed()
        
        # Камера следует за игроком
        self.camera_y = self.player.y - SCREEN_HEIGHT + 200
        
        # Генерация нового мира когда игрок приближается к верхней границе
        if self.player.y < self.world_top + 1500:
            self.generate_world_segment()
        
        # Обновление игрока (проверяем столкновения с островами И берегами)
        all_obstacles = self.islands + self.left_shores + self.right_shores
        self.player.update(keys, all_obstacles)
        
        # Стрельба
        if keys[pygame.K_SPACE]:
            new_projectiles = self.player.shoot()
            if new_projectiles:
                self.projectiles.extend(new_projectiles)
        
        # Волны
        self.wave_offset = (self.wave_offset + 2) % 80
        
        # Обновление снарядов
        for proj in self.projectiles[:]:
            proj.update()
            if proj.lifetime <= 0 or proj.x < 0 or proj.x > SCREEN_WIDTH:
                self.projectiles.remove(proj)
        
        # ОЧИСТКА СТАРЫХ ОБЪЕКТОВ, которые позади игрока
        cleanup_threshold = self.player.y + SCREEN_HEIGHT * 2
        
        # Считаем сколько было до очистки
        islands_before = len(self.islands)
        
        # Очищаем старые острова
        self.islands = [i for i in self.islands if i.y < cleanup_threshold]
        
        # Очищаем старые берега
        self.left_shores = [s for s in self.left_shores if s.start_y < cleanup_threshold]
        self.right_shores = [s for s in self.right_shores if s.start_y < cleanup_threshold]
        
        if islands_before != len(self.islands):
            print(f"Очищено островов: {islands_before - len(self.islands)}, осталось: {len(self.islands)}")
    
    def draw(self):
        # Море
        self.screen.fill(WATER_BLUE)
        
        # Волны
        for i in range(-1, SCREEN_HEIGHT // 40 + 2):
            y = i * 40 + (int(self.camera_y / 3) % 40) + self.wave_offset % 40
            color = (10, 95, 170) if (i + self.wave_offset // 40) % 2 == 0 else (15, 100, 175)
            pygame.draw.line(self.screen, color, (0, y), (SCREEN_WIDTH, y), 2)
        
        # БЕРЕГА (рисуем первыми, чтобы были на заднем плане)
        for shore in self.left_shores:
            shore.draw(self.screen, self.camera_y)
        for shore in self.right_shores:
            shore.draw(self.screen, self.camera_y)
        
        # Острова
        for island in self.islands:
            island.draw(self.screen, self.camera_y)
        
        # Снаряды
        for proj in self.projectiles:
            proj.draw(self.screen, self.camera_y)
        
        # Игрок
        self.player.draw(self.screen, self.camera_y)
        
        # UI
        self.draw_ui()
        
        pygame.display.flip()
    
    def draw_ui(self):
        # Здоровье
        health_text = self.font.render(f"HP: {max(0, self.player.health)}/{self.player.max_health}", True, WHITE)
        self.screen.blit(health_text, (20, 20))
        
        bar_width = 250
        bar_height = 30
        health_ratio = max(0, self.player.health) / self.player.max_health
        
        pygame.draw.rect(self.screen, (100, 0, 0), (20, 60, bar_width, bar_height))
        pygame.draw.rect(self.screen, (0, 200, 0), 
                        (20, 60, int(bar_width * health_ratio), bar_height))
        pygame.draw.rect(self.screen, WHITE, (20, 60, bar_width, bar_height), 3)
        
        # Счёт
        score_text = self.font.render(f"Счёт: {self.player.score}", True, GOLD)
        self.screen.blit(score_text, (SCREEN_WIDTH - 250, 20))
        
        # УГОЛ ПОВОРОТА
        angle_text = self.big_font.render(f"Угол: {int(self.player.hull_angle)}°", True, CYAN)
        self.screen.blit(angle_text, (SCREEN_WIDTH // 2 - 100, 20))
        
        # Направление выстрела
        if abs(self.player.hull_angle) > 5:
            direction = "↖ ЗАЛП ВЛЕВО-ВВЕРХ" if self.player.hull_angle > 5 else "ЗАЛП ВПРАВО-ВВЕРХ ↗"
            dir_color = RED if self.player.shoot_cooldown == 0 else (100, 100, 100)
            dir_text = self.font.render(direction, True, dir_color)
            self.screen.blit(dir_text, (SCREEN_WIDTH // 2 - 200, 75))
        
        # Управление
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
            font = self.small_font
            control_text = font.render(text, True, color)
            self.screen.blit(control_text, 
                           (SCREEN_WIDTH - 440, SCREEN_HEIGHT - 145 + i * 28))
        
        # Статистика
        stats_text = self.small_font.render(
            f"Островов: {len(self.islands)} | Берегов: {len(self.left_shores) + len(self.right_shores)}", 
            True, (255, 200, 100))
        self.screen.blit(stats_text, (20, SCREEN_HEIGHT - 40))
    
    def run(self):
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
            
            if self.player.health <= 0:
                self.game_over()
                running = False
            
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()
    
    def game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(220)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        game_over_font = pygame.font.Font(None, 84)
        game_over_text = game_over_font.render("ИГРА ОКОНЧЕНА", True, RED)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
        
        score_text = self.big_font.render(f"Финальный счёт: {self.player.score}", True, GOLD)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        
        distance_text = self.font.render(f"Пройдено: {int(abs(self.player.y) / 10)} морских миль", 
                                        True, WHITE)
        distance_rect = distance_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
        
        self.screen.blit(game_over_text, game_over_rect)
        self.screen.blit(score_text, score_rect)
        self.screen.blit(distance_text, distance_rect)
        
        pygame.display.flip()
        pygame.time.wait(4000)

if __name__ == "__main__":
    game = Game()
    game.run()