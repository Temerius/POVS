# main.py - Основной файл игры "Бескрайнее море"

import pygame
import random
import math
import sys
from config import *
from uart_protocol import UARTProtocol
from game_objects import Island, Shore
from renderer import GameRenderer


class Game:
    """Главный класс игры"""
    
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Бескрайнее море — STM32 Edition")
        self.clock = pygame.time.Clock()
        
        # UART протокол
        self.uart = UARTProtocol(UART_PORT, UART_BAUDRATE, debug=True)
        
        # Рендерер
        self.renderer = GameRenderer(self.screen)
        
        # Визуальные объекты (генерируются локально)
        self.islands = []
        self.left_shores = []
        self.right_shores = []
        
        # Состояние из STM32
        self.game_state = None
        
        # Мир
        self.world_top = -SCREEN_HEIGHT * 2
        
        # Инициализация игры на STM32
        self.uart.send_init_game()
        
        # Генерация начального мира
        for _ in range(WORLD_INITIAL_SEGMENTS):
            self._generate_world_segment()
    
    def _is_position_clear(self, x, y, radius=50):
        """Проверка что позиция свободна"""
        for island in self.islands[-50:]:
            dist = math.sqrt((island.x - x)**2 + (island.y - y)**2)
            if dist < island.radius + radius + 50:
                return False
        
        if x < SHORE_EDGE_MARGIN or x > SCREEN_WIDTH - SHORE_EDGE_MARGIN:
            return False
        
        return True
    
    def _generate_world_segment(self):
        """Генерация сегмента мира (берега и острова)"""
        segment_start = self.world_top - WORLD_SEGMENT_HEIGHT
        segment_end = self.world_top
        
        print(f"Генерация сегмента: {segment_start} -> {segment_end}")
        
        # Берега - создаём локально и отправляем на STM32
        left_shore = Shore('left', segment_start, segment_end)
        right_shore = Shore('right', segment_start, segment_end)
        
        self.left_shores.append(left_shore)
        self.right_shores.append(right_shore)
        
        # Отправка берегов на STM32
        self.uart.send_add_shore('left', segment_start, segment_end)
        self.uart.send_add_shore('right', segment_start, segment_end)
        
        # Генерация островов
        current_y = segment_start
        while current_y < segment_end:
            if random.random() < WORLD_ISLAND_SPAWN_CHANCE:
                x = random.randint(SHORE_WIDTH, SCREEN_WIDTH - SHORE_WIDTH)
                
                if self._is_position_clear(x, current_y):
                    seed = random.randint(0, 1000000)
                    island = Island(x, current_y, seed)
                    self.islands.append(island)
                    
                    # Отправка острова на STM32
                    self.uart.send_add_obstacle(0, x, current_y, island.radius)
            
            current_y += random.randint(60, 120)
        
        self.world_top = segment_start
    
    def _cleanup_old_objects(self):
        """Очистка старых островов и берегов"""
        if not self.game_state:
            return
        
        cleanup_threshold = self.game_state.player_y + WORLD_CLEANUP_DISTANCE
        
        islands_before = len(self.islands)
        
        self.islands = [i for i in self.islands if i.y < cleanup_threshold]
        self.left_shores = [s for s in self.left_shores if s.start_y < cleanup_threshold]
        self.right_shores = [s for s in self.right_shores if s.start_y < cleanup_threshold]
        
        if islands_before != len(self.islands):
            print(f"Очищено островов: {islands_before - len(self.islands)}, осталось: {len(self.islands)}")
    
    def update(self):
        """Обновление игры"""
        # Получение состояния от STM32
        new_state = self.uart.receive_game_state()
        if new_state:
            self.game_state = new_state
        
        if not self.game_state:
            return
        
        # Проверка окончания игры
        if self.game_state.player_health <= 0:
            self._game_over()
            return
        
        # Генерация нового мира
        if self.game_state.player_y < self.world_top + WORLD_GENERATION_AHEAD:
            self._generate_world_segment()
        
        # Очистка старых островов и берегов
        self._cleanup_old_objects()
    
    def _game_over(self):
        """Экран окончания игры"""
        self.renderer.draw_game_over(self.game_state)
        pygame.display.flip()
        
        # Ожидание нажатия R
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        waiting = False
                        self._restart_game()
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
            
            self.clock.tick(30)
    
    def _restart_game(self):
        """Перезапуск игры"""
        # Очистка текущего состояния
        self.islands = []
        self.left_shores = []
        self.right_shores = []
        self.world_top = -SCREEN_HEIGHT * 2
        
        # Перезапуск игры на STM32
        self.uart.send_init_game()
        
        # Генерация начального мира
        for _ in range(WORLD_INITIAL_SEGMENTS):
            self._generate_world_segment()
        
        # Сброс состояния
        self.game_state = None
    
    def draw(self):
        """Отрисовка"""
        if not self.game_state:
            self.renderer.draw_waiting_screen()
            pygame.display.flip()
            return
        
        # Море
        self.screen.fill(WATER_BLUE)
        
        # Волны
        self.renderer.draw_waves()
        
        camera_y = self.game_state.camera_y
        
        # Берега (локальные)
        for shore in self.left_shores:
            shore.draw(self.screen, camera_y)
        for shore in self.right_shores:
            shore.draw(self.screen, camera_y)
        
        # Острова (локальные)
        for island in self.islands:
            island.draw(self.screen, camera_y)
        
        # Водовороты (из STM32)
        self.renderer.draw_whirlpools(self.game_state.whirlpools, camera_y)
        
        # Враги (из STM32)
        self.renderer.draw_enemies(self.game_state.enemies, camera_y)
        
        # Снаряды (из STM32)
        self.renderer.draw_projectiles(self.game_state.projectiles, camera_y)
        
        # Игрок
        self.renderer.draw_player(
            self.game_state.player_x,
            self.game_state.player_y,
            self.game_state.player_angle,
            camera_y
        )
        
        # UI
        self.renderer.draw_ui(self.game_state, len(self.islands))
        
        benchmark_stats = self.uart.get_benchmark_stats()
        if benchmark_stats:
            self.renderer.draw_benchmark(self.screen, benchmark_stats)
        pygame.display.flip()
    
    def handle_events(self):
        """Обработка событий"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_r and self.game_state and self.game_state.player_health <= 0:
                    self._restart_game()
        
        return True
    
    def run(self):
        """Запуск игры"""
        running = True
        
        while running:
            # Обработка debug-пакетов (если нужно)
            # debug_info = self.uart.receive_debug_packet()
            # if debug_info:
            #     self.uart.print_debug_packet(debug_info)
            
            # Обработка событий
            running = self.handle_events()
            
            # Обновление игры
            self.update()
            
            # Отрисовка
            self.draw()
            
            # Ограничение FPS
            self.clock.tick(FPS)
        
        # Завершение работы
        pygame.quit()
        if self.uart.ser:
            self.uart.ser.close()
        sys.exit()


# ============ ЗАПУСК ИГРЫ ============

if __name__ == "__main__":
    try:
        game = Game()
        game.run()
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        pygame.quit()
        sys.exit(1)