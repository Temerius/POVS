# uart_protocol.py - UART протокол обмена данными с STM32

import serial
import struct
import pygame
from typing import Optional, List
from dataclasses import dataclass
from config import *


@dataclass
class GameStateFromSTM32:
    """Структура состояния игры от STM32"""
    player_x: float
    player_y: float
    player_angle: float
    player_health: int
    player_score: int
    player_shoot_cooldown: int
    enemies: List[dict]  # {'type', 'x', 'y', 'health', 'direction'}
    projectiles: List[dict]  # {'x', 'y', 'is_player_shot'}
    whirlpools: List[dict]  # {'x', 'y', 'used'}
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
            PKT_ADD_SHORE: "ADD_SHORE"
        }
        return names.get(packet_type, f"UNKNOWN_{packet_type:02X}")
    
    def send_add_obstacle(self, obstacle_type, x, y, radius):
        """Отправка команды добавления препятствия (острова)"""
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
        """Отправка команды добавления берега
        side: 'left' или 'right'
        """
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
    
    def receive_game_state(self) -> Optional[GameStateFromSTM32]:
        """Получение состояния игры от STM32"""
        if not self.ser:
            return None
        
        try:
            # Читаем все доступные данные с ограничением
            if self.ser.in_waiting > 0:
                bytes_to_read = min(self.ser.in_waiting, 256)
                self.packet_buffer += self.ser.read(bytes_to_read)
                
                # Ограничение максимального размера буфера
                if len(self.packet_buffer) > 4096:
                    self.packet_buffer = self.packet_buffer[-2048:]
                    self.error_packets += 1
                    if self.debug:
                        print("⚠️ Буфер переполнен, сброшено старое содержимое")
            
            # Ищем начало пакета
            packets_processed = 0
            max_packets_per_frame = 3
            
            while len(self.packet_buffer) > 0 and packets_processed < max_packets_per_frame:
                # Ищем стартовый байт
                start_pos = self.packet_buffer.find(bytes([START_BYTE]))
                
                if start_pos == -1:
                    if self.crc_error_count > 5:
                        self.packet_buffer = b''
                        self.crc_error_count = 0
                        if self.debug:
                            print("⚠️ Много ошибок CRC, буфер полностью сброшен")
                    return None
                
                # Удаляем все до стартового байта
                self.packet_buffer = self.packet_buffer[start_pos:]
                
                # Проверяем минимальный размер пакета
                if len(self.packet_buffer) < 10:
                    return None
                
                # Ищем конечный байт
                end_pos = self.packet_buffer.find(bytes([END_BYTE]))
                
                if end_pos == -1:
                    return None
                
                # Извлекаем полный пакет
                packet_data = self.packet_buffer[:end_pos + 1]
                self.packet_buffer = self.packet_buffer[end_pos + 1:]
                
                if len(packet_data) < 10:
                    continue
                
                # Проверка CRC
                crc_received = packet_data[-2]
                crc_calculated = self.calculate_crc(packet_data[1:-2])
                
                if crc_received != crc_calculated:
                    self.crc_error_count += 1
                    self.error_packets += 1
                    
                    if self.crc_error_count > 10:
                        self.packet_buffer = b''
                        self.crc_error_count = 0
                        if self.debug:
                            print("⚠️ Критическое количество ошибок CRC, полный сброс буфера")
                    else:
                        if self.debug:
                            print(f"✗ CRC error: calc={crc_calculated}, recv={crc_received}")
                    continue
                
                # Сброс счётчика ошибок при успешном приёме
                self.crc_error_count = max(0, self.crc_error_count - 1)
                
                # Проверка заголовка
                if packet_data[1] != PKT_GAME_STATE:
                    continue
                
                # Распаковка пакета
                offset = 2
                
                try:
                    # 1. Player data (18 bytes)
                    player_x, player_y, player_angle, player_health, player_score, player_shoot_cooldown = struct.unpack(
                        '<fffhHH', packet_data[offset:offset+18]
                    )
                    offset += 18
                    
                    # 2. Enemy count (1 byte)
                    enemy_count = packet_data[offset]
                    offset += 1
                    
                    # 3. Enemy data
                    enemies = []
                    for i in range(min(enemy_count, MAX_ENEMIES_IN_PACKET)):
                        enemy_type, ex, ey, ehealth, direction = struct.unpack('<BffBB', packet_data[offset:offset+11])
                        enemies.append({
                            'type': enemy_type, 
                            'x': ex, 
                            'y': ey, 
                            'health': ehealth,
                            'direction': direction
                        })
                        offset += 11
                    
                    # 4. Projectile count (1 byte)
                    proj_count = packet_data[offset]
                    offset += 1
                    
                    # 5. Projectiles data
                    projectiles = []
                    for i in range(min(proj_count, MAX_PROJECTILES_IN_PACKET)):
                        px, py, is_player = struct.unpack('<ffB', packet_data[offset:offset+9])
                        projectiles.append({'x': px, 'y': py, 'is_player_shot': bool(is_player)})
                        offset += 9
                    
                    # 6. Whirlpool count (1 byte)
                    whirlpool_count = packet_data[offset]
                    offset += 1
                    
                    # 7. Whirlpools data
                    whirlpools = []
                    for i in range(min(whirlpool_count, MAX_WHIRLPOOLS_IN_PACKET)):
                        wx, wy, used = struct.unpack('<ffB', packet_data[offset:offset+9])
                        whirlpools.append({'x': wx, 'y': wy, 'used': bool(used)})
                        offset += 9
                    
                    # 8. Camera и frame counter (8 bytes)
                    camera_y, frame_counter = struct.unpack('<fI', packet_data[offset:offset+8])
                    offset += 8
                    
                    self.received_packets += 1
                    if self.debug:
                        self._log_packet("in", PKT_GAME_STATE, 
                                    f"(player_y={player_y:.1f}, enemies={len(enemies)})")
                    
                    packets_processed += 1
                    return GameStateFromSTM32(
                        player_x, player_y, player_angle, player_health, player_score, player_shoot_cooldown,
                        enemies, projectiles, whirlpools, camera_y, frame_counter
                    )
                
                except Exception as e:
                    self.error_packets += 1
                    if self.debug:
                        print(f"✗ Ошибка парсинга пакета: {e}")
                    continue
            
            return None
        
        except Exception as e:
            self.error_packets += 1
            self.packet_buffer = b''
            self.crc_error_count = 0
            if self.debug:
                import traceback
                print(f"✗ Критическая ошибка приёма данных: {e}")
                print(traceback.format_exc())
            return None
    
    def receive_debug_packet(self) -> Optional[dict]:
        """Получение и обработка debug-пакета от STM32"""
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