@echo off
echo Sea Defenders - Тест подключения
echo ================================
echo.

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Ошибка: Python не найден!
    echo Установите Python с https://python.org
    pause
    exit /b 1
)

echo Открытие теста подключения...
echo.
echo Инструкции:
echo 1. Нажмите "Подключиться"
echo 2. Выберите COM порт (обычно COM5)
echo 3. Проверьте, что данные приходят от STM32
echo 4. Закройте браузер для выхода
echo.

start test_connection.html

echo Тест подключения открыт в браузере.
echo Нажмите любую клавишу для выхода...
pause >nul
