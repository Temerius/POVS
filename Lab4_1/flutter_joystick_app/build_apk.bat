@echo off
echo Сборка APK для Android...
flutter build apk --release
echo.
echo APK собран! Файл находится в:
echo build\app\outputs\flutter-apk\app-release.apk
echo.
echo Скопируйте этот файл на телефон и установите.
pause

