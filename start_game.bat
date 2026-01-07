@echo off
chcp 65001 >nul
title Морський бій — запуск гри

echo Перевірка файлів...
if not exist "battleship_gui.py" (
    echo Не знайдено battleship_gui.py
    pause
    exit /b
)
if not exist "battleship_backend.exe" (
    echo Не знайдено battleship_backend.exe
    pause
    exit /b
)

echo Запуск гри...
where python >nul 2>&1
if %errorlevel%==0 (
    start "Морський бій" cmd /k "python battleship_gui.py & echo. & echo Гру закінчено. Натисни будь-яку клавішу... & pause >nul"
) else (
    where python3 >nul 2>&1
    if %errorlevel%==0 (
        start "Морський бій" cmd /k "python3 battleship_gui.py & echo. & echo Гру закінчено. Натисни будь-яку клавішу... & pause >nul"
    ) else (
        echo Python не знайдено. Встанови Python і запусти ще раз.
        pause
        exit /b
    )
)

echo Гра запущена у новому вікні.
pause
