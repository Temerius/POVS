# Flutter Bluetooth Joystick App

Приложение для Android, которое подключается к джойстику через Bluetooth HC-05 и отображает данные, а также позволяет играть в простую игру.

## Формат данных

Приложение ожидает данные в формате:
```
X=0;Y=0;UP=0;RIGHT=0;LEFT=0;DOWN=0;E=0;F=0;JOYSTICK=0\r\n
```

Это точно такой же формат, как отправляет STM32.

## Установка

1. Убедитесь, что у вас установлен Flutter SDK
2. Перейдите в папку проекта:
   ```bash
   cd flutter_joystick_app
   ```
3. Установите зависимости:
   ```bash
   flutter pub get
   ```
4. Подключите Android устройство или запустите эмулятор
5. Запустите приложение:
   ```bash
   flutter run
   ```

## Настройка разрешений

В файле `android/app/src/main/AndroidManifest.xml` должны быть следующие разрешения:

```xml
<uses-permission android:name="android.permission.BLUETOOTH" />
<uses-permission android:name="android.permission.BLUETOOTH_ADMIN" />
<uses-permission android:name="android.permission.BLUETOOTH_CONNECT" />
<uses-permission android:name="android.permission.BLUETOOTH_SCAN" />
```

Для Android 12+ также нужны:
```xml
<uses-permission android:name="android.permission.BLUETOOTH_CONNECT" android:maxSdkVersion="30" />
<uses-permission android:name="android.permission.BLUETOOTH_SCAN" android:maxSdkVersion="30" />
```

## Использование

1. Откройте приложение
2. Включите Bluetooth, если он выключен
3. Выберите устройство HC-05 из списка сопряженных устройств
4. После подключения вы увидите:
   - Визуализацию джойстика (положение X, Y)
   - Состояние всех кнопок
   - Сырые данные

5. Нажмите иконку игры, чтобы запустить простую игру, где вы можете управлять персонажем джойстиком

## Функции

- Подключение к Bluetooth HC-05
- Парсинг данных джойстика в реальном времени
- Визуализация состояния джойстика и кнопок
- Простая игра для демонстрации управления

## Структура проекта

- `lib/main.dart` - Главный экран подключения Bluetooth
- `lib/joystick_screen.dart` - Экран отображения данных джойстика
- `lib/game_screen.dart` - Игровой экран
- `lib/joystick_data.dart` - Модель данных джойстика и парсер

