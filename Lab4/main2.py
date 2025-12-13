import time
import serial
import vgamepad as vg

COM_PORT = "COM6"
BAUD_RATE = 115200

gamepad = vg.VX360Gamepad()
ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)

def clamp(v, a, b):
    return max(a, min(b, v))

def map_percent_to_axis(value):
    value = clamp(value, -100, 100)
    return value / 100.0

def parse_line(line):
    out = {'x':0, 'y':0}
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

print(f"[INFO] Starting vgamepad on {COM_PORT} @ {BAUD_RATE} bps")

BUTTON_MAP = {
    'A': vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
    'B': vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
    'C': vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
    'D': vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
}
try:
    while True:
        raw = ser.readline().decode(errors='ignore').strip()
        if not raw:
            continue
        print(raw)
        data = parse_line(raw)
        x = data['x'] + 4
        y = data['y'] + 3
        fx = map_percent_to_axis(x)
        fy = map_percent_to_axis(y)
        gamepad.left_joystick_float(fx, fy)
        for key, btn in BUTTON_MAP.items():
            if data.get(key, 0):
                gamepad.press_button(btn)
            else:
                gamepad.release_button(btn)
        gamepad.update()

        time.sleep(0.01)
except KeyboardInterrupt:
    print("Exiting")
finally:
    ser.close()
    gamepad.reset()
