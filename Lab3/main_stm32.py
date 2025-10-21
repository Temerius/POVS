"""
main_stm32.py
Главный файл для работы с STM32
Принимает данные от STM32 и отправляет команды спавна врагов
"""

import pygame
import serial
import threading
import time
import random
from stm32_game_view import STM32GameView
from protocol import GameStatePacket, DebugPacket, SpawnEnemyPacket, CommandPacket, START_BYTE, END_BYTE, PACKET_DEBUG, PACKET_GAME_STATE, PACKET_MENU_STATE, MenuStatePacket, PACKET_EXPLOSION

class STM32GameController:
    """Контроллер связи с STM32"""
    
    def __init__(self, port='COM3', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.running = False
        
        self.latest_packet = None
        self.latest_menu = None
        self.packet_lock = threading.Lock()
        
        self.spawn_timer = 0.0
        self.spawn_interval = 2.0
        
        # Буфер приёма
        self.rx_buffer = bytearray()
        
    def connect(self):
        """Подключиться к STM32"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.01
            )
            print(f"✓ Connected to {self.port}")
            return True
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
            
    def start(self):
        """Запустить потоки"""
        self.running = True
        
        self.rx_thread = threading.Thread(target=self._receiver_thread, daemon=True)
        self.tx_thread = threading.Thread(target=self._spawner_thread, daemon=True)
        
        self.rx_thread.start()
        self.tx_thread.start()
        
        print("✓ Threads started")
        
    def stop(self):
        """Остановить потоки"""
        self.running = False
        time.sleep(0.1)
        if self.ser:
            self.ser.close()
        print("✓ Disconnected")
        
    def get_latest_packet(self):
        """Получить последний пакет от STM32"""
        with self.packet_lock:
            return self.latest_packet
        
    def get_latest_menu(self):  
        with self.packet_lock:
            return self.latest_menu
            
    def _receiver_thread(self):
        """Поток приёма данных от STM32"""
        print("📡 RX Thread started")
        
        while self.running:
            try:
                if self.ser.in_waiting > 0:
                    data = self.ser.read(self.ser.in_waiting)
                    self.rx_buffer.extend(data)
                    
                    # Ищем пакеты
                    self._parse_packets()
                    
            except Exception as e:
                if self.running:
                    print(f"❌ RX Error: {e}")
                break
                
            time.sleep(0.001)
            
    def _parse_packets(self):
        """Парсинг пакетов из буфера"""
        while len(self.rx_buffer) >= 4:
            # Ищем START_BYTE
            start_idx = -1
            for i in range(len(self.rx_buffer)):
                if self.rx_buffer[i] == START_BYTE:
                    start_idx = i
                    break

            if start_idx == -1:
                self.rx_buffer.clear()
                return

            # Удаляем мусор до START
            if start_idx > 0:
                self.rx_buffer = self.rx_buffer[start_idx:]

            # Ищем END_BYTE
            end_idx = -1
            for i in range(1, len(self.rx_buffer)):
                if self.rx_buffer[i] == END_BYTE:
                    end_idx = i
                    break

            if end_idx == -1:
                if len(self.rx_buffer) > 256:
                    self.rx_buffer = self.rx_buffer[1:]
                return

            # Извлекаем пакет
            packet_data = bytes(self.rx_buffer[:end_idx + 1])
            self.rx_buffer = self.rx_buffer[end_idx + 1:]

            # Определяем тип пакета и парсим нужным парсером
            packet_type = packet_data[1]

            if packet_type == PACKET_GAME_STATE:
                packet = GameStatePacket.parse(packet_data)
                if packet:
                    with self.packet_lock:
                        self.latest_packet = packet
                else:
                    print(f"⚠ Invalid GAME packet: {[hex(b) for b in packet_data]}")

            elif packet_type == PACKET_MENU_STATE:
                packet = MenuStatePacket.parse(packet_data)
                if packet:
                    with self.packet_lock:
                        self.latest_menu = packet  
                else:
                    print(f"⚠ Invalid MENU packet: {[hex(b) for b in packet_data]}")

            elif packet_type == PACKET_DEBUG:
                message = DebugPacket.parse(packet_data)
                if message is not None:
                    print(f"[STM32 DEBUG] {message}")
                else:
                    print(f"⚠ Invalid DEBUG packet: {[hex(b) for b in packet_data]}")

            elif packet_type == PACKET_EXPLOSION:
                # Можно добавить ExplosionPacket.parse(), если нужно
                # Пока просто игнорируем или логируем
                print(f"[EXPLOSION] Raw: {[hex(b) for b in packet_data]}")

            else:
                print(f"⚠ Unknown packet type: 0x{packet_type:02X}, data: {[hex(b) for b in packet_data]}")

    def _spawner_thread(self):
        """Поток генерации и отправки врагов"""
        print("📤 TX Spawner started")
        
        # Даём время на инициализацию
        time.sleep(2.0)
        
        # Отправляем команду старта игры
        self._send_packet(CommandPacket.start_game())
        print("→ START_GAME sent")
        
        while self.running:
            try:
                time.sleep(self.spawn_interval)
                
                # Генерируем случайного врага
                x = random.randint(50, 750)
                enemy_type = random.choice([0, 1])  # 0=asteroid, 1=ship
                vx = random.uniform(-1.0, 1.0)
                vy = random.uniform(1.5, 3.0)
                
                packet = SpawnEnemyPacket(x, enemy_type, vx, vy)
                self._send_packet(packet.encode())
                
                print(f"→ SPAWN_ENEMY: x={x}, type={enemy_type}, v=({vx:.1f}, {vy:.1f})")
                
            except Exception as e:
                if self.running:
                    print(f"❌ TX Error: {e}")
                break
                
    def _send_packet(self, data):
        """Отправить пакет на STM32"""
        if self.ser and self.ser.is_open:
            self.ser.write(data)

def main():
    PORT = 'COM5'  # Измени на свой порт!
    
    print("=" * 60)
    print("Space Defender - STM32 Mode")
    print("=" * 60)
    print(f"Port: {PORT}")
    print(f"Baudrate: 115200")
    print()
    print("STM32 controls game logic")
    print("PC only visualizes and spawns enemies")
    print()
    print("Press ESC to quit")
    print("=" * 60)
    
    # Инициализация
    controller = STM32GameController(PORT)
    view = STM32GameView(800, 600)
    
    if not controller.connect():
        print("\n⚠ Failed to connect to STM32")
        print("Check:")
        print("  1. Correct COM port")
        print("  2. STM32 is powered and programmed")
        print("  3. USB cable is connected")
        return
        
    controller.start()
    
    # Главный цикл
    running = True
    
    try:
        while running:
            dt = view.clock.tick(60) / 1000.0
            
            # События
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                        
            # Получаем данные от STM32
            game_packet = controller.get_latest_packet()
            menu_packet = controller.get_latest_menu()

            # Отрисовка: сначала игра, потом меню (если нет игры)
            if game_packet:
                view.render(packet=game_packet)
            elif menu_packet:
                view.render(menu=menu_packet)
            else:
                view.render()  # waiting screen 

            
    except KeyboardInterrupt:
        print("\n⚠ Interrupted by user")
        
    finally:
        controller.stop()
        pygame.quit()
        print("✓ Shutdown complete")

if __name__ == "__main__":
    main()