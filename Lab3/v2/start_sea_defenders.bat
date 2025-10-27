@echo off
echo Sea Defenders Server - Windows
echo =============================
echo.

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Ошибка: Python не найден!
    echo Установите Python с https://python.org
    pause
    exit /b 1
)

REM Проверяем наличие pyserial
python -c "import serial" >nul 2>&1
if errorlevel 1 (
    echo Установка pyserial...
    pip install pyserial
)

echo Запуск Sea Defenders Server...
echo Порт: COM5 (измените если нужно)
echo.
echo Управление:
echo - Сервер автоматически генерирует ландшафт
echo - Нажмите Ctrl+C для остановки
echo.

python sea_defenders_server_simple.py COM5

echo.
echo Сервер остановлен.
pause
