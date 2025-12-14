import time
import serial
import vgamepad as vg

COM_PORT = "COM7"
BAUD_RATE = 9600

gamepad = vg.VX360Gamepad()

# Попытка подключения с обработкой ошибок
try:
    ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
    print(f"[INFO] Подключено к {COM_PORT} @ {BAUD_RATE} bps")
except serial.SerialException as e:
    print(f"[ERROR] Не удалось подключиться к {COM_PORT}: {e}")
    print("[INFO] Проверьте:")
    print("  1. Правильность COM-порта (может быть COM3, COM4 и т.д.)")
    print("  2. Что Bluetooth адаптер подключен")
    print("  3. Что HC-05 сопряжен с компьютером")
    exit(1)

def clamp(v, a, b):
    return max(a, min(b, v))

def map_percent_to_axis(value):
    value = clamp(value, -100, 100)
    return value / 100.0

def parse_line(line):
    out = {'x': 0, 'y': 0, 'UP': 0, 'RIGHT': 0, 'LEFT': 0, 'DOWN': 0, 'E': 0, 'F': 0, 'JOYSTICK': 0}
    parts = line.strip().split(';')
    for p in parts:
        if '=' in p:
            k, v = p.split('=')
            k = k.strip().upper()
            try:
                val = int(v.strip())
            except:
                val = 0
            if k == 'X':
                out['x'] = val
            elif k == 'Y':
                out['y'] = val
            else:
                out[k] = 1 if val else 0
    return out

print(f"[INFO] Ожидание данных от джойстика...")
print(f"[INFO] Если данные не приходят, проверьте:")
print(f"  1. Что STM32 включен и работает")
print(f"  2. Что HC-05 мигает (подключен)")
print(f"  3. Правильность скорости передачи ({BAUD_RATE} бод)")

# Маппинг кнопок на Xbox контроллер
BUTTON_MAP = {
    'E': vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,      # E -> LB (Left Bumper)
    'F': vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,     # F -> RB (Right Bumper)
    'JOYSTICK': vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,  # Нажатие джойстика -> Left Stick Click
    'UP': vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,                 # UP -> Y
    'DOWN': vg.XUSB_BUTTON.XUSB_GAMEPAD_A,               # DOWN -> A
    'LEFT': vg.XUSB_BUTTON.XUSB_GAMEPAD_X,               # LEFT -> X
    'RIGHT': vg.XUSB_BUTTON.XUSB_GAMEPAD_B,              # RIGHT -> B
}

no_data_counter = 0
first_run = True

try:
    print(f"[INFO] Начинаем чтение данных...")
    print(f"[INFO] Проверка: порт открыт = {ser.is_open}")
    
    while True:
        # Читаем данные
        if ser.in_waiting > 0:
            raw_bytes = ser.readline()
            
            if raw_bytes and len(raw_bytes) > 0:
                try:
                    raw = raw_bytes.decode('utf-8', errors='ignore').strip()
                    print(f"[DATA] {raw}")
                except:
                    raw = raw_bytes.decode('latin-1', errors='ignore').strip()
                    print(f"[DATA] {raw}")
                
                if raw and len(raw) >= 5:
                    data = parse_line(raw)
        
        # Проверяем что данные корректны
        if 'x' not in data or 'y' not in data:
            print(f"[WARNING] Некорректный формат данных: {raw}")
            print(f"[WARNING] Parsed data: {data}")
            continue
        
        # Проверяем что данные корректны
        if 'x' in data and 'y' in data:
            # Джойстик (Left Stick)
            x = data['x'] + 4
            y = data['y'] + 3
            fx = map_percent_to_axis(x)
            fy = map_percent_to_axis(y)
            gamepad.left_joystick_float(fx, fy)
            
            # Все кнопки (E, F, JOYSTICK, UP, DOWN, LEFT, RIGHT)
            for key, btn in BUTTON_MAP.items():
                if data.get(key, 0):
                    gamepad.press_button(btn)
                else:
                    gamepad.release_button(btn)
            
            gamepad.update()
            no_data_counter = 0
        else:
            no_data_counter += 1
            if no_data_counter % 500 == 0:  # Каждые ~5 секунд
                print(f"[WARNING] Данные не поступают... (ждем {no_data_counter * 0.01:.1f} сек)")
        
        time.sleep(0.01)
except KeyboardInterrupt:
    print("\n[INFO] Остановка...")
except serial.SerialException as e:
    print(f"\n[ERROR] Ошибка связи: {e}")
except Exception as e:
    print(f"\n[ERROR] Неожиданная ошибка: {e}")
    import traceback
    traceback.print_exc()
finally:
    if ser.is_open:
        ser.close()
    gamepad.reset()
    print("[INFO] Подключение закрыто, контроллер сброшен")
