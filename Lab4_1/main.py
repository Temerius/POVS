import time
import serial
import serial.tools.list_ports
import vgamepad as vg

COM_PORT = "COM7"  
BAUD_RATE = 115200
DEBUG = True

DEADZONE = 8
INVERT_X = False
INVERT_Y = False
SWAP_AXES = False
CALIBRATION_SAMPLES = 20

offset_x = 0
offset_y = 0

def clamp(v, a, b):
    return max(a, min(b, v))

def apply_deadzone(value, deadzone):
    if abs(value) < deadzone:
        return 0
    if value > 0:
        return (value - deadzone) * 100 // (100 - deadzone)
    else:
        return (value + deadzone) * 100 // (100 - deadzone)

def map_percent_to_axis(value):
    value = clamp(value, -100, 100)
    return value / 100.0

def parse_line(line):
    out = {'X': 0, 'Y': 0}
    parts = line.strip().split(';')
    for p in parts:
        if '=' in p:
            try:
                k, v = p.split('=', 1)
                k = k.strip().upper()
                val = int(v.strip())
                if k in ['X', 'Y']:
                    out[k] = val
                else:
                    out[k] = 1 if val else 0
            except ValueError:
                pass
    return out

def is_data_line(line):
    return line.startswith('X=') and 'Y=' in line

def process_joystick(raw_x, raw_y):
    global offset_x, offset_y
    x = raw_x - offset_x
    y = raw_y - offset_y
    if SWAP_AXES:
        x, y = y, x
    if INVERT_X:
        x = -x
    if INVERT_Y:
        y = -y
    x = apply_deadzone(x, DEADZONE)
    y = apply_deadzone(y, DEADZONE)
    return x, y

try:
    ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
    print(f"[OK] Serial port {COM_PORT} opened")
except serial.SerialException as e:
    print(f"[ERROR] Failed to open {COM_PORT}: {e}")
    exit(1)

try:
    gamepad = vg.VX360Gamepad()
    print("[OK] Virtual Xbox gamepad created")
except Exception as e:
    print(f"[ERROR] Failed to create gamepad: {e}")
    ser.close()
    exit(1)

print()
print("[CALIBRATION] Don't touch the joystick!")
print(f"[CALIBRATION] Reading {CALIBRATION_SAMPLES} samples...")

cal_x = []
cal_y = []
cal_count = 0

while cal_count < CALIBRATION_SAMPLES:
    raw_bytes = ser.readline()
    if not raw_bytes:
        continue
    raw = raw_bytes.decode(errors='ignore').strip()
    if is_data_line(raw):
        data = parse_line(raw)
        cal_x.append(data['X'])
        cal_y.append(data['Y'])
        cal_count += 1
        print(f"  Sample {cal_count}/{CALIBRATION_SAMPLES}: X={data['X']:+4d}, Y={data['Y']:+4d}")

offset_x = sum(cal_x) // len(cal_x)
offset_y = sum(cal_y) // len(cal_y)

print()
print(f"[CALIBRATION] Center offset: X={offset_x:+d}, Y={offset_y:+d}")
print("[CALIBRATION] Done!")
print()
print(f"[SETTINGS] Deadzone: {DEADZONE}%")
print(f"[SETTINGS] Invert X: {INVERT_X}, Invert Y: {INVERT_Y}")
print("-" * 50)

BUTTON_MAP = {
    'JOYSTICK':  vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
    'E':         vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
    'F':         vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
    'UP':        vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
    'DOWN':      vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
    'LEFT':      vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
    'RIGHT':     vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
}

data_count = 0

try:
    while True:
        raw_bytes = ser.readline()
        if not raw_bytes:
            continue
        raw = raw_bytes.decode(errors='ignore').strip()
        if not raw:
            continue
        
        if is_data_line(raw):
            data_count += 1
            data = parse_line(raw)
            
            joy_x, joy_y = process_joystick(data['X'], data['Y'])
            fx = map_percent_to_axis(joy_x)
            fy = map_percent_to_axis(joy_y)
            gamepad.left_joystick_float(fx, fy)
            
            for key, btn in BUTTON_MAP.items():
                if data.get(key, 0):
                    gamepad.press_button(btn)
                else:
                    gamepad.release_button(btn)
            
            gamepad.update()
            
            if DEBUG and data_count % 1 == 0:
                print(f"X: {joy_x:+4d} | Y: {joy_y:+4d} | "
                      f"UP: {data.get('UP', 0)} | DOWN: {data.get('DOWN', 0)} | "
                      f"LEFT: {data.get('LEFT', 0)} | RIGHT: {data.get('RIGHT', 0)} | "
                      f"E: {data.get('E', 0)} | F: {data.get('F', 0)} | "
                      f"JOY: {data.get('JOYSTICK', 0)}")
        else:
            print(f"[STM32] {raw}")
        
        time.sleep(0.001)

except KeyboardInterrupt:
    print("\n[INFO] Exiting...")
    
finally:
    ser.close()
    gamepad.reset()
    print("[OK] Done!")