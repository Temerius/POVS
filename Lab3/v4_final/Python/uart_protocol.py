# uart_protocol.py - UART протокол для кнопок и миль

import serial
import struct
from typing import Optional
from dataclasses import dataclass

# Константы
START_BYTE = 0xAA
END_BYTE = 0x55
PKT_BUTTONS = 0x01
PKT_MILES = 0x02

UART_PORT = 'COM5'  # Измените на ваш порт
UART_BAUDRATE = 115200
UART_TIMEOUT = 0.001


@dataclass
class ButtonState:
    """Состояние кнопок от STM32"""
    left_pressed: bool
    right_pressed: bool
    fire_pressed: bool
    
    # Для совместимости с pygame keys
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
    
    def __init__(self, port=UART_PORT, baudrate=UART_BAUDRATE, debug=True):
        self.debug = debug
        self.packet_buffer = b''
        self.sent_packets = 0
        self.received_packets = 0
        self.error_packets = 0
        
        # Последнее состояние кнопок
        self.last_button_state = ButtonState(False, False, False)
        
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
    
    def send_miles(self, miles: int):
        """Отправка счёта миль на STM32"""
        if not self.ser:
            return
        
        # Ограничиваем диапазон 0-9999
        miles = max(0, min(9999, int(miles)))
        
        # Формируем пакет: START | TYPE | MILES(2 байта) | CRC | END
        packet = struct.pack('<BH', PKT_MILES, miles)
        crc = self.calculate_crc(packet)
        full_packet = struct.pack('<B', START_BYTE) + packet + struct.pack('<BB', crc, END_BYTE)
        
        try:
            self.ser.write(full_packet)
            self.sent_packets += 1
            
            if self.debug and self.sent_packets % 100 == 0:
                print(f"[SEND] Мили: {miles} (пакет #{self.sent_packets})")
        except Exception as e:
            self.error_packets += 1
            if self.debug:
                print(f"✗ Ошибка отправки миль: {e}")
    
    def receive_buttons(self) -> ButtonState:
        """Получение состояния кнопок от STM32"""
        if not self.ser:
            return self.last_button_state
        
        try:
            # Читаем доступные данные
            if self.ser.in_waiting > 0:
                bytes_to_read = min(self.ser.in_waiting, 128)
                self.packet_buffer += self.ser.read(bytes_to_read)
                
                # Ограничение размера буфера
                if len(self.packet_buffer) > 512:
                    self.packet_buffer = self.packet_buffer[-256:]
            
            # Обрабатываем пакеты
            while len(self.packet_buffer) >= 6:
                # Ищем начало пакета
                start_pos = self.packet_buffer.find(bytes([START_BYTE]))
                
                if start_pos == -1:
                    self.packet_buffer = b''
                    break
                
                # Удаляем всё до стартового байта
                if start_pos > 0:
                    self.packet_buffer = self.packet_buffer[start_pos:]
                
                # Проверяем минимальный размер пакета (6 байт)
                if len(self.packet_buffer) < 6:
                    break
                
                # Ищем конечный байт
                end_pos = self.packet_buffer.find(bytes([END_BYTE]), 1)
                
                if end_pos == -1:
                    # Если не нашли END_BYTE, ждём больше данных
                    if len(self.packet_buffer) > 20:
                        # Слишком длинный пакет - сбрасываем
                        self.packet_buffer = self.packet_buffer[1:]
                    break
                
                # Извлекаем полный пакет
                packet_data = self.packet_buffer[:end_pos + 1]
                self.packet_buffer = self.packet_buffer[end_pos + 1:]
                
                # Проверка размера (должно быть ровно 6 байт)
                test = len(packet_data)
                if len(packet_data) != 7:
                    continue
                
                # Проверка CRC
                crc_received = packet_data[-2]
                crc_calculated = self.calculate_crc(packet_data[1:-2])
                
                if crc_received != crc_calculated:
                    self.error_packets += 1
                    if self.debug:
                        print(f"✗ CRC error: calc={crc_calculated:02X}, recv={crc_received:02X}")
                    continue
                
                # Проверка типа пакета
                if packet_data[1] != PKT_BUTTONS:
                    continue
                
                # Распаковка данных кнопок
                left = bool(packet_data[2])
                right = bool(packet_data[3])
                fire = bool(packet_data[4])
                
                self.received_packets += 1
                self.last_button_state = ButtonState(left, right, fire)
                
                if self.debug and self.received_packets % 100 == 0:
                    print(f"[RECV] Кнопки: L={left} R={right} F={fire} (пакет #{self.received_packets})")
            
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
        if self.received_packets > 0:
            success_rate = (self.received_packets / max(1, self.sent_packets)) * 100
            print(f"Успешность: {success_rate:.1f}%")
        print("==================================\n")