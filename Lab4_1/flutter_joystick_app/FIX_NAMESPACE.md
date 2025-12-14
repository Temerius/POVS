# Исправление проблемы с namespace для flutter_bluetooth_serial

После выполнения `flutter pub get`, нужно исправить файл плагина:

## Шаги:

1. Найти файл плагина (обычно здесь):
   ```
   C:\Users\<USERNAME>\.pub-cache\hosted\pub.dev\flutter_bluetooth_serial-0.4.0\android\build.gradle
   ```

2. Открыть файл `build.gradle` плагина и найти секцию `android {`

3. Добавить `namespace` ПЕРЕД закрывающей скобкой секции `android {`:
   ```gradle
   android {
       namespace = "it.matteocrippa.flutterbluetoothserial"
       // остальной код
   }
   ```

   Или если используется старый формат:
   ```gradle
   android {
       namespace "it.matteocrippa.flutterbluetoothserial"
       // остальной код
   }
   ```

4. Сохранить файл

5. Запустить `flutter run` снова

## Альтернативное решение (если не помогает):

Можно временно использовать более старую версию Gradle Plugin в `android/build.gradle.kts`:

```kotlin
dependencies {
    classpath("com.android.tools.build:gradle:7.4.2")
}
```

Но это не рекомендуется, лучше исправить namespace в плагине.

