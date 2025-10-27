#!/usr/bin/env python3
"""
Sea Defenders Server
Генерирует ландшафт, врагов и управляет игрой
"""

import serial
import time
import random
import math
from protocol import *

class SeaDefendersServer:
    def __init__(self, port='COM3', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.game_running = False
        self.level = 1
        self.enemy_spawn_timer = 0
        self.enemy_spawn_interval = 120  # кадры между спавнами
        
        # Ландшафт
        self.islands = []
        self.whirlpools = []
        
        # Враги
        self.enemies = []
        
    def connect(self):
        """Подключение к STM32"""
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)
            print(f"Подключено к {self.port}")
            return True
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return False
    
    def disconnect(self):
        """Отключение от STM32"""
        if self.serial_conn:
            self.serial_conn.close()
            self.serial_conn = None
            print("Отключено")
    
    def generate_level_1(self):
        """Генерация 1-го уровня - только шлюпки и острова"""
        print("Генерация уровня 1...")
        
        # Очистка предыдущего ландшафта
        self.islands = []
        self.whirlpools = []
        
        # Создаем острова
        for i in range(8):
            island = {
                'x': random.randint(50, 750),
                'y': random.randint(100, 500),
                'size': random.randint(30, 60)
            }
            self.islands.append(island)
            
            # Отправляем остров на STM32
            if self.serial_conn:
                packet = SpawnIslandPacket(island['x'], island['y'], island['size'])
                self.serial_conn.write(packet.encode())
        
        # Отправляем острова на STM32 (если нужно)
        self.send_landscape_data()
    
    def generate_level_2(self):
        """Генерация 2-го уровня - добавляются галеоны"""
        print("Генерация уровня 2...")
        self.generate_level_1()  # Базовый ландшафт
        # Галеоны будут спавниться динамически
    
    def generate_level_3(self):
        """Генерация 3-го уровня - добавляются водовороты"""
        print("Генерация уровня 3...")
        self.generate_level_2()  # Базовый ландшафт + галеоны
        
        # Создаем водовороты
        for i in range(3):
            whirlpool = {
                'x': random.randint(100, 700),
                'y': random.randint(200, 400),
                'target_x': random.randint(100, 700),
                'target_y': random.randint(200, 400)
            }
            self.whirlpools.append(whirlpool)
            
            # Отправляем водоворот на STM32
            if self.serial_conn:
                packet = SpawnWhirlpoolPacket(whirlpool['x'], whirlpool['y'], 
                                            whirlpool['target_x'], whirlpool['target_y'])
                self.serial_conn.write(packet.encode())
    
    def send_landscape_data(self):
        """Отправка данных о ландшафте на STM32"""
        # В данной реализации ландшафт обрабатывается на PC
        # STM32 получает только игровые объекты
        pass
    
    def spawn_enemy(self, enemy_type=None):
        """Спавн врага"""
        if enemy_type is None:
            # Выбираем тип врага в зависимости от уровня
            if self.level == 1:
                enemy_type = 0  # Только шлюпки
            elif self.level == 2:
                enemy_type = random.choice([0, 1])  # Шлюпки и галеоны
            else:
                enemy_type = random.choice([0, 1])  # Шлюпки и галеоны
        
        # Позиция спавна
        x = random.randint(50, 750)
        
        # Скорость в зависимости от типа
        if enemy_type == 0:  # Шлюпка
            vx = random.randint(-3, 3)
            vy = random.randint(1, 3)
        else:  # Галеон
            vx = random.randint(-2, 2)
            vy = random.randint(1, 2)
        
        # Отправляем пакет спавна на STM32
        packet = SpawnEnemyPacket(x, enemy_type, vx, vy)
        if self.serial_conn:
            self.serial_conn.write(packet.encode())
            print(f"Спавн врага: тип={enemy_type}, x={x}, vx={vx}, vy={vy}")
    
    def spawn_treasure_chest(self):
        """Спавн сундука с сокровищами"""
        # Реализация сундуков с бонусами
        pass
    
    def update_game(self):
        """Обновление игровой логики"""
        if not self.game_running:
            return
        
        # Спавн врагов
        self.enemy_spawn_timer += 1
        if self.enemy_spawn_timer >= self.enemy_spawn_interval:
            self.spawn_enemy()
            self.enemy_spawn_timer = 0
            
            # Уменьшаем интервал спавна с уровнем
            self.enemy_spawn_interval = max(60, 120 - self.level * 10)
        
        # Спавн сундуков (редко)
        if random.randint(1, 1000) == 1:
            self.spawn_treasure_chest()
    
    def read_game_state(self):
        """Чтение состояния игры от STM32"""
        if not self.serial_conn:
            return None
        
        try:
            # Читаем данные от STM32
            data = self.serial_conn.read(256)
            if len(data) < 3:
                return None
            
            # Парсим пакеты
            packets = self.parse_packets(data)
            for packet in packets:
                if isinstance(packet, GameStatePacket):
                    return packet
                elif isinstance(packet, MenuStatePacket):
                    if packet.game_state == 1:  # GAME_PLAYING
                        self.game_running = True
                    else:
                        self.game_running = False
                        
        except Exception as e:
            print(f"Ошибка чтения: {e}")
        
        return None
    
    def parse_packets(self, data):
        """Парсинг пакетов из данных"""
        packets = []
        idx = 0
        
        while idx < len(data) - 2:
            if data[idx] == START_BYTE:
                # Ищем конец пакета
                end_idx = idx + 1
                while end_idx < len(data) and data[end_idx] != END_BYTE:
                    end_idx += 1
                
                if end_idx < len(data):
                    packet_data = data[idx:end_idx + 1]
                    
                    # Пытаемся распарсить пакет
                    if len(packet_data) > 2:
                        packet_type = packet_data[1]
                        
                        if packet_type == PACKET_GAME_STATE:
                            packet = GameStatePacket.parse(packet_data)
                            if packet:
                                packets.append(packet)
                        elif packet_type == PACKET_MENU_STATE:
                            packet = MenuStatePacket.parse(packet_data)
                            if packet:
                                packets.append(packet)
                    
                    idx = end_idx + 1
                else:
                    break
            else:
                idx += 1
        
        return packets
    
    def run(self):
        """Основной цикл игры"""
        if not self.connect():
            return
        
        print("Sea Defenders Server запущен!")
        print("Управление:")
        print("  SPACE - спавн врага")
        print("  1,2,3 - генерация уровней")
        print("  q - выход")
        
        try:
            while True:
                # Обновляем игру
                self.update_game()
                
                # Читаем состояние от STM32
                game_state = self.read_game_state()
                if game_state:
                    self.level = game_state.level
                
                # Обработка клавиатуры для Windows
                try:
                    import msvcrt
                    if msvcrt.kbhit():
                        key = msvcrt.getch().decode('utf-8').lower()
                        
                        if key == ' ':
                            self.spawn_enemy()
                        elif key == '1':
                            self.level = 1
                            self.generate_level_1()
                        elif key == '2':
                            self.level = 2
                            self.generate_level_2()
                        elif key == '3':
                            self.level = 3
                            self.generate_level_3()
                        elif key == 'q':
                            break
                except ImportError:
                    # Если msvcrt недоступен, пропускаем обработку клавиатуры
                    pass
                
                time.sleep(0.016)  # ~60 FPS
                
        except KeyboardInterrupt:
            print("\nОстановка сервера...")
        finally:
            self.disconnect()

if __name__ == "__main__":
    import sys
    
    port = 'COM5'  # Windows
    if len(sys.argv) > 1:
        port = sys.argv[1]
    
    server = SeaDefendersServer(port)
    server.run()
