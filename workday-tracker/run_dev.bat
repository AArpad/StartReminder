@echo off
setlocal

if not exist ".venv\Scripts\activate.bat" (
    echo HIBA: Nem talalhato a .venv virtualis kornyezet.
    echo Eloszor futtasd a setup_env.bat szkriptet.
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"
set "PYTHONPATH=%~dp0src;%PYTHONPATH%"
python -m workday_tracker

endlocal
