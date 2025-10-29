# game.py - ГЛАВНЫЙ ФАЙЛ с умным спавном врагов
import pygame
import random
import math
import sys
from config import *
from player import Player
from island import Island
from shore import Shore
from whirlpool import WhirlpoolManager
from whirlpool import Whirlpool
from enemy_simple import SimpleEnemy
from enemy_hard import HardEnemy

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
        self.enemies = []
        self.left_shores = []
        self.right_shores = []
        
        # ВЕРХНЯЯ ГРАНИЦА МИРА
        self.world_top = self.player.y - SCREEN_HEIGHT * 2
        
        self.wave_offset = 0
        
        # Создаем менеджер водоворотов
        self.whirlpool_manager = WhirlpoolManager(max_whirlpools=6)
        self.teleport_effect_timer = 0
        
        # Счетчик миль
        self.total_distance = 0  # Общее расстояние в пикселях
        self.last_y = self.player.y  # Последняя позиция для подсчета
        
        # Пауза
        self.paused = False
        self.space_held = False
        self.space_hold_time = 0
        self.pause_threshold = 60  # 1 секунда удержания при 60 FPS
        
        # Начальная генерация мира
        self.generate_world_segment()
        self.generate_world_segment()
        self.generate_world_segment()
    
    def is_position_clear(self, x, y, radius=50):
        """Проверка, свободна ли позиция от островов и берегов"""
        # Проверка островов
        for island in self.islands[-50:]:  # Проверяем только недавние острова
            dx = island.x - x
            dy = island.y - y
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < island.radius + radius + 50:  # +50 для дополнительного запаса
                return False
        
        # Проверка берегов
        for shore in self.left_shores + self.right_shores:
            if shore.collides_with(x, y, radius):
                return False
        
        # Проверка, что не слишком близко к краям
        if x < 200 or x > SCREEN_WIDTH - 200:
            return False
        
        return True
        
    def generate_world_segment(self):
        """Генерация сегмента мира с умным спавном врагов"""
        segment_height = 2000
        segment_start = self.world_top - segment_height
        segment_end = self.world_top
        
        print(f"Генерация нового сегмента: {segment_start} -> {segment_end}")
        
        # БЕРЕГА ПО КРАЯМ
        self.left_shores.append(Shore('left', segment_start, segment_end))
        self.right_shores.append(Shore('right', segment_start, segment_end))
        
        current_y = segment_start
        islands_generated = 0
        whirlpools_generated = 0
        enemies_generated = 0
        
        # Генерируем острова СВЕРХУ ВНИЗ
        while current_y < segment_end:
            # КУЧА ОСТРОВОВ - 85% вероятность
            if random.random() < 0.85:
                x = random.randint(150, SCREEN_WIDTH - 150)
                
                # Проверка близости с недавними островами
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
            
            # Генерация водоворотов (10% вероятность)
            if random.random() < 0.1:
                x = random.randint(300, SCREEN_WIDTH - 300)
                if Whirlpool.can_place_whirlpool(x, current_y, self.islands, 
                                                self.left_shores + self.right_shores, 
                                                self.whirlpool_manager.whirlpools):
                    self.whirlpool_manager.add_whirlpool(x, current_y, self.islands, 
                                                       self.left_shores + self.right_shores)
                    whirlpools_generated += 1
            
            # Двигаемся ВНИЗ
            current_y += random.randint(60, 120)
        
        # ГЕНЕРАЦИЯ ВРАГОВ ОТДЕЛЬНО - после создания всех островов
        # Это гарантирует, что мы можем проверить коллизии
        current_y = segment_start
        while current_y < segment_end:
            # Враги генерируются ТОЛЬКО если далеко впереди игрока
            if current_y < self.player.y - 1500:
                
                # Генерация простых врагов (10% вероятность)
                if random.random() < 0.40:
                    # Пытаемся найти свободную позицию
                    for attempt in range(10):
                        x = random.randint(250, SCREEN_WIDTH - 250)
                        
                        if self.is_position_clear(x, current_y, 40):
                            self.enemies.append(SimpleEnemy(x, current_y))
                            enemies_generated += 1
                            break
                
                # Генерация сложных врагов (4% вероятность)
                if random.random() < 0.20:
                    for attempt in range(10):
                        x = random.randint(300, SCREEN_WIDTH - 300)
                        
                        if self.is_position_clear(x, current_y, 60):
                            self.enemies.append(HardEnemy(x, current_y))
                            enemies_generated += 1
                            break
            
            current_y += random.randint(100, 200)
        
        # Обновляем верхнюю границу мира
        self.world_top = segment_start
        print(f"Сгенерировано островов: {islands_generated}, всего: {len(self.islands)}")
        print(f"Сгенерировано водоворотов: {whirlpools_generated}")
        print(f"Сгенерировано врагов: {enemies_generated}, всего: {len(self.enemies)}")
        
    def update(self):
        keys = pygame.key.get_pressed()
        
        # Камера следует за игроком
        self.camera_y = self.player.y - SCREEN_HEIGHT + 200
        
        # Генерация нового мира когда игрок приближается к верхней границе
        if self.player.y < self.world_top + 1500:
            self.generate_world_segment()
        
        # Обновление водоворотов и проверка на телепортацию
        teleport_pos = self.whirlpool_manager.update(
            self.player, 
            self.world_top,
            self.islands,
            self.left_shores + self.right_shores
        )
        
        if teleport_pos:
            self.player.x, self.player.y = teleport_pos
            self.teleport_effect_timer = 30
        
        # Обновление врагов
        new_enemy_projectiles = []
        enemies_to_remove = []
        
        for enemy in self.enemies:
            # Обновляем врага и получаем его снаряды
            enemy_projectiles = enemy.update(
                self.islands, 
                self.left_shores + self.right_shores,
                self.player,
                self.world_top
            )
            
            # Если враг вышел за пределы мира
            if enemy_projectiles is None:
                enemies_to_remove.append(enemy)
                continue
                
            # Добавляем новые снаряды
            new_enemy_projectiles.extend(enemy_projectiles)
            
            # Проверка столкновения игрока с врагом (таран)
            if self.player.collides_with(enemy.x, enemy.y, enemy.radius):
                damage = enemy.get_torpedo_damage()
                self.player.take_damage(damage)
                # Простой враг уничтожается при таране
                if isinstance(enemy, SimpleEnemy):
                    enemies_to_remove.append(enemy)
        
        # Удаляем ненужных врагов
        for enemy in enemies_to_remove:
            self.enemies.remove(enemy)
        
        # Добавляем снаряды врагов
        self.projectiles.extend(new_enemy_projectiles)
        
        # Обновление игрока
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
        projectiles_to_remove = []
        for proj in self.projectiles[:]:
            proj.update()
            # Проверка столкновения снаряда с врагами
            for enemy in self.enemies[:]:
                if proj.collides_with(enemy):
                    if proj.is_player_shot:
                        if enemy.take_damage(1):
                            self.player.score += enemy.points
                            self.enemies.remove(enemy)
                        projectiles_to_remove.append(proj)
                        break
            
            # Проверка столкновения с препятствиями
            obstacle_hit = False
            for obstacle in all_obstacles:
                if proj.collides_with(obstacle):
                    obstacle_hit = True
                    break
            
            # Условия удаления снаряда
            if (proj.lifetime <= 0 or 
                proj.x < 0 or 
                proj.x > SCREEN_WIDTH or
                obstacle_hit or
                (not proj.is_player_shot and self.player.collides_with(proj.x, proj.y, 10))):
                
                if not proj.is_player_shot and self.player.collides_with(proj.x, proj.y, 10):
                    self.player.take_damage(20)
                projectiles_to_remove.append(proj)
        
        # Удаляем ненужные снаряды
        for proj in projectiles_to_remove:
            if proj in self.projectiles:
                self.projectiles.remove(proj)
        
        # Уменьшение таймера эффекта телепортации
        if self.teleport_effect_timer > 0:
            self.teleport_effect_timer -= 1
        
        # ОЧИСТКА СТАРЫХ ОБЪЕКТОВ
        cleanup_threshold = self.player.y + SCREEN_HEIGHT * 2
        
        islands_before = len(self.islands)
        
        self.islands = [i for i in self.islands if i.y < cleanup_threshold]
        self.left_shores = [s for s in self.left_shores if s.start_y < cleanup_threshold]
        self.right_shores = [s for s in self.right_shores if s.start_y < cleanup_threshold]
        
        self.whirlpool_manager.cleanup(cleanup_threshold)
        
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
        
        # БЕРЕГА
        for shore in self.left_shores:
            shore.draw(self.screen, self.camera_y)
        for shore in self.right_shores:
            shore.draw(self.screen, self.camera_y)
        
        # ВОДОВОРОТЫ
        self.whirlpool_manager.draw(self.screen, self.camera_y)
        
        # Острова
        for island in self.islands:
            island.draw(self.screen, self.camera_y)
        
        # ВРАГИ
        for enemy in self.enemies:
            enemy.draw(self.screen, self.camera_y)
        
        # Снаряды
        for proj in self.projectiles:
            proj.draw(self.screen, self.camera_y)
        
        # Игрок
        self.player.draw(self.screen, self.camera_y)
        
        # ЭФФЕКТ ТЕЛЕПОРТАЦИИ
        if self.teleport_effect_timer > 0:
            alpha = int((self.teleport_effect_timer / 30) * 200)
            flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            flash.set_alpha(alpha)
            flash.fill((255, 255, 255))
            self.screen.blit(flash, (0, 0))
        
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
        whirlpool_count = len(self.whirlpool_manager.whirlpools)
        enemy_count = len(self.enemies)
        stats_text = self.small_font.render(
            f"Островов: {len(self.islands)} | Врагов: {enemy_count} | Водоворотов: {whirlpool_count}", 
            True, (255, 200, 100))
        self.screen.blit(stats_text, (20, SCREEN_HEIGHT - 40))
        
        # Информация о водоворотах
        active_whirlpools = sum(1 for w in self.whirlpool_manager.whirlpools if not w.used_recently)
        if whirlpool_count > 0:
            whirlpool_info = self.small_font.render(
                f"🌀 Активных водоворотов: {active_whirlpools}/{whirlpool_count}", 
                True, CYAN)
            self.screen.blit(whirlpool_info, (20, SCREEN_HEIGHT - 70))
        
        # Информация о врагах
        simple_enemies = sum(1 for e in self.enemies if isinstance(e, SimpleEnemy))
        hard_enemies = sum(1 for e in self.enemies if isinstance(e, HardEnemy))
        if enemy_count > 0:
            enemy_info = self.small_font.render(
                f"⚔️ Враги: {simple_enemies} простых | {hard_enemies} серьезных", 
                True, (255, 100, 100))
            self.screen.blit(enemy_info, (20, SCREEN_HEIGHT - 100))
    
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