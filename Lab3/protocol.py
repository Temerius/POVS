"""
protocol.py
Протокол передачи данных между STM32 и PC
"""

import struct

# Константы протокола
START_BYTE = 0xAA
END_BYTE = 0x55

# Типы пакетов STM32 -> PC
PACKET_GAME_STATE = 0x01
PACKET_MENU_STATE = 0x02
PACKET_DEBUG = 0x03
PACKET_EXPLOSION = 0x04

# Типы пакетов PC -> STM32
PACKET_SPAWN_ENEMY = 0x10
PACKET_START_GAME = 0x11
PACKET_PAUSE_GAME = 0x12

# Лимиты
MAX_ENEMIES = 10
MAX_BULLETS = 10

def crc8(data):
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

class DebugPacket:
    """Пакет отладки STM32 -> PC"""
    
    @staticmethod
    def parse(data):
        """Распарсить debug пакет"""
        if len(data) < 4:
            return None
            
        if data[0] != START_BYTE or data[-1] != END_BYTE:
            return None
            
        if data[1] != PACKET_DEBUG:
            return None
            
        # Проверка CRC
        crc_calculated = crc8(data[1:-2])
        crc_received = data[-2]
        if crc_calculated != crc_received:
            return None
            
        # Извлекаем текст (между байтом типа и CRC)
        message = data[2:-2].decode('utf-8', errors='ignore')
        return message

class MenuStatePacket:
    """Пакет состояния меню STM32 -> PC"""
    
    def __init__(self):
        self.game_state = 0      # 0=MENU, 1=PLAYING, 2=PAUSED, 3=GAME_OVER
        self.selected_item = 0   # текущий выбранный пункт меню
        self.score = 0           # текущий счёт (для GAME_OVER)
        
    @staticmethod
    def parse(data):
        """Распарсить пакет меню из байтов"""
        print(data)
        if len(data) < 6:
            return None
            
        if data[0] != START_BYTE or data[-1] != END_BYTE:
            return None
            
        if data[1] != PACKET_MENU_STATE:
            return None
            
        
        crc_calculated = crc8(data[1:-2])
        crc_received = data[-2]
        if crc_calculated != crc_received:
            return None
            
        packet = MenuStatePacket()
        idx = 2
        
        packet.game_state = data[idx]
        idx += 1
        packet.selected_item = data[idx]
        idx += 1
        packet.score = (data[idx] << 8) | data[idx + 1]
        # idx += 2 — не используется дальше
        
        return packet
    
class GameStatePacket:
    """Пакет игрового состояния STM32 -> PC"""
    
    def __init__(self):
        self.player_x = 0
        self.player_y = 0
        self.player_hp = 100
        self.score = 0
        self.level = 1
        self.enemies = []  # [(x, y, type, hp), ...]
        self.bullets = []  # [(x, y), ...]
        self.enemy_bullets = []  # [(x, y), ...]
        
    @staticmethod
    def parse(data):
        """Распарсить пакет из байтов"""
        if len(data) < 6:
            return None
            
        if data[0] != START_BYTE or data[-1] != END_BYTE:
            return None
            
        if data[1] != PACKET_GAME_STATE:
            return None
            
        # Проверка CRC (пропускаем если проблемы)
        # crc_calculated = crc8(data[1:-2])
        # crc_received = data[-2]
        # if crc_calculated != crc_received:
        #     print(f"⚠ CRC mismatch: calc={crc_calculated:02X}, recv={crc_received:02X}")
        #     return None
            
        packet = GameStatePacket()
        idx = 2
        
        # Player
        packet.player_x = struct.unpack('>H', data[idx:idx+2])[0]
        idx += 2
        packet.player_y = struct.unpack('>H', data[idx:idx+2])[0]
        idx += 2
        packet.player_hp = data[idx]
        idx += 1
        packet.score = struct.unpack('>H', data[idx:idx+2])[0]
        idx += 2
        packet.level = data[idx]
        idx += 1
        
        # Enemies
        enemy_count = data[idx]
        idx += 1
        for _ in range(min(enemy_count, MAX_ENEMIES)):
            if idx + 6 > len(data) - 2:
                break
            ex = struct.unpack('>H', data[idx:idx+2])[0]
            idx += 2
            ey = struct.unpack('>H', data[idx:idx+2])[0]
            idx += 2
            etype = data[idx]
            idx += 1
            ehp = data[idx]
            idx += 1
            packet.enemies.append((ex, ey, etype, ehp))
            
        # Player bullets
        if idx < len(data) - 2:
            bullet_count = data[idx]
            idx += 1
            for _ in range(min(bullet_count, MAX_BULLETS)):
                if idx + 4 > len(data) - 2:
                    break
                bx = struct.unpack('>H', data[idx:idx+2])[0]
                idx += 2
                by = struct.unpack('>H', data[idx:idx+2])[0]
                idx += 2
                packet.bullets.append((bx, by))
                
        # Enemy bullets
        if idx < len(data) - 2:
            ebullet_count = data[idx]
            idx += 1
            for _ in range(min(ebullet_count, MAX_BULLETS)):
                if idx + 4 > len(data) - 2:
                    break
                bx = struct.unpack('>H', data[idx:idx+2])[0]
                idx += 2
                by = struct.unpack('>H', data[idx:idx+2])[0]
                idx += 2
                packet.enemy_bullets.append((bx, by))
                
        return packet

class SpawnEnemyPacket:
    """Пакет спавна врага PC -> STM32"""
    
    def __init__(self, x, enemy_type, velocity_x, velocity_y):
        self.x = x
        self.enemy_type = enemy_type
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        
    def encode(self):
        """Закодировать в байты"""
        data = bytearray()
        data.append(START_BYTE)
        data.append(PACKET_SPAWN_ENEMY)
        data.extend(struct.pack('>H', self.x))
        data.append(self.enemy_type)
        # Скорости как знаковые байты (-127..127) * 0.1
        vx_byte = int(self.velocity_x * 10) & 0xFF
        vy_byte = int(self.velocity_y * 10) & 0xFF
        data.append(vx_byte)
        data.append(vy_byte)
        data.append(crc8(data[1:]))
        data.append(END_BYTE)
        return bytes(data)

class CommandPacket:
    """Командные пакеты PC -> STM32"""
    
    @staticmethod
    def start_game():
        data = bytearray([START_BYTE, PACKET_START_GAME])
        data.append(crc8(data[1:]))
        data.append(END_BYTE)
        return bytes(data)
        
    @staticmethod
    def pause_game():
        data = bytearray([START_BYTE, PACKET_PAUSE_GAME])
        data.append(crc8(data[1:]))
        data.append(END_BYTE)
        return bytes(data)