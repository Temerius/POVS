import serial

PORT = "COM9"
BAUDRATE = 38400   
ser = serial.Serial(PORT, BAUDRATE, timeout=1)

print(f"Открыт порт {PORT} со скоростью {BAUDRATE}")
print("Вводи AT‑команды. Для выхода набери 'exit'.")

while True:
    cmd = input(">>> ")
    if cmd.lower() == "exit":
        break

    
    ser.write((cmd + "\r\n").encode("utf-8"))

    response = b""
    while True:
        chunk = ser.read(ser.in_waiting or 1)
        if not chunk:
            break
        response += chunk

    if response:
        print("Ответ:", response.decode("utf-8", errors="ignore").strip())

ser.close()
