@echo off
setlocal

if not exist ".venv\Scripts\activate.bat" (
    echo HIBA: Nem talalhato a .venv virtualis kornyezet.
    echo Eloszor futtasd a setup_env.bat szkriptet.
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"

echo Korabbi build/ es dist/ mappak torlese...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo.
echo === PyInstaller build inditasa ===
set "PYTHONPATH=%~dp0src;%PYTHONPATH%"
python -m PyInstaller workday_tracker.spec --noconfirm
if errorlevel 1 (
    echo HIBA: A build sikertelen volt.
    pause
    exit /b 1
)

set "EXE_PATH=%~dp0dist\WorkDayTracker.exe"
if not exist "%EXE_PATH%" (
    echo HIBA: A varhato EXE fajl nem jott letre: %EXE_PATH%
    pause
    exit /b 1
)

for %%F in ("%EXE_PATH%") do set "EXE_SIZE=%%~zF"
set /a EXE_SIZE_MB=%EXE_SIZE% / 1048576

echo.
echo === Build kesz! ===
echo EXE eleresi ut: %EXE_PATH%
echo Meret: %EXE_SIZE% byte (kb. %EXE_SIZE_MB% MB)
pause
endlocal
