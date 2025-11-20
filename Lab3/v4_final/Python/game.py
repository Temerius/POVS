
import pygame
import random
import math
import sys
from config import *
from player import Player
from island import Island, Shore
from whirlpool import WhirlpoolManager, Whirlpool
from enemy_simple import SimpleEnemy
from enemy_hard import HardEnemy
from uart_protocol import UARTProtocol 

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Мейфлауэр")
        self.clock = pygame.time.Clock()
        
        self.uart = UARTProtocol(debug=True)  
        self.last_miles_sent = 0  
        
        self._init_fonts()
        self._init_game_objects()
        self._generate_initial_world()
    
    def _init_fonts(self):
        """Инициализация шрифтов"""
        self.font = pygame.font.Font(None, UI_FONT_SIZE)
        self.small_font = pygame.font.Font(None, UI_SMALL_FONT_SIZE)
        self.big_font = pygame.font.Font(None, UI_BIG_FONT_SIZE)
    
    def _init_game_objects(self):
        """Инициализация игровых объектов"""
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150)
        self.camera_y = self.player.y - SCREEN_HEIGHT + CAMERA_OFFSET
        
        self.islands = []
        self.projectiles = []
        self.enemies = []
        self.left_shores = []
        self.right_shores = []
        
        self.world_top = self.player.y - SCREEN_HEIGHT * 2
        self.wave_offset = 0
        
        self.whirlpool_manager = WhirlpoolManager(max_whirlpools=WHIRLPOOL_MAX_COUNT)
        self.teleport_effect_timer = 0
    
    def _generate_initial_world(self):
        """Генерация начального мира"""
        for _ in range(WORLD_INITIAL_SEGMENTS):
            self._generate_world_segment()
    
    def _is_position_clear(self, x, y, radius=SPAWN_CLEARANCE_RADIUS):
        """Проверка свободности позиции"""
        for island in self.islands[-50:]:
            dx = island.x - x
            dy = island.y - y
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < island.radius + radius + ENEMY_CLEARANCE_EXTRA:
                return False
        
        for shore in self.left_shores + self.right_shores:
            if shore.collides_with(x, y, radius):
                return False
        
        if x < SHORE_EDGE_MARGIN or x > SCREEN_WIDTH - SHORE_EDGE_MARGIN:
            return False
        
        return True
    
    def _generate_world_segment(self):
        """Генерация сегмента мира"""
        segment_start = self.world_top - WORLD_SEGMENT_HEIGHT
        segment_end = self.world_top
        
        print(f"Генерация нового сегмента: {segment_start} -> {segment_end}")
        
        
        self.left_shores.append(Shore('left', segment_start, segment_end))
        self.right_shores.append(Shore('right', segment_start, segment_end))
        
        current_y = segment_start
        islands_generated = 0
        whirlpools_generated = 0
        enemies_generated = 0
        
        while current_y < segment_end:
            if random.random() < WORLD_ISLAND_SPAWN_CHANCE:
                x = random.randint(SHORE_WIDTH, SCREEN_WIDTH - SHORE_WIDTH)
                
                too_close = False
                for island in self.islands[-WORLD_ISLAND_RECENT_CHECK:]:
                    dist = math.sqrt((island.x - x)**2 + (island.y - current_y)**2)
                    if dist < WORLD_ISLAND_MIN_SPACING:
                        too_close = True
                        break
                
                if not too_close:
                    island = Island(x, current_y, random.randint(0, 1000000))
                    self.islands.append(island)
                    islands_generated += 1
            
            if random.random() < WHIRLPOOL_SPAWN_CHANCE:
                x = random.randint(WHIRLPOOL_EDGE_MARGIN, SCREEN_WIDTH - WHIRLPOOL_EDGE_MARGIN)
                if Whirlpool.can_place_whirlpool(x, current_y, self.islands, 
                                                self.left_shores + self.right_shores, 
                                                self.whirlpool_manager.whirlpools):
                    self.whirlpool_manager.add_whirlpool(x, current_y, self.islands, 
                                                       self.left_shores + self.right_shores)
                    whirlpools_generated += 1
            
            current_y += random.randint(WORLD_ISLAND_STEP_MIN, WORLD_ISLAND_STEP_MAX)
        
        current_y = segment_start
        while current_y < segment_end:
            if current_y < self.player.y + WORLD_ENEMY_SPAWN_DISTANCE:
                if random.random() < ENEMY_SIMPLE_SPAWN_CHANCE:
                    for _ in range(10):
                        x = random.randint(250, SCREEN_WIDTH - 250)
                        
                        if self._is_position_clear(x, current_y, COLLISION_RADIUS_ENEMY_SIMPLE):
                            self.enemies.append(SimpleEnemy(x, current_y))
                            enemies_generated += 1
                            break
                
                if random.random() < ENEMY_HARD_SPAWN_CHANCE:
                    for _ in range(10):
                        x = random.randint(300, SCREEN_WIDTH - 300)
                        
                        if self._is_position_clear(x, current_y, COLLISION_RADIUS_ENEMY_HARD):
                            self.enemies.append(HardEnemy(x, current_y))
                            enemies_generated += 1
                            break
            
            current_y += random.randint(WORLD_ENEMY_STEP_MIN, WORLD_ENEMY_STEP_MAX)
        
        self.world_top = segment_start
        print(f"Сгенерировано островов: {islands_generated}, всего: {len(self.islands)}")
        print(f"Сгенерировано водоворотов: {whirlpools_generated}")
        print(f"Сгенерировано врагов: {enemies_generated}, всего: {len(self.enemies)}")
    
    def update(self):
        """Главное обновление игры"""
        if not self.uart.is_connected():
            print("Потеря связи с платой!")
            self.player.health = 0  
            return
        
        if self.uart.check_reset():
            print("RESET платы - перезапуск игры!")
            self._restart_game()
            return
        

        button_state = self.uart.receive_buttons()
        keys = button_state.to_pygame_keys()
        

        self.camera_y = self.player.y - SCREEN_HEIGHT + CAMERA_OFFSET
        
 
        if self.player.y > 0:
            current_miles = 0
        else:
            current_miles = int(abs(self.player.y) / PIXELS_PER_MILE)
        if current_miles != self.last_miles_sent:
            # print(current_miles)
            self.uart.send_miles(current_miles)
            self.last_miles_sent = current_miles
        

        if self.player.y < self.world_top + WORLD_GENERATION_AHEAD:
            self._generate_world_segment()
        

        teleport_pos = self.whirlpool_manager.update(
            self.player, 
            self.world_top,
            self.islands,
            self.left_shores + self.right_shores
        )
        
        if teleport_pos:
            self.player.x, self.player.y = teleport_pos
            self.teleport_effect_timer = TELEPORT_EFFECT_DURATION
        
 
        self._update_enemies()
        

        all_obstacles = self.islands + self.left_shores + self.right_shores
        self.player.update(keys, all_obstacles)
        

        if keys[pygame.K_SPACE]:
            new_projectiles = self.player.shoot()
            if new_projectiles:
                self.projectiles.extend(new_projectiles)
        

        self.wave_offset = (self.wave_offset + WAVE_SPEED) % WAVE_HEIGHT
        
        self._update_projectiles(all_obstacles)
        
        if self.teleport_effect_timer > 0:
            self.teleport_effect_timer -= 1
        
        self._cleanup_old_objects()
    
    def _update_enemies(self):
        """Обновление всех врагов"""
        new_enemy_projectiles = []
        enemies_to_remove = []
        
        for enemy in self.enemies:
            enemy_projectiles = enemy.update(
                self.islands, 
                self.left_shores + self.right_shores,
                self.player,
                self.world_top
            )
            
            if enemy_projectiles is None:
                enemies_to_remove.append(enemy)
                continue
            
            new_enemy_projectiles.extend(enemy_projectiles)
            
            # Таран
            if self.player.collides_with(enemy.x, enemy.y, enemy.radius):
                damage = enemy.get_torpedo_damage()
                self.player.take_damage(damage)
                if isinstance(enemy, SimpleEnemy):
                    enemies_to_remove.append(enemy)
        
        for enemy in enemies_to_remove:
            self.enemies.remove(enemy)
        
        self.projectiles.extend(new_enemy_projectiles)
    
    def _update_projectiles(self, all_obstacles):
        """Обновление всех снарядов"""
        projectiles_to_remove = []
        
        for proj in self.projectiles[:]:
            proj.update()
            
            for enemy in self.enemies[:]:
                if proj.collides_with(enemy):
                    if proj.is_player_shot:
                        if enemy.take_damage(1):
                            self.player.score += enemy.points
                            self.enemies.remove(enemy)
                        projectiles_to_remove.append(proj)
                        break
            
            obstacle_hit = any(proj.collides_with(obstacle) for obstacle in all_obstacles)
            
            player_hit = not proj.is_player_shot and self.player.collides_with(proj.x, proj.y, PROJECTILE_RADIUS)
            if player_hit:
                self.player.take_damage(PROJECTILE_DAMAGE_TO_PLAYER)
            
            if (proj.lifetime <= 0 or 
                proj.x < 0 or 
                proj.x > SCREEN_WIDTH or
                obstacle_hit or
                player_hit):
                projectiles_to_remove.append(proj)
        
        for proj in projectiles_to_remove:
            if proj in self.projectiles:
                self.projectiles.remove(proj)
    
    def _cleanup_old_objects(self):
        """Очистка старых объектов"""
        cleanup_threshold = self.player.y + WORLD_CLEANUP_DISTANCE
        
        islands_before = len(self.islands)
        
        self.islands = [i for i in self.islands if i.y < cleanup_threshold]
        self.left_shores = [s for s in self.left_shores if s.start_y < cleanup_threshold]
        self.right_shores = [s for s in self.right_shores if s.start_y < cleanup_threshold]
        
        self.whirlpool_manager.cleanup(cleanup_threshold)
        
        if islands_before != len(self.islands):
            print(f"Очищено островов: {islands_before - len(self.islands)}, осталось: {len(self.islands)}")
    
    def draw(self):
        """Отрисовка всей игры"""
        
        self.screen.fill(WATER_BLUE)
        
        
        self._draw_waves()
        
        
        for shore in self.left_shores:
            shore.draw(self.screen, self.camera_y)
        for shore in self.right_shores:
            shore.draw(self.screen, self.camera_y)
        
        self.whirlpool_manager.draw(self.screen, self.camera_y)
        
        for island in self.islands:
            island.draw(self.screen, self.camera_y)
        
        for enemy in self.enemies:
            enemy.draw(self.screen, self.camera_y)
        
        for proj in self.projectiles:
            proj.draw(self.screen, self.camera_y)
        
        self.player.draw(self.screen, self.camera_y)
        
        
        if self.teleport_effect_timer > 0:
            alpha = int((self.teleport_effect_timer / TELEPORT_EFFECT_DURATION) * 200)
            flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            flash.set_alpha(alpha)
            flash.fill(WHITE)
            self.screen.blit(flash, (0, 0))
        
        
        self._draw_ui()
        
        pygame.display.flip()
    
    def _draw_waves(self):
        """Отрисовка реалистичных волн с синусоидальными колебаниями"""
        AMPLITUDE = 12
        WAVE_LENGTH = 80
        WAVE_SPEED = 0.03
        VERTICAL_SPACING = 35
        
        base_offset = (self.camera_y // 3) % VERTICAL_SPACING + (self.wave_offset % VERTICAL_SPACING)
        
        for layer in range(-2, SCREEN_HEIGHT // VERTICAL_SPACING + 3):
            base_y = layer * VERTICAL_SPACING + base_offset
            
            depth_factor = (layer % 3) * 5
            color = (
                10 + depth_factor, 
                95 + depth_factor, 
                170 + min(depth_factor, 10)
            )
            
            phase_shift = layer * 0.8
            points = []
            
            for x in range(0, SCREEN_WIDTH + WAVE_LENGTH, 5):
                y = base_y + AMPLITUDE * math.sin(
                    (2 * math.pi * x / WAVE_LENGTH) + 
                    (self.wave_offset * WAVE_SPEED) + 
                    phase_shift
                )
                
                y += AMPLITUDE * 0.3 * math.sin(
                    (4 * math.pi * x / WAVE_LENGTH) + 
                    (self.wave_offset * WAVE_SPEED * 1.5) + 
                    phase_shift * 1.2
                )
                
                points.append((x, y))
            
            if len(points) > 1:
                pygame.draw.lines(self.screen, color, False, points, 2)
    
    def _draw_ui(self):
        """Отрисовка UI"""
        health_text = self.font.render(f"HP: {max(0, self.player.health)}/{self.player.max_health}", True, WHITE)
        self.screen.blit(health_text, (UI_PADDING, UI_PADDING))
        
        health_ratio = max(0, self.player.health) / self.player.max_health
        
        pygame.draw.rect(self.screen, (100, 0, 0), (UI_PADDING, 60, UI_HEALTH_BAR_WIDTH, UI_HEALTH_BAR_HEIGHT))
        pygame.draw.rect(self.screen, (0, 200, 0), 
                        (UI_PADDING, 60, int(UI_HEALTH_BAR_WIDTH * health_ratio), UI_HEALTH_BAR_HEIGHT))
        pygame.draw.rect(self.screen, WHITE, (UI_PADDING, 60, UI_HEALTH_BAR_WIDTH, UI_HEALTH_BAR_HEIGHT), 3)
        
        score_text = self.font.render(f"Счёт: {self.player.score}", True, GOLD)
        self.screen.blit(score_text, (SCREEN_WIDTH - 250, UI_PADDING))

        if self.player.y > 0:
            miles = 0
        else:
            miles = int(abs(self.player.y) / PIXELS_PER_MILE)
        miles_text = self.font.render(f"Мили: {miles}", True, WHITE)
        self.screen.blit(miles_text, (SCREEN_WIDTH - 250, 60))
        
        angle_text = self.big_font.render(f"Угол: {int(self.player.hull_angle)}°", True, CYAN)
        self.screen.blit(angle_text, (SCREEN_WIDTH // 2 - 100, UI_PADDING))
        
        if abs(self.player.hull_angle) > PLAYER_MIN_ANGLE_FOR_SIDE_SHOT:
            direction = "↖ ЗАЛП ВЛЕВО-ВВЕРХ" if self.player.hull_angle > PLAYER_MIN_ANGLE_FOR_SIDE_SHOT else "ЗАЛП ВПРАВО-ВВЕРХ ↗"
            dir_color = RED if self.player.shoot_cooldown == 0 else (100, 100, 100)
            dir_text = self.font.render(direction, True, dir_color)
            self.screen.blit(dir_text, (SCREEN_WIDTH // 2 - 200, 75))
        
        self._draw_controls()
        
        self._draw_stats()
    
    def _draw_controls(self):
        """Отрисовка подсказок управления"""
        controls = [
            "Управление: кнопки на STM32",
            "CANON_LEFT - Лево (плывёшь влево)",
            "CANON_RIGHT - Право (плывёшь вправо)",
            "CANON_FIRE - Залп",
            "ESC - Выход"
        ]
        
        pygame.draw.rect(self.screen, (0, 0, 0, 180), 
                        (SCREEN_WIDTH - 500, SCREEN_HEIGHT - 160, 490, UI_CONTROLS_HEIGHT))
        pygame.draw.rect(self.screen, WHITE, 
                        (SCREEN_WIDTH - 500, SCREEN_HEIGHT - 160, 490, UI_CONTROLS_HEIGHT), 2)
        
        for i, text in enumerate(controls):
            color = GOLD if i == 0 else WHITE
            control_text = self.small_font.render(text, True, color)
            self.screen.blit(control_text, (SCREEN_WIDTH - 490, SCREEN_HEIGHT - 145 + i * 28))
    
    def _draw_stats(self):
        """Отрисовка статистики"""
        whirlpool_count = len(self.whirlpool_manager.whirlpools)
        enemy_count = len(self.enemies)
        
        stats_text = self.small_font.render(
            f"Островов: {len(self.islands)} | Врагов: {enemy_count} | Водоворотов: {whirlpool_count}", 
            True, (255, 200, 100))
        self.screen.blit(stats_text, (UI_PADDING, SCREEN_HEIGHT - 40))
        
        active_whirlpools = sum(1 for w in self.whirlpool_manager.whirlpools if not w.used_recently)
        if whirlpool_count > 0:
            whirlpool_info = self.small_font.render(
                f"🌀 Активных водоворотов: {active_whirlpools}/{whirlpool_count}", 
                True, CYAN)
            self.screen.blit(whirlpool_info, (UI_PADDING, SCREEN_HEIGHT - 70))
        
        simple_enemies = sum(1 for e in self.enemies if isinstance(e, SimpleEnemy))
        hard_enemies = sum(1 for e in self.enemies if isinstance(e, HardEnemy))
        if enemy_count > 0:
            enemy_info = self.small_font.render(
                f"⚔️ Враги: {simple_enemies} простых | {hard_enemies} серьезных", 
                True, (255, 100, 100))
            self.screen.blit(enemy_info, (UI_PADDING, SCREEN_HEIGHT - 100))
    
    def run(self):
        """Главный цикл игры"""
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
            
            if self.player.health <= 0:
                self._game_over()
                running = False
            
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        self.uart.print_statistics()
        
        pygame.quit()
        sys.exit()
    
    def _game_over(self):
        """Экран окончания игры"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(220)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        game_over_font = pygame.font.Font(None, 84)
        game_over_text = game_over_font.render("ИГРА ОКОНЧЕНА", True, RED)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
        
        score_text = self.big_font.render(f"Финальный счёт: {self.player.score}", True, GOLD)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        
        distance_text = self.font.render(f"Пройдено: {int(abs(self.player.y) / PIXELS_PER_MILE)} морских миль", 
                                        True, WHITE)
        distance_rect = distance_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
        
        self.screen.blit(game_over_text, game_over_rect)
        self.screen.blit(score_text, score_rect)
        self.screen.blit(distance_text, distance_rect)
        
        pygame.display.flip()
        pygame.time.wait(UI_GAME_OVER_WAIT)


if __name__ == "__main__":
    game = Game()
    game.run()