import serial
import sys
import threading
import time
import random
from datetime import datetime

class STM32TwoWayComm:
    def __init__(self, port, baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.running = False
        self.rx_count = 0
        self.tx_count = 0
        
    def connect(self):
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.1
            )
            print(f"✓ Connected to {self.port}")
            return True
        except serial.SerialException as e:
            print(f"❌ Error: {e}")
            return False
    
    def send_number(self, number):
        """Отправляет число на STM32"""
        if self.ser and self.ser.is_open:
            # Отправляем как ASCII символ для чисел 0-9
            if 0 <= number <= 9:
                self.ser.write(chr(ord('0') + number).encode('utf-8'))
            # Для чисел 10-99 отправляем как байт
            else:
                self.ser.write(bytes([number]))
            
            self.tx_count += 1
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(f"[{timestamp}] TX #{self.tx_count}: Sent {number} to STM32")
    
    def receiver_thread(self):
        """Поток для приёма данных от STM32"""
        print("\n📡 RX Thread started\n")
        
        while self.running:
            try:
                if self.ser.in_waiting > 0:
                    data = self.ser.readline()
                    
                    try:
                        message = data.decode('utf-8', errors='ignore').strip()
                        
                        if message:
                            self.rx_count += 1
                            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                            print(f"[{timestamp}] RX #{self.rx_count}: {message}")
                            
                    except UnicodeDecodeError:
                        print(f"⚠ Decode error: {data.hex()}")
                        
            except Exception as e:
                if self.running:
                    print(f"❌ RX Error: {e}")
                break
            
            #time.sleep(0.01)  # Небольшая задержка
    
    def sender_thread(self):
        """Поток для отправки случайных чисел на STM32"""
        print("📤 TX Thread started\n")
        
        while self.running:
            try:
                # Генерируем случайное число от 0 до 99
                random_number = random.randint(0, 99)
                

                # Отправляем на STM32
                self.send_number(random_number)
                
                # Ждём 3 секунды перед следующей отправкой
                time.sleep(100)
                
            except Exception as e:
                if self.running:
                    print(f"❌ TX Error: {e}")
                break
    
    def run(self):
        """Запуск двусторонней связи"""
        self.running = True
        
        # Создаём два потока: для приёма и отправки
        rx_thread = threading.Thread(target=self.receiver_thread, daemon=True)
        tx_thread = threading.Thread(target=self.sender_thread, daemon=True)
        
        rx_thread.start()
        tx_thread.start()
        
        try:
            # Главный поток ожидает Ctrl+C
            while True:
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n\n" + "=" * 60)
            print("🛑 Stopping...")
            self.running = False
            
            # Ждём завершения потоков
            rx_thread.join(timeout=1)
            tx_thread.join(timeout=1)
            
            print(f"📊 Statistics:")
            print(f"   RX: {self.rx_count} messages received")
            print(f"   TX: {self.tx_count} numbers sent")
            
            if self.ser:
                self.ser.close()
            
            print("✓ Disconnected. Bye!")

def main():
    PORT = 'COM5'  # Измени на свой порт!
    
    print("=" * 60)
    print("STM32 Two-Way Communication Test")
    print("=" * 60)
    print(f"Port: {PORT}")
    print(f"Baudrate: 115200")
    print("\nMode:")
    print("  RX: Receiving messages from STM32")
    print("  TX: Sending random numbers (0-99) every 3 sec")
    print("\nPress Ctrl+C to exit")
    print("=" * 60)
    print()
    
    comm = STM32TwoWayComm(PORT)
    
    if comm.connect():
        time.sleep(1) 
        comm.run()
    else:
        print("\nПроверь:")
        print("1. Правильно ли указан COM-порт")
        print("2. Не занят ли порт другой программой")
        print("3. Подключена ли плата к компьютеру")
        sys.exit(1)

if __name__ == "__main__":
    main()