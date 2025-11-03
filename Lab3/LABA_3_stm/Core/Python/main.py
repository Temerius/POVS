# game_integrated.py - Endless Sea с интеграцией STM32 через UART

import pygame
import serial
import struct
import math
import random
import sys
from dataclasses import dataclass
from typing import List, Tuple, Optional

# ============ КОНФИГУРАЦИЯ ============

# UART
UART_PORT = 'COM5'
UART_BAUDRATE = 115200
UART_TIMEOUT = 0.001

# Параметры экрана
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# Цвета
WATER_BLUE = (20, 105, 180)
ISLAND_GREEN = (34, 139, 34)
DARK_GREEN = (25, 100, 25)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 20, 20)
GOLD = (255, 215, 0)
CYAN = (0, 255, 255)

# Игровые параметры
PLAYER_SIZE = 50
PLAYER_MAX_HEALTH = 100
ENEMY_SIMPLE_SIZE = 40
ENEMY_HARD_SIZE = 60
PROJECTILE_RADIUS = 5
PROJECTILE_COLOR_PLAYER = (255, 255, 0)
PROJECTILE_COLOR_ENEMY = (255, 50, 50)
WHIRLPOOL_RADIUS = 45

MAX_ENEMIES_IN_PACKET = 6
MAX_PROJECTILES_IN_PACKET = 10
MAX_WHIRLPOOLS_IN_PACKET = 3

# Генерация мира
WORLD_SEGMENT_HEIGHT = 2000
WORLD_GENERATION_AHEAD = 1500
WORLD_INITIAL_SEGMENTS = 3
WORLD_CLEANUP_DISTANCE = 2000
WORLD_ISLAND_SPAWN_CHANCE = 0.85
WORLD_ENEMY_SPAWN_DISTANCE = -1500
ENEMY_SIMPLE_SPAWN_CHANCE = 0.25
ENEMY_HARD_SPAWN_CHANCE = 0.10
WHIRLPOOL_SPAWN_CHANCE = 0.1
WHIRLPOOL_MAX_COUNT = 6

# Острова
ISLAND_MIN_RADIUS = 50
ISLAND_MAX_RADIUS = 120
ISLAND_SHAPE_POINTS = 20
SHORE_WIDTH = 150
SHORE_EDGE_MARGIN = 200

# Камера и UI
CAMERA_OFFSET = 200
UI_PADDING = 20
UI_HEALTH_BAR_WIDTH = 250
UI_HEALTH_BAR_HEIGHT = 30

# Типы пакетов
PKT_GAME_STATE = 0x01
PKT_ADD_ENEMY = 0x02
PKT_ADD_OBSTACLE = 0x03
PKT_CLEANUP = 0x04
PKT_INIT_GAME = 0x05
PKT_ADD_WHIRLPOOL = 0x06


START_BYTE = 0xAA
END_BYTE = 0x55

# ============ СТРУКТУРЫ ДАННЫХ ============

@dataclass
class GameStateFromSTM32:
    player_x: float
    player_y: float
    player_angle: float
    player_health: int
    player_score: int
    player_shoot_cooldown: int  # Добавлено
    enemies: List[dict]  # {'type', 'x', 'y', 'health'}
    projectiles: List[dict]  # {'x', 'y', 'is_player_shot'}
    whirlpools: List[dict]  # {'x', 'y', 'used'}
    camera_y: float
    frame_counter: int  # Добавлено для синхронизации

# ============ ВИЗУАЛЬНЫЕ ОБЪЕКТЫ ============

class Island:
    def __init__(self, x, y, seed):
        self.x = x
        self.y = y
        random.seed(seed)
        self.radius = random.randint(ISLAND_MIN_RADIUS, ISLAND_MAX_RADIUS)
        self.color = (
            max(20, min(80, ISLAND_GREEN[0] + random.randint(-15, 15))),
            max(80, min(160, ISLAND_GREEN[1] + random.randint(-20, 20))),
            max(10, min(60, ISLAND_GREEN[2] + random.randint(-10, 10)))
        )
        self.points = self._generate_shape()
    
    def _generate_shape(self):
        points = []
        for i in range(ISLAND_SHAPE_POINTS):
            angle = (i / ISLAND_SHAPE_POINTS) * 2 * math.pi
            noise = random.uniform(0.85, 1.15)
            r = self.radius * noise
            x = self.x + math.cos(angle) * r
            y = self.y + math.sin(angle) * r
            points.append((x, y))
        return points
    
    def draw(self, screen, camera_y):
        adjusted_points = [(int(p[0]), int(p[1] - camera_y)) for p in self.points]
        min_y = min(p[1] for p in adjusted_points)
        max_y = max(p[1] for p in adjusted_points)
        
        if max_y < -200 or min_y > SCREEN_HEIGHT + 200:
            return
        
        pygame.draw.polygon(screen, self.color, adjusted_points)
        pygame.draw.polygon(screen, DARK_GREEN, adjusted_points, 3)

class Shore:
    def __init__(self, side, start_y, end_y):
        self.side = side
        self.start_y = start_y
        self.end_y = end_y
        self.points = self._generate_shore()
    
    def _generate_shore(self):
        points = []
        current_y = self.start_y
        
        if self.side == 'left':
            points.append((0, current_y))
            while current_y < self.end_y:
                indent = random.randint(40, 100)
                segment_height = random.randint(80, 150)
                points.append((indent, current_y))
                current_y += segment_height / 2
                points.append((indent + random.randint(-20, 20), current_y))
                current_y += segment_height / 2
            points.append((0, self.end_y))
        else:
            points.append((SCREEN_WIDTH, current_y))
            while current_y < self.end_y:
                indent = random.randint(40, 100)
                segment_height = random.randint(80, 150)
                points.append((SCREEN_WIDTH - indent, current_y))
                current_y += segment_height / 2
                points.append((SCREEN_WIDTH - indent + random.randint(-20, 20), current_y))
                current_y += segment_height / 2
            points.append((SCREEN_WIDTH, self.end_y))
        
        return points
    
    def draw(self, screen, camera_y):
        adjusted_points = [(int(p[0]), int(p[1] - camera_y)) for p in self.points]
        visible = any(-100 < p[1] < SCREEN_HEIGHT + 100 for p in adjusted_points)
        
        if not visible:
            return
        
        if self.side == 'left':
            polygon_points = [(0, -200)] + adjusted_points + [(0, SCREEN_HEIGHT + 200)]
        else:
            polygon_points = [(SCREEN_WIDTH, -200)] + adjusted_points + [(SCREEN_WIDTH, SCREEN_HEIGHT + 200)]
        
        pygame.draw.polygon(screen, ISLAND_GREEN, polygon_points)
        pygame.draw.lines(screen, DARK_GREEN, False, adjusted_points, 4)

# ============ UART ПРОТОКОЛ ============

# ============ UART ПРОТОКОЛ С ДЕТАЛЬНЫМ ЛОГИРОВАНИЕМ ============


# game_integrated.py

# game_integrated.py

class UARTProtocol:
    def __init__(self, port, baudrate, debug=False):
        self.debug = debug
        self.packet_buffer = b''
        self.sent_packets = 0
        self.received_packets = 0
        self.error_packets = 0
        self.last_packet_time = 0
        
        try:
            self.ser = serial.Serial(port, baudrate, timeout=UART_TIMEOUT)
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            print(f"✓ UART подключен: {port} @ {baudrate}")
        except Exception as e:
            print(f"✗ Ошибка подключения UART: {e}")
            self.ser = None
    
    def calculate_crc(self, data):
        """Вычисление CRC8"""
        crc = 0
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x07
                else:
                    crc <<= 1
                crc &= 0xFF
        return crc
    
    def _log_packet(self, direction, packet_type, details=""):
        """Вспомогательная функция для логирования пакетов"""
        packet_name = self._get_packet_name(packet_type)
        timestamp = pygame.time.get_ticks()
        delta = timestamp - self.last_packet_time if self.last_packet_time else 0
        self.last_packet_time = timestamp
        
        log_type = "SENT" if direction == "out" else "RECV"
        print(f"[{log_type}] #{self.received_packets + self.sent_packets} [{timestamp}ms (+{delta}ms)] "
              f"PKT_{packet_name} {details}")
    
    def _get_packet_name(self, packet_type):
        """Возвращает имя пакета по его типу"""
        names = {
            PKT_GAME_STATE: "GAME_STATE",
            PKT_ADD_ENEMY: "ADD_ENEMY",
            PKT_ADD_OBSTACLE: "ADD_OBSTACLE",
            PKT_CLEANUP: "CLEANUP",
            PKT_INIT_GAME: "INIT_GAME",
            PKT_ADD_WHIRLPOOL: "ADD_WHIRLPOOL"
        }
        return names.get(packet_type, f"UNKNOWN_{packet_type:02X}")
    
    def send_add_enemy(self, enemy_type, x, y):
        if not self.ser:
            return
        
        # Формируем пакет
        packet = struct.pack('<BBff', PKT_ADD_ENEMY, enemy_type, x, y)
        crc = self.calculate_crc(packet)
        full_packet = struct.pack('<B', START_BYTE) + packet + struct.pack('<B', crc) + struct.pack('<B', END_BYTE)
        
        try:
            self.ser.write(full_packet)
            self.sent_packets += 1
            
            if self.debug:
                enemy_name = "SIMPLE" if enemy_type == 0 else "HARD"
                self._log_packet("out", PKT_ADD_ENEMY, 
                                f"(type={enemy_name}, x={x:.1f}, y={y:.1f})")
        except Exception as e:
            self.error_packets += 1
            print(f"✗ Ошибка отправки врага: {e}")
    
    def send_add_obstacle(self, obstacle_type, x, y, radius):
        if not self.ser:
            return
        
        # Формируем пакет
        packet = struct.pack('<BBfff', PKT_ADD_OBSTACLE, obstacle_type, x, y, radius)
        crc = self.calculate_crc(packet)
        full_packet = struct.pack('<B', START_BYTE) + packet + struct.pack('<BB', crc, END_BYTE)
        
        try:
            self.ser.write(full_packet)
            self.sent_packets += 1
            
            if self.debug:
                obstacle_names = {0: "ISLAND", 1: "SHORE_LEFT", 2: "SHORE_RIGHT"}
                name = obstacle_names.get(obstacle_type, f"UNKNOWN_{obstacle_type}")
                self._log_packet("out", PKT_ADD_OBSTACLE, 
                                f"(type={name}, x={x:.1f}, y={y:.1f}, radius={radius:.1f})")
        except Exception as e:
            self.error_packets += 1
            print(f"✗ Ошибка отправки препятствия: {e}")
    
    def send_add_whirlpool(self, x, y):
        if not self.ser:
            return
        
        # Формируем пакет
        packet = struct.pack('<Bff', PKT_ADD_WHIRLPOOL, x, y)
        crc = self.calculate_crc(packet)
        full_packet = struct.pack('<B', START_BYTE) + packet + struct.pack('<BB', crc, END_BYTE)
        
        try:
            self.ser.write(full_packet)
            self.sent_packets += 1
            
            if self.debug:
                self._log_packet("out", PKT_ADD_WHIRLPOOL, 
                                f"(x={x:.1f}, y={y:.1f})")
        except Exception as e:
            self.error_packets += 1
            print(f"✗ Ошибка отправки водоворота: {e}")
    
    def send_cleanup(self, threshold_y):
        if not self.ser:
            return
        
        # Формируем пакет
        packet = struct.pack('<Bf', PKT_CLEANUP, threshold_y)
        crc = self.calculate_crc(packet)
        full_packet = struct.pack('<B', START_BYTE) + packet + struct.pack('<BB', crc, END_BYTE)
        
        try:
            self.ser.write(full_packet)
            self.sent_packets += 1
            
            if self.debug:
                self._log_packet("out", PKT_CLEANUP, 
                                f"(threshold_y={threshold_y:.1f})")
        except Exception as e:
            self.error_packets += 1
            print(f"✗ Ошибка отправки cleanup: {e}")
    
    def send_init_game(self):
        if not self.ser:
            return
        
        # Формируем пакет
        packet = struct.pack('<B', PKT_INIT_GAME)
        crc = self.calculate_crc(packet)
        full_packet = struct.pack('<B', START_BYTE) + packet + struct.pack('<BB', crc, END_BYTE)
        
        try:
            self.ser.write(full_packet)
            self.sent_packets += 1
            
            if self.debug:
                self._log_packet("out", PKT_INIT_GAME, "(initialization)")
            else:
                print("✓ Отправлен INIT_GAME")
        except Exception as e:
            self.error_packets += 1
            print(f"✗ Ошибка отправки init: {e}")
    
    def receive_game_state(self) -> Optional[GameStateFromSTM32]:
        if not self.ser:
            return None
        
        try:
            # Читаем все доступные данные
            if self.ser.in_waiting > 0:
                self.packet_buffer += self.ser.read(self.ser.in_waiting)
            
            # Ищем начало пакета
            while len(self.packet_buffer) > 0:
                # Ищем стартовый байт
                start_pos = self.packet_buffer.find(bytes([START_BYTE]))
                
                if start_pos == -1:
                    # Нет стартового байта - сохраняем остаток и выходим
                    if len(self.packet_buffer) > 100:
                        self.packet_buffer = self.packet_buffer[-100:]
                    return None
                
                # Удаляем все до стартового байта
                self.packet_buffer = self.packet_buffer[start_pos:]
                
                # Проверяем минимальный размер пакета
                if len(self.packet_buffer) < 10:  # Минимальный размер пакета
                    return None
                
                # Ищем конечный байт
                end_pos = self.packet_buffer.find(bytes([END_BYTE]))
                
                if end_pos == -1:
                    # Нет конечного байта - выходим, ждем больше данных
                    return None
                
                # Извлекаем полный пакет
                packet_data = self.packet_buffer[:end_pos + 1]
                self.packet_buffer = self.packet_buffer[end_pos + 1:]
                
                # Проверяем длину пакета
                if len(packet_data) < 10:
                    continue
                
                # Проверка CRC
                crc_received = packet_data[-2]
                crc_calculated = self.calculate_crc(packet_data[1:-2])
                
                if crc_received != crc_calculated:
                    self.error_packets += 1
                    if self.debug:
                        print(f"✗ Ошибка контрольной суммы: {crc_calculated} != {crc_received}")
                    continue
                
                # Проверка заголовка
                if packet_data[1] != PKT_GAME_STATE:
                    continue
                
                # Последовательная распаковка пакета для отладки
                offset = 2  # Пропускаем START_BYTE и тип пакета
                debug_info = []
                
                try:
                    # 1. Player data (18 bytes)
                    if offset + 18 > len(packet_data):
                        raise ValueError(f"Недостаточно данных для player (требуется 18, доступно {len(packet_data)-offset})")
                    
                    player_x, player_y, player_angle, player_health, player_score, player_shoot_cooldown = struct.unpack(
                        '<fffhHH', packet_data[offset:offset+18]
                    )
                    debug_info.append(f"Player: x={player_x:.1f}, y={player_y:.1f}, angle={player_angle:.1f}, "
                                    f"health={player_health}, score={player_score}, cooldown={player_shoot_cooldown}")
                    offset += 18
                    
                    # 2. Enemy count (1 byte)
                    if offset >= len(packet_data):
                        raise ValueError("Недостаточно данных для enemy_count")
                    enemy_count = packet_data[offset]
                    debug_info.append(f"Enemy count: {enemy_count}")
                    offset += 1
                    
                    # 3. Enemies data
                    enemies = []
                    for i in range(min(enemy_count, MAX_ENEMIES_IN_PACKET)):
                        if offset + 9 > len(packet_data):
                            raise ValueError(f"Недостаточно данных для enemy {i} (требуется 9, доступно {len(packet_data)-offset})")
                        
                        enemy_type, ex, ey, ehealth = struct.unpack('<Bffb', packet_data[offset:offset+9])
                        enemies.append({'type': enemy_type, 'x': ex, 'y': ey, 'health': ehealth})
                        debug_info.append(f"  Enemy {i}: type={enemy_type}, x={ex:.1f}, y={ey:.1f}, health={ehealth}")
                        offset += 9
                    
                    # 4. Projectile count (1 byte)
                    if offset >= len(packet_data):
                        raise ValueError("Недостаточно данных для projectile_count")
                    proj_count = packet_data[offset]
                    debug_info.append(f"Projectile count: {proj_count}")
                    offset += 1
                    
                    # 5. Projectiles data
                    projectiles = []
                    for i in range(min(proj_count, MAX_PROJECTILES_IN_PACKET)):
                        if offset + 9 > len(packet_data):
                            raise ValueError(f"Недостаточно данных для projectile {i} (требуется 9, доступно {len(packet_data)-offset})")
                        
                        px, py, is_player = struct.unpack('<ffB', packet_data[offset:offset+9])
                        projectiles.append({'x': px, 'y': py, 'is_player_shot': bool(is_player)})
                        debug_info.append(f"  Projectile {i}: x={px:.1f}, y={py:.1f}, player={is_player}")
                        offset += 9
                    
                    # 6. Whirlpool count (1 byte)
                    if offset >= len(packet_data):
                        raise ValueError("Недостаточно данных для whirlpool_count")
                    whirlpool_count = packet_data[offset]
                    debug_info.append(f"Whirlpool count: {whirlpool_count}")
                    offset += 1
                    
                    # 7. Whirlpools data
                    whirlpools = []
                    for i in range(min(whirlpool_count, MAX_WHIRLPOOLS_IN_PACKET)):
                        if offset + 9 > len(packet_data):
                            raise ValueError(f"Недостаточно данных для whirlpool {i} (требуется 9, доступно {len(packet_data)-offset})")
                        
                        wx, wy, used = struct.unpack('<ffB', packet_data[offset:offset+9])
                        whirlpools.append({'x': wx, 'y': wy, 'used': bool(used)})
                        debug_info.append(f"  Whirlpool {i}: x={wx:.1f}, y={wy:.1f}, used={used}")
                        offset += 9
                    
                    # 8. Camera и frame counter (8 bytes)
                    if offset + 8 > len(packet_data):
                        raise ValueError(f"Недостаточно данных для camera_y и frame_counter (требуется 8, доступно {len(packet_data)-offset})")
                    camera_y, frame_counter = struct.unpack('<fI', packet_data[offset:offset+8])
                    debug_info.append(f"Camera: y={camera_y:.1f}, frame={frame_counter}")
                    offset += 8
                    
                    # 9. CRC и END_BYTE уже проверены, поэтому мы здесь
                    
                    self.received_packets += 1
                    if self.debug:
                        self._log_packet("in", PKT_GAME_STATE, 
                                    f"(player_y={player_y:.1f}, enemies={len(enemies)})")
                        if self.debug:
                            print("✓ Успешная распаковка пакета:")
                            for info in debug_info:
                                print(f"  - {info}")
                    
                    return GameStateFromSTM32(
                        player_x, player_y, player_angle, player_health, player_score, player_shoot_cooldown,
                        enemies, projectiles, whirlpools, camera_y, frame_counter
                    )
                
                except Exception as e:
                    self.error_packets += 1
                    if self.debug:
                        print(f"✗ Ошибка парсинга пакета: {e}")
                        print("Содержимое пакета (первые 50 байт):", packet_data[:50])
                        print("Длина пакета:", len(packet_data))
                        print("Текущий offset:", offset)
                        print("Данные игрока (первые 20 байт):", packet_data[2:22])
                        # Попробуем распаковать только данные игрока для диагностики
                        try:
                            player_data = packet_data[2:20]  # 18 байт для игрока
                            print("Попытка распаковки данных игрока:")
                            print("  player_x:", struct.unpack('<f', player_data[0:4])[0])
                            print("  player_y:", struct.unpack('<f', player_data[4:8])[0])
                            print("  player_angle:", struct.unpack('<f', player_data[8:12])[0])
                            print("  player_health:", struct.unpack('<h', player_data[12:14])[0])
                            print("  player_score:", struct.unpack('<H', player_data[14:16])[0])
                            print("  player_shoot_cooldown:", struct.unpack('<H', player_data[16:18])[0])
                        except Exception as ex:
                            print(f"  Ошибка при распаковке данных игрока: {ex}")
                    return None
    
        except Exception as e:
            self.error_packets += 1
            if self.debug:
                import traceback
                print(f"✗ Ошибка приёма данных: {e}")
                print(traceback.format_exc())
            return None


    def print_statistics(self):
        """Вывод статистики UART-трафика"""
        print("\n===== СТАТИСТИКА UART-ТРАФИКА =====")
        print(f"Отправлено пакетов: {self.sent_packets}")
        print(f"Получено пакетов: {self.received_packets}")
        print(f"Ошибочных пакетов: {self.error_packets}")
        if self.sent_packets > 0:
            success_rate = (self.received_packets / self.sent_packets) * 100
            print(f"Успешных ответов: {success_rate:.1f}%")
        print("==================================\n")

# ============ ГЛАВНАЯ ИГРА ============

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Бескрайнее море — STM32 Edition")
        self.clock = pygame.time.Clock()
        
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.big_font = pygame.font.Font(None, 48)
        
        # UART
        self.uart = UARTProtocol(UART_PORT, UART_BAUDRATE, debug=True)
        
        # Визуальные объекты
        self.islands = []
        self.left_shores = []
        self.right_shores = []
        
        # Состояние из STM32
        self.game_state = None
        
        # Мир
        self.world_top = -SCREEN_HEIGHT * 2
        self.wave_offset = 0
        
        # Загрузка спрайтов
        self._load_sprites()
        
        # Инициализация игры на STM32
        self.uart.send_init_game()
        
        # Генерация начального мира
        for _ in range(WORLD_INITIAL_SEGMENTS):
            self._generate_world_segment()
    
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
        surf = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE), pygame.SRCALPHA)
        pygame.draw.polygon(surf, (0, 100, 255), [
            (PLAYER_SIZE//2, 0), (PLAYER_SIZE, PLAYER_SIZE),
            (PLAYER_SIZE//2, PLAYER_SIZE*0.7), (0, PLAYER_SIZE)
        ])
        return surf
    
    def _create_enemy_sprite(self, size, color):
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.polygon(surf, color, [
            (size//2, 0), (size, size),
            (size//2, size*0.7), (0, size)
        ])
        return surf
    
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
        """Генерация сегмента мира"""
        segment_start = self.world_top - WORLD_SEGMENT_HEIGHT
        segment_end = self.world_top
        
        print(f"Генерация сегмента: {segment_start} -> {segment_end}")
        
        # Берега
        self.left_shores.append(Shore('left', segment_start, segment_end))
        self.right_shores.append(Shore('right', segment_start, segment_end))
        
        # Отправка берегов на STM32
        self.uart.send_add_obstacle(1, 0, (segment_start + segment_end) / 2, SHORE_WIDTH)
        self.uart.send_add_obstacle(2, SCREEN_WIDTH, (segment_start + segment_end) / 2, SHORE_WIDTH)
        
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
            
            # Водовороты
            if random.random() < WHIRLPOOL_SPAWN_CHANCE:
                x = random.randint(300, SCREEN_WIDTH - 300)
                if self._is_position_clear(x, current_y):
                    self.uart.send_add_whirlpool(x, current_y)
            
            current_y += random.randint(60, 120)
        
        # Генерация врагов
        current_y = segment_start
        while current_y < segment_end:
            if current_y < self.game_state.player_y + WORLD_ENEMY_SPAWN_DISTANCE if self.game_state else True:
                # Простые враги
                if random.random() < ENEMY_SIMPLE_SPAWN_CHANCE:
                    x = random.randint(250, SCREEN_WIDTH - 250)
                    if self._is_position_clear(x, current_y, 40):
                        self.uart.send_add_enemy(0, x, current_y)
                
                # Сложные враги
                if random.random() < ENEMY_HARD_SPAWN_CHANCE:
                    x = random.randint(300, SCREEN_WIDTH - 300)
                    if self._is_position_clear(x, current_y, 60):
                        self.uart.send_add_enemy(1, x, current_y)
            
            current_y += random.randint(100, 200)
        
        self.world_top = segment_start
    
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
        
        # Очистка старых объектов
        cleanup_threshold = self.game_state.player_y + WORLD_CLEANUP_DISTANCE
        
        islands_before = len(self.islands)
        self.islands = [i for i in self.islands if i.y < cleanup_threshold]
        self.left_shores = [s for s in self.left_shores if s.start_y < cleanup_threshold]
        self.right_shores = [s for s in self.right_shores if s.start_y < cleanup_threshold]
        
        if islands_before != len(self.islands):
            self.uart.send_cleanup(cleanup_threshold)
        
        # Волны
        self.wave_offset = (self.wave_offset + 2) % 40
    
    def _game_over(self):
        """Экран окончания игры"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(220)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        game_over_font = pygame.font.Font(None, 84)
        game_over_text = game_over_font.render("ИГРА ОКОНЧЕНА", True, RED)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
        
        score_text = self.big_font.render(f"Финальный счёт: {self.game_state.player_score}", True, GOLD)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        
        miles = int(abs(self.game_state.player_y) / 10)
        distance_text = self.font.render(f"Пройдено: {miles} морских миль", 
                                        True, WHITE)
        distance_rect = distance_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
        
        restart_text = self.font.render("Нажмите R для перезапуска", True, CYAN)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 120))
        
        self.screen.blit(game_over_text, game_over_rect)
        self.screen.blit(score_text, score_rect)
        self.screen.blit(distance_text, distance_rect)
        self.screen.blit(restart_text, restart_rect)
        
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
            self.screen.fill(BLACK)
            text = self.font.render("Ожидание STM32...", True, WHITE)
            self.screen.blit(text, (SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2))
            pygame.display.flip()
            return
        
        # Море
        self.screen.fill(WATER_BLUE)
        
        # Волны
        self._draw_waves()
        
        camera_y = self.game_state.camera_y
        
        # Берега
        for shore in self.left_shores:
            shore.draw(self.screen, camera_y)
        for shore in self.right_shores:
            shore.draw(self.screen, camera_y)
        
        # Острова
        for island in self.islands:
            island.draw(self.screen, camera_y)
        
        # Водовороты
        self._draw_whirlpools(camera_y)
        
        # Враги
        self._draw_enemies(camera_y)
        
        # Снаряды
        self._draw_projectiles(camera_y)
        
        # Игрок
        self._draw_player(camera_y)
        
        # UI
        self._draw_ui()
        
        pygame.display.flip()
    
    def _draw_waves(self):
        """Рисуем волны"""
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
    
    def _draw_whirlpools(self, camera_y):
        """Рисуем водовороты"""
        for whirlpool in self.game_state.whirlpools:
            x = int(whirlpool['x'])
            y_screen = int(whirlpool['y'] - camera_y)
            
            if y_screen < -150 or y_screen > SCREEN_HEIGHT + 150:
                continue
            
            rotation = (pygame.time.get_ticks() / 10) % 360
            
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
    
    def _draw_enemies(self, camera_y):
        """Рисуем врагов"""
        for enemy in self.game_state.enemies:
            x = int(enemy['x'])
            y_screen = int(enemy['y'] - camera_y)
            
            if y_screen < -100 or y_screen > SCREEN_HEIGHT + 100:
                continue
            
            sprite = self.enemy_simple_sprite if enemy['type'] == 0 else self.enemy_hard_sprite
            rect = sprite.get_rect(center=(x, y_screen))
            self.screen.blit(sprite, rect.topleft)
            
            # Полоска здоровья
            if enemy['health'] > 0:
                bar_width = 30
                bar_height = 4
                health_ratio = enemy['health'] / (1 if enemy['type'] == 0 else 3)
                
                pygame.draw.rect(self.screen, RED, 
                               (x - bar_width//2, y_screen - 25, bar_width, bar_height))
                pygame.draw.rect(self.screen, (0, 255, 0), 
                               (x - bar_width//2, y_screen - 25, int(bar_width * health_ratio), bar_height))
    
    def _draw_projectiles(self, camera_y):
        """Рисуем снаряды"""
        for proj in self.game_state.projectiles:
            x = int(proj['x'])
            y_screen = int(proj['y'] - camera_y)
            
            color = PROJECTILE_COLOR_PLAYER if proj['is_player_shot'] else PROJECTILE_COLOR_ENEMY
            pygame.draw.circle(self.screen, color, (x, y_screen), PROJECTILE_RADIUS)
    
    def _draw_player(self, camera_y):
        """Рисуем игрока"""
        x = int(self.game_state.player_x)
        y_screen = int(self.game_state.player_y - camera_y)
        
        rotated = pygame.transform.rotate(self.player_sprite, -self.game_state.player_angle)
        rect = rotated.get_rect(center=(x, y_screen))
        self.screen.blit(rotated, rect.topleft)
    
    def _draw_ui(self):
        """Рисуем UI"""
        # Здоровье
        health_text = self.font.render(
            f"HP: {max(0, self.game_state.player_health)}/{PLAYER_MAX_HEALTH}", 
            True, WHITE
        )
        self.screen.blit(health_text, (UI_PADDING, UI_PADDING))
        
        health_ratio = max(0, self.game_state.player_health) / PLAYER_MAX_HEALTH
        
        pygame.draw.rect(self.screen, (100, 0, 0), 
                        (UI_PADDING, 60, UI_HEALTH_BAR_WIDTH, UI_HEALTH_BAR_HEIGHT))
        pygame.draw.rect(self.screen, (0, 200, 0), 
                        (UI_PADDING, 60, int(UI_HEALTH_BAR_WIDTH * health_ratio), UI_HEALTH_BAR_HEIGHT))
        pygame.draw.rect(self.screen, WHITE, 
                        (UI_PADDING, 60, UI_HEALTH_BAR_WIDTH, UI_HEALTH_BAR_HEIGHT), 3)
        
        # Счёт
        score_text = self.font.render(f"Счёт: {self.game_state.player_score}", True, GOLD)
        self.screen.blit(score_text, (SCREEN_WIDTH - 250, UI_PADDING))
        
        # Пройденные мили
        miles = int(abs(self.game_state.player_y) / 10)  # PIXELS_PER_MILE = 10
        miles_text = self.font.render(f"Мили: {miles}", True, WHITE)
        self.screen.blit(miles_text, (SCREEN_WIDTH - 250, 60))
        
        # Угол поворота
        angle_text = self.big_font.render(f"Угол: {int(self.game_state.player_angle)}°", True, CYAN)
        self.screen.blit(angle_text, (SCREEN_WIDTH // 2 - 100, UI_PADDING))
        
        # Направление выстрела
        if abs(self.game_state.player_angle) > 5:  # PLAYER_MIN_ANGLE_FOR_SIDE_SHOT
            direction = "↖ ЗАЛП ВЛЕВО-ВВЕРХ" if self.game_state.player_angle > 5 else "ЗАЛП ВПРАВО-ВВЕРХ ↗"
            dir_color = RED if self.game_state.player_shoot_cooldown == 0 else (100, 100, 100)
            dir_text = self.font.render(direction, True, dir_color)
            self.screen.blit(dir_text, (SCREEN_WIDTH // 2 - 200, 75))
        
        # Управление
        self._draw_controls()
        
        # Статистика
        self._draw_stats()
        
        # Эффект телепортации (если нужно)
        if hasattr(self, 'teleport_effect_timer') and self.teleport_effect_timer > 0:
            alpha = int((self.teleport_effect_timer / 30) * 200)
            flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            flash.set_alpha(alpha)
            flash.fill(WHITE)
            self.screen.blit(flash, (0, 0))

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

    def _draw_stats(self):
        """Отрисовка статистики"""
        whirlpool_count = len(self.game_state.whirlpools)
        enemy_count = len(self.game_state.enemies)
        
        stats_text = self.small_font.render(
            f"Островов: {len(self.islands)} | Врагов: {enemy_count} | Водоворотов: {whirlpool_count}", 
            True, (255, 200, 100))
        self.screen.blit(stats_text, (UI_PADDING, SCREEN_HEIGHT - 40))
        
        # Информация о водоворотах
        active_whirlpools = sum(1 for w in self.game_state.whirlpools if not w['used'])
        if whirlpool_count > 0:
            whirlpool_info = self.small_font.render(
                f"🌀 Активных водоворотов: {active_whirlpools}/{whirlpool_count}", 
                True, CYAN)
            self.screen.blit(whirlpool_info, (UI_PADDING, SCREEN_HEIGHT - 70))
        
        # Информация о врагах
        simple_enemies = sum(1 for e in self.game_state.enemies if e['type'] == 0)
        hard_enemies = sum(1 for e in self.game_state.enemies if e['type'] == 1)
        if enemy_count > 0:
            enemy_info = self.small_font.render(
                f"⚔️ Враги: {simple_enemies} простых | {hard_enemies} серьезных", 
                True, (255, 100, 100))
            self.screen.blit(enemy_info, (UI_PADDING, SCREEN_HEIGHT - 100))
    
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
        last_world_generation = 0
        
        while running:
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
        pygame.quit()
        sys.exit(1)