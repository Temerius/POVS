import serial
import struct
import time
from typing import Optional
from dataclasses import dataclass

START_BYTE = 0xAA
END_BYTE = 0x55
PKT_BUTTONS = 0x01
PKT_MILES = 0x02

UART_PORT = 'COM5'
UART_BAUDRATE = 115200
UART_TIMEOUT = 0.001


@dataclass
class ButtonState:
    """Состояние кнопок от STM32"""
    left_pressed: bool
    right_pressed: bool
    fire_pressed: bool
    fire_just_pressed: bool = False 
    
    def to_pygame_keys(self):
        """Преобразование в формат pygame keys"""
        import pygame
        keys = [False] * 512
        if self.left_pressed:
            keys[pygame.K_a] = True
        if self.right_pressed:
            keys[pygame.K_d] = True
        if self.fire_pressed:
            keys[pygame.K_SPACE] = True
        return keys


class UARTProtocol:
    """Класс для работы с UART протоколом"""
    
    def __init__(self, port=UART_PORT, baudrate=UART_BAUDRATE, debug=False):
        self.debug = debug
        self.packet_buffer = b''
        self.sent_packets = 0
        self.received_packets = 0
        self.error_packets = 0
        
        # Последнее состояние кнопок
        self.last_button_state = ButtonState(False, False, False)
        self.prev_fire_state = False
        
        self.last_receive_time = time.time()
        self.connection_timeout = 1.0
        self.board_reset_detected = False
        
        try:
            self.ser = serial.Serial(port, baudrate, timeout=UART_TIMEOUT)
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            print(f"UART подключен: {port} @ {baudrate}")
        except Exception as e:
            print(f"Ошибка подключения UART: {e}")
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
    
    def is_connected(self):
        """Проверка связи с платой"""
        if not self.ser:
            return False
        return (time.time() - self.last_receive_time) < self.connection_timeout
    
    def check_reset(self):
        """Проверка reset платы"""
        if self.board_reset_detected:
            self.board_reset_detected = False
            return True
        return False
    
    def send_miles(self, miles: int):
        """Отправка счёта миль на STM32"""
        if not self.ser:
            return
        
        miles = max(0, min(9999, int(miles)))
        
        data_for_crc = struct.pack('<BH', PKT_MILES, miles)
        crc = self.calculate_crc(data_for_crc)
        
        full_packet = struct.pack('<B', START_BYTE) + data_for_crc + struct.pack('<BB', crc, END_BYTE)
        
        try:
            self.ser.write(full_packet)
            self.sent_packets += 1
            
            if self.debug and self.sent_packets % 100 == 0:
                print(f"[SEND] Мили: {miles} | Пакет: {full_packet.hex()}")
        except Exception as e:
            self.error_packets += 1
            if self.debug:
                print(f"Ошибка отправки миль: {e}")
    
    def receive_buttons(self) -> ButtonState:
        """Получение состояния кнопок от STM32"""
        if not self.ser:
            return self.last_button_state
        
        try:
            if self.ser.in_waiting > 0:
                bytes_to_read = min(self.ser.in_waiting, 128)
                self.packet_buffer += self.ser.read(bytes_to_read)
                
                if len(self.packet_buffer) > 512:
                    self.packet_buffer = self.packet_buffer[-256:]
            
            while len(self.packet_buffer) >= 7:
                start_pos = self.packet_buffer.find(bytes([START_BYTE]))
                
                if start_pos == -1:
                    self.packet_buffer = b''
                    break
                
                if start_pos > 0:
                    self.packet_buffer = self.packet_buffer[start_pos:]
                
                if len(self.packet_buffer) < 7:
                    break
                
                end_pos = self.packet_buffer.find(bytes([END_BYTE]), 1)
                
                if end_pos == -1:
                    if len(self.packet_buffer) > 20:
                        self.packet_buffer = self.packet_buffer[1:]
                    break
                
                packet_data = self.packet_buffer[:end_pos + 1]
                self.packet_buffer = self.packet_buffer[end_pos + 1:]
                
                if len(packet_data) != 7:
                    continue
                
                if packet_data[1] != PKT_BUTTONS:
                    continue
                
                crc_received = packet_data[-2]
                crc_calculated = self.calculate_crc(packet_data[1:-2])
                
                if crc_received != crc_calculated:
                    self.error_packets += 1
                    if self.debug:
                        print(f"✗ CRC error: calc={crc_calculated:02X}, recv={crc_received:02X} | Пакет: {packet_data.hex()}")
                    continue
                
                left = bool(packet_data[2])
                right = bool(packet_data[3])
                fire = bool(packet_data[4])
                
                fire_just_pressed = fire and not self.prev_fire_state
                self.prev_fire_state = fire
                
                self.received_packets += 1
                self.last_receive_time = time.time()
                
                if (time.time() - self.last_receive_time) > 2.0:
                    self.board_reset_detected = True
                    print("Обнаружен RESET платы!")
                
                self.last_button_state = ButtonState(left, right, fire, fire_just_pressed)
                
                if self.debug and self.received_packets % 100 == 0:
                    print(f"[RECV] L={left} R={right} F={fire} | Пакет: {packet_data.hex()}")
            
            return self.last_button_state
        
        except Exception as e:
            self.error_packets += 1
            if self.debug:
                print(f"✗ Ошибка приёма кнопок: {e}")
            return self.last_button_state
    
    def get_pygame_keys(self):
        """Получить состояние кнопок в формате pygame keys"""
        button_state = self.receive_buttons()
        return button_state.to_pygame_keys()
    
    def print_statistics(self):
        """Вывод статистики UART-трафика"""
        print("\n===== СТАТИСТИКА UART-ТРАФИКА =====")
        print(f"Отправлено пакетов: {self.sent_packets}")
        print(f"Получено пакетов: {self.received_packets}")
        print(f"Ошибочных пакетов: {self.error_packets}")
        if self.sent_packets > 0:
            success_rate = (self.received_packets / self.sent_packets) * 100
            print(f"Соотношение: {success_rate:.1f}%")
        print("==================================\n")