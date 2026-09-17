@echo off
setlocal enabledelayedexpansion

echo === WorkDay Tracker - fejlesztoi kornyezet letrehozasa ===

py -3.12 --version >nul 2>&1
if errorlevel 1 (
    echo HIBA: Nem talalhato a Python 3.12 telepites.
    echo Telepitsd a Python 3.12-t a https://www.python.org/downloads/ oldalrol,
    echo majd futtasd ujra ezt a szkriptet.
    pause
    exit /b 1
)

if not exist ".venv" (
    echo Virtualis kornyezet letrehozasa: .venv
    py -3.12 -m venv .venv
    if errorlevel 1 (
        echo HIBA: Nem sikerult letrehozni a virtualis kornyezetet.
        pause
        exit /b 1
    )
) else (
    echo A .venv mappa mar letezik, kihagyva.
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 (
    echo HIBA: Nem sikerult aktivalni a virtualis kornyezetet.
    pause
    exit /b 1
)

echo Pip frissitese...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo HIBA: A pip frissitese sikertelen volt.
    pause
    exit /b 1
)

echo Fuggosegek telepitese a requirements.txt alapjan...
pip install -r requirements.txt
if errorlevel 1 (
    echo HIBA: A fuggosegek telepitese sikertelen volt.
    pause
    exit /b 1
)

echo.
echo === Sikeres telepites! ===
echo A fejlesztoi futtatashoz hasznald a run_dev.bat szkriptet.
pause
endlocal
