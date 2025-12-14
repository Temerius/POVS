// Модель данных джойстика
class JoystickData {
  int x;
  int y;
  bool up;
  bool right;
  bool left;
  bool down;
  bool e;
  bool f;
  bool joystickClick;

  JoystickData({
    this.x = 0,
    this.y = 0,
    this.up = false,
    this.right = false,
    this.left = false,
    this.down = false,
    this.e = false,
    this.f = false,
    this.joystickClick = false,
  });

  // Парсинг строки от STM32: "X=0;Y=0;UP=0;RIGHT=0;LEFT=0;DOWN=0;E=0;F=0;JOYSTICK=0\r\n"
  factory JoystickData.fromString(String data) {
    JoystickData joystick = JoystickData();

    List<String> parts = data.trim().split(';');
    for (String part in parts) {
      if (part.contains('=')) {
        List<String> keyValue = part.split('=');
        if (keyValue.length == 2) {
          String key = keyValue[0].trim().toUpperCase();
          String value = keyValue[1].trim();

          try {
            switch (key) {
              case 'X':
                joystick.x = int.parse(value);
                break;
              case 'Y':
                joystick.y = int.parse(value);
                break;
              case 'UP':
                joystick.up = value == '1';
                break;
              case 'RIGHT':
                joystick.right = value == '1';
                break;
              case 'LEFT':
                joystick.left = value == '1';
                break;
              case 'DOWN':
                joystick.down = value == '1';
                break;
              case 'E':
                joystick.e = value == '1';
                break;
              case 'F':
                joystick.f = value == '1';
                break;
              case 'JOYSTICK':
                joystick.joystickClick = value == '1';
                break;
            }
          } catch (e) {
            // Игнорируем ошибки парсинга
          }
        }
      }
    }

    return joystick;
  }

  @override
  String toString() {
    return 'X=$x;Y=$y;UP=${up ? 1 : 0};RIGHT=${right ? 1 : 0};LEFT=${left ? 1 : 0};DOWN=${down ? 1 : 0};E=${e ? 1 : 0};F=${f ? 1 : 0};JOYSTICK=${joystickClick ? 1 : 0}';
  }
}

