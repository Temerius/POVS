# uart_protocol.py - UART протокол с поддержкой бенчмарка

import serial
import struct
import pygame
from typing import Optional, List
from dataclasses import dataclass
from config import *


import logging
import struct

# Настройка логгеров
logger = logging.getLogger("game_comm")
logger.setLevel(logging.DEBUG)

# Форматтер
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# INFO логгер (успешные пакеты)
info_handler = logging.FileHandler('game_info.log')
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(formatter)

# ERROR логгер (полный разбор ошибок)
error_handler = logging.FileHandler('game_errors.log')
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)

# Консольный логгер для критических ошибок
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(formatter)

logger.addHandler(info_handler)
logger.addHandler(error_handler)
logger.addHandler(console_handler)


@dataclass
class GameStateFromSTM32:
    """Структура состояния игры от STM32"""
    player_x: float
    player_y: float
    player_angle: float
    player_health: int
    player_score: int
    player_shoot_cooldown: int
    enemies: List[dict]
    projectiles: List[dict]
    whirlpools: List[dict]
    camera_y: float
    frame_counter: int


class UARTProtocol:
    """Класс для работы с UART протоколом"""
    
    def __init__(self, port, baudrate, debug=False):
        self.debug = debug
        self.packet_buffer = b''
        self.sent_packets = 0
        self.received_packets = 0
        self.error_packets = 0
        self.last_packet_time = 0
        self.crc_error_count = 0
        
        # НОВОЕ: Статистика бенчмарка
        self.last_benchmark_stats = None
        
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
        """Логирование пакетов"""
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
            PKT_ADD_OBSTACLE: "ADD_OBSTACLE",
            PKT_INIT_GAME: "INIT_GAME",
            PKT_ADD_SHORE: "ADD_SHORE",
            PKT_DEBUG: "DEBUG",
            0xFF: "BENCHMARK"
        }
        return names.get(packet_type, f"UNKNOWN_{packet_type:02X}")
    
    def send_add_obstacle(self, obstacle_type, x, y, radius):
        """Отправка команды добавления препятствия"""
        if not self.ser:
            return
        
        packet = struct.pack('<BBfff', PKT_ADD_OBSTACLE, obstacle_type, x, y, radius)
        crc = self.calculate_crc(packet)
        full_packet = struct.pack('<B', START_BYTE) + packet + struct.pack('<BB', crc, END_BYTE)
        
        try:
            self.ser.write(full_packet)
            self.sent_packets += 1
            
            if self.debug:
                obstacle_names = {0: "ISLAND"}
                name = obstacle_names.get(obstacle_type, f"UNKNOWN_{obstacle_type}")
                self._log_packet("out", PKT_ADD_OBSTACLE, 
                                f"(type={name}, x={x:.1f}, y={y:.1f}, radius={radius:.1f})")
        except Exception as e:
            self.error_packets += 1
            print(f"✗ Ошибка отправки препятствия: {e}")
    
    def send_add_shore(self, side, start_y, end_y):
        """Отправка команды добавления берега"""
        if not self.ser:
            return
        
        side_byte = 0 if side == 'left' else 1
        packet = struct.pack('<BBff', PKT_ADD_SHORE, side_byte, start_y, end_y)
        crc = self.calculate_crc(packet)
        full_packet = struct.pack('<B', START_BYTE) + packet + struct.pack('<BB', crc, END_BYTE)
        
        try:
            self.ser.write(full_packet)
            self.sent_packets += 1
            
            if self.debug:
                self._log_packet("out", PKT_ADD_SHORE, 
                                f"(side={side}, start_y={start_y:.1f}, end_y={end_y:.1f})")
        except Exception as e:
            self.error_packets += 1
            print(f"✗ Ошибка отправки берега: {e}")
    
    def send_init_game(self):
        """Отправка команды инициализации игры"""
        if not self.ser:
            return
        
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
    
    def receive_debug_packet(self) -> Optional[dict]:
        """Получение debug-пакета (включая бенчмарк)"""
        if not self.ser:
            return None
        
        try:
            if self.ser.in_waiting > 0:
                self.packet_buffer += self.ser.read(self.ser.in_waiting)
            
            while len(self.packet_buffer) > 0:
                start_pos = self.packet_buffer.find(bytes([START_BYTE]))
                if start_pos == -1:
                    if len(self.packet_buffer) > 100:
                        self.packet_buffer = self.packet_buffer[-100:]
                    return None
                
                self.packet_buffer = self.packet_buffer[start_pos:]
                
                if len(self.packet_buffer) < 10:
                    return None
                
                if self.packet_buffer[1] != PKT_DEBUG:
                    self.packet_buffer = self.packet_buffer[1:]
                    continue
                
                end_pos = self.packet_buffer.find(bytes([END_BYTE]))
                if end_pos == -1:
                    return None
                
                packet_data = self.packet_buffer[:end_pos + 1]
                self.packet_buffer = self.packet_buffer[end_pos + 1:]
                
                if len(packet_data) < 20:
                    continue
                
                offset = 2
                
                packet_type = packet_data[offset]
                
                # Проверка: это бенчмарк-пакет?
                if packet_type == 0xFF:
                    # Парсим бенчмарк-сообщение
                    message_bytes = packet_data[offset + 6:offset + 38]
                    try:
                        message = message_bytes.decode('utf-8', errors='ignore').rstrip('\x00')
                        self.last_benchmark_stats = message
                        print(f"[BENCHMARK] {message}")
                    except:
                        pass
                    continue
                
                # Обычный debug-пакет
                packet_size = packet_data[offset + 1]
                parse_state = packet_data[offset + 2]
                crc_recv = packet_data[offset + 3]
                crc_calc = packet_data[offset + 4]
                success = packet_data[offset + 5]
                
                message_bytes = packet_data[offset + 6:offset + 38]
                try:
                    message = message_bytes.decode('utf-8', errors='ignore').rstrip('\x00')
                except:
                    message = str(message_bytes)
                
                return {
                    'packet_type': packet_type,
                    'packet_size': packet_size,
                    'parse_state': parse_state,
                    'crc_received': crc_recv,
                    'crc_calculated': crc_calc,
                    'success': bool(success),
                    'message': message
                }
        
        except Exception as e:
            print(f"✗ Ошибка приёма debug-пакета: {e}")
            return None
    
    def receive_game_state(self) -> Optional[GameStateFromSTM32]:
        """Получение состояния игры от STM32 с детальной диагностикой (включая парсинг при ошибках CRC)"""
        if not self.ser:
            return None
        
        try:
            if self.ser.in_waiting > 0:
                bytes_to_read = min(self.ser.in_waiting, 256)
                self.packet_buffer += self.ser.read(bytes_to_read)
                
                if len(self.packet_buffer) > 4096:
                    print(f"⚠️ Буфер переполнен! Размер: {len(self.packet_buffer)} байт")
                    self.packet_buffer = self.packet_buffer[-2048:]
                    self.error_packets += 1
            
            packets_processed = 0
            max_packets_per_frame = 3
            
            while len(self.packet_buffer) > 0 and packets_processed < max_packets_per_frame:
                start_pos = self.packet_buffer.find(bytes([START_BYTE]))
                
                if start_pos == -1:
                    if self.debug and len(self.packet_buffer) > 0:
                        print(f"⚠️ START_BYTE не найден. Буфер размер: {len(self.packet_buffer)}")
                        print(f"   Первые 20 байт: {self.packet_buffer[:20].hex()}")
                    
                    if self.crc_error_count > 5:
                        self.packet_buffer = b''
                        self.crc_error_count = 0
                        if self.debug:
                            print("⚠️ Много ошибок CRC, буфер полностью сброшен")
                    return None
                
                # Пропускаем мусор до START_BYTE
                if start_pos > 0 and self.debug:
                    print(f"⚠️ Пропущено {start_pos} байт мусора до START_BYTE")
                    print(f"   Мусор: {self.packet_buffer[:start_pos].hex()}")
                
                self.packet_buffer = self.packet_buffer[start_pos:]
                
                if len(self.packet_buffer) < 10:
                    return None
                
                end_pos = self.packet_buffer.find(bytes([END_BYTE]))
                
                if end_pos == -1:
                    if self.debug and len(self.packet_buffer) > 100:
                        print(f"⚠️ END_BYTE не найден. Буфер: {len(self.packet_buffer)} байт")
                        print(f"   Начало пакета: {self.packet_buffer[:50].hex()}")
                    return None
                
                packet_data = self.packet_buffer[:end_pos + 1]
                self.packet_buffer = self.packet_buffer[end_pos + 1:]
                
                if len(packet_data) < 10:
                    if self.debug:
                        print(f"⚠️ Пакет слишком маленький: {len(packet_data)} байт")
                        print(f"   Данные: {packet_data.hex()}")
                    continue
                
                # === ДЕТАЛЬНЫЙ АНАЛИЗ ПАКЕТА ===
                print(f"\n{'='*80}")
                print(f"[PACKET ANALYSIS] Размер: {len(packet_data)} байт (CRC может быть неверным!)")
                print(f"{'='*80}")
                
                # Показываем структуру пакета
                print(f"START_BYTE: 0x{packet_data[0]:02X} (ожидается 0x{START_BYTE:02X})")
                print(f"PACKET_TYPE: 0x{packet_data[1]:02X} (ожидается 0x{PKT_GAME_STATE:02X})")
                print(f"END_BYTE: 0x{packet_data[-1]:02X} (ожидается 0x{END_BYTE:02X})")
                
                crc_received = packet_data[-2]
                crc_calculated = self.calculate_crc(packet_data[1:-2])
                
                print(f"CRC: received=0x{crc_received:02X}, calculated=0x{crc_calculated:02X}", end="")
                if crc_received == crc_calculated:
                    print(" ✓ OK")
                else:
                    print(" ✗ MISMATCH (ПРОДОЛЖАЕМ ПАРСИНГ ДЛЯ ОТЛАДКИ!)")
                
                # Hex dump первых 100 байт
                print(f"\nHex dump (первые 100 байт):")
                for i in range(0, min(100, len(packet_data)), 16):
                    hex_str = ' '.join(f'{b:02X}' for b in packet_data[i:i+16])
                    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in packet_data[i:i+16])
                    print(f"  {i:04X}: {hex_str:<48} | {ascii_str}")
                
                # === КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: УБРАН CONTINUE ПОСЛЕ ОШИБКИ CRC ===
                if crc_received != crc_calculated:
                    self.crc_error_count += 1
                    self.error_packets += 1
                    
                    print(f"\n❌ CRC ОШИБКА #{self.crc_error_count} (НО ПРОДОЛЖАЕМ ПАРСИНГ!)")
                    print(f"   Размер данных для CRC: {len(packet_data[1:-2])} байт")
                    print(f"   Полный пакет: {packet_data.hex()}")
                    
                    if self.crc_error_count > 10:
                        self.packet_buffer = b''
                        self.crc_error_count = 0
                        print("⚠️ Критическое количество ошибок CRC, полный сброс буфера")
                    
                    # УБРАНО: continue  <-- ЭТО БЫЛО ПРЕПЯТСТВИЕМ ДЛЯ ПАРСИНГА
                    print(f"{'='*80}\n")
                else:
                    self.crc_error_count = max(0, self.crc_error_count - 1)
                
                # === ПРОДОЛЖАЕМ ПАРСИНГ ВСЕГДА (ДАЖЕ ПРИ ОШИБКЕ CRC) ===
                if packet_data[1] != PKT_GAME_STATE:
                    print(f"⚠️ Неожиданный тип пакета: 0x{packet_data[1]:02X} (НО ПРОБУЕМ ПАРСИНГ)")
                    print(f"{'='*80}\n")
                
                # === ПАРСИНГ ДАННЫХ С ДЕТАЛЬНЫМ ВЫВОДОМ (ВСЕГДА!) ===
                offset = 2
                
                try:
                    print(f"\n[ПАРСИНГ ДАННЫХ] (Даже при ошибке CRC)")
                    
                    # Player data
                    player_x, player_y, player_angle, player_health, player_score, player_shoot_cooldown = struct.unpack(
                        '<fffhHH', packet_data[offset:offset+18]
                    )
                    print(f"Player: x={player_x:.1f}, y={player_y:.1f}, angle={player_angle:.1f}°")
                    print(f"        health={player_health}/{PLAYER_MAX_HEALTH}, score={player_score}, cooldown={player_shoot_cooldown}")
                    offset += 18
                    
                    # Enemies
                    enemy_count = packet_data[offset]
                    print(f"Enemies: count={enemy_count} (max={MAX_ENEMIES_IN_PACKET})")
                    offset += 1
                    
                    enemies = []
                    for i in range(min(enemy_count, MAX_ENEMIES_IN_PACKET)):
                        enemy_type, ex, ey, ehealth, direction = struct.unpack('<BffBB', packet_data[offset:offset+11])
                        enemy_name = "Simple" if enemy_type == 0 else "Hard"
                        dir_name = ['up', 'right', 'down', 'left'][direction] if direction < 4 else 'unknown'
                        print(f"  Enemy {i+1}: type={enemy_name}, pos=({ex:.1f}, {ey:.1f}), hp={ehealth}, dir={dir_name}")
                        enemies.append({
                            'type': enemy_type, 
                            'x': ex, 
                            'y': ey, 
                            'health': ehealth,
                            'direction': direction
                        })
                        offset += 11
                    
                    # Projectiles
                    proj_count = packet_data[offset]
                    print(f"Projectiles: count={proj_count} (max={MAX_PROJECTILES_IN_PACKET})")
                    offset += 1
                    
                    projectiles = []
                    for i in range(min(proj_count, MAX_PROJECTILES_IN_PACKET)):
                        px, py, is_player = struct.unpack('<ffB', packet_data[offset:offset+9])
                        owner = "Player" if is_player else "Enemy"
                        print(f"  Proj {i+1}: pos=({px:.1f}, {py:.1f}), owner={owner}")
                        projectiles.append({'x': px, 'y': py, 'is_player_shot': bool(is_player)})
                        offset += 9
                    
                    # Whirlpools
                    whirlpool_count = packet_data[offset]
                    print(f"Whirlpools: count={whirlpool_count} (max={MAX_WHIRLPOOLS_IN_PACKET})")
                    offset += 1
                    
                    whirlpools = []
                    for i in range(min(whirlpool_count, MAX_WHIRLPOOLS_IN_PACKET)):
                        wx, wy, used = struct.unpack('<ffB', packet_data[offset:offset+9])
                        status = "USED" if used else "active"
                        print(f"  Whirlpool {i+1}: pos=({wx:.1f}, {wy:.1f}), status={status}")
                        whirlpools.append({'x': wx, 'y': wy, 'used': bool(used)})
                        offset += 9
                    
                    # Camera & frame
                    camera_y, frame_counter = struct.unpack('<fI', packet_data[offset:offset+8])
                    print(f"Camera Y: {camera_y:.1f}")
                    print(f"Frame: {frame_counter}")
                    offset += 8
                    
                    # Проверка размера
                    expected_size = offset + 2  # +2 для CRC и END_BYTE
                    actual_size = len(packet_data)
                    print(f"\nPacket size check: expected={expected_size}, actual={actual_size}", end="")
                    if expected_size == actual_size:
                        print(" ✓")
                    else:
                        print(f" ✗ MISMATCH (diff={actual_size - expected_size})")
                    
                    self.received_packets += 1
                    packets_processed += 1
                    
                    print(f"{'='*80}")
                    print(f"✅ ПАКЕТ ОБРАБОТАН (даже с ошибкой CRC) #{self.received_packets}")
                    print(f"{'='*80}\n")
                    
                    return GameStateFromSTM32(
                        player_x, player_y, player_angle, player_health, player_score, player_shoot_cooldown,
                        enemies, projectiles, whirlpools, camera_y, frame_counter
                    )
                
                except struct.error as e:
                    self.error_packets += 1
                    print(f"\n❌ STRUCT UNPACK ERROR: {e}")
                    print(f"   Offset: {offset}, осталось байт: {len(packet_data) - offset}")
                    print(f"   Данные на offset: {packet_data[offset:offset+20].hex()}")
                    print(f"{'='*80}\n")
                    continue
                
                except Exception as e:
                    self.error_packets += 1
                    print(f"\n❌ PARSING ERROR: {e}")
                    import traceback
                    traceback.print_exc()
                    print(f"{'='*80}\n")
                    continue
            
            return None
        
        except Exception as e:
            self.error_packets += 1
            self.packet_buffer = b''
            self.crc_error_count = 0
            print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА ПРИЁМА: {e}")
            import traceback
            traceback.print_exc()
            return None
    def get_benchmark_stats(self):
        """Получить последнюю статистику бенчмарка"""
        return self.last_benchmark_stats
    
    def print_debug_packet(self, debug_info):
        """Красивый вывод debug-пакета"""
        packet_names = {
            0x01: "GAME_STATE",
            0x02: "ADD_ENEMY",
            0x03: "ADD_OBSTACLE",
            0x04: "CLEANUP",
            0x05: "INIT_GAME",
            0x06: "ADD_WHIRLPOOL",
            0xFF: "UNKNOWN"
        }
        
        packet_name = packet_names.get(debug_info['packet_type'], f"0x{debug_info['packet_type']:02X}")
        status = "✓ SUCCESS" if debug_info['success'] else "✗ FAILED"
        
        print(f"\n{'='*60}")
        print(f"[DEBUG PACKET] {status}")
        print(f"  Type: {packet_name}")
        print(f"  Size: {debug_info['packet_size']} bytes")
        print(f"  Parse State: {debug_info['parse_state']}")
        print(f"  CRC: received=0x{debug_info['crc_received']:02X}, "
            f"calculated=0x{debug_info['crc_calculated']:02X}")
        print(f"  Message: {debug_info['message']}")
        print(f"{'='*60}\n")
    
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