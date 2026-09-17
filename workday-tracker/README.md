# WorkDay Tracker

Windows asztali alkalmazás a napi munkavégzési státusz (iroda / home office /
szabadság / betegszabadság / ünnepnap) és a napokhoz fűzött üzenetek
nyilvántartására.

## Telepítés (fejlesztői környezet)

Előfeltétel: Python 3.12 telepítve (`py -3.12` elérhető a parancssorból).

```bat
setup_env.bat
```

Ez létrehozza a `.venv` virtuális környezetet, és telepíti a
`requirements.txt`-ben felsorolt függőségeket (PySide6, PyInstaller, pytest).

## Fejlesztői futtatás

```bat
run_dev.bat
```

Ez aktiválja a `.venv`-et, és elindítja az alkalmazást forrásból
(`python -m workday_tracker`).

## Tesztek futtatása

```bat
.venv\Scripts\activate.bat
pytest
```

## Build (EXE készítése)

```bat
build.bat
```

Ez törli a korábbi `build/` és `dist/` mappákat, majd lefuttatja a
PyInstaller-t a `workday_tracker.spec` alapján. A kész, egyfájlos,
konzolablak nélküli EXE a `dist\WorkDayTracker.exe` helyen jön létre.

## Adatfájlok helye

Az alkalmazás alapértelmezés szerint az EXE (vagy fejlesztéskor a projekt
gyökér) könyvtárába menti az adatait, három JSON fájlba:

- `startreminder_calendar.json` — a napok státuszai
- `startreminder_messages.json` — a napi üzenetek
- `startreminder_settings.json` — a beállítások

Ha ez a könyvtár nem írható (pl. `Program Files` alá van telepítve
rendszergazdai jog nélkül), az alkalmazás automatikusan átvált a
`%LOCALAPPDATA%\WorkDayTracker` mappára. A ténylegesen használt könyvtár
elérési útja mindig megtekinthető a **Beállítások → Adatok helye** részben.

Hibák és figyelmeztetések a `workday_tracker.log` fájlba kerülnek, ugyanabba
a könyvtárba, ahol a JSON adatfájlok is vannak.

## Biztonsági mentés készítése

Másold ki a fenti három JSON fájlt (és opcionálisan a log fájlt) egy
biztonságos helyre. Mivel minden mentés atomikus (ideiglenes fájlba írás,
majd átnevezés), a fájlok másolása futó alkalmazás mellett is biztonságos.

```bat
copy startreminder_calendar.json  C:\Mentesek\
copy startreminder_messages.json  C:\Mentesek\
copy startreminder_settings.json  C:\Mentesek\
```

## Adatok átvitele másik gépre

1. Zárd be az alkalmazást a régi gépen.
2. Másold át a három `startreminder_*.json` fájlt az EXE mellé (vagy a
   `%LOCALAPPDATA%\WorkDayTracker` mappába) az új gépen.
3. Indítsd el az alkalmazást az új gépen — automatikusan betölti az átvitt
   adatokat.

Ha a `startreminder_settings.json` fájlt is átviszed, az autostart
jelölőnégyzet állapota nem követi automatikusan a fájlt, mivel az mindig a
Windows registry aktuális állapotát mutatja — ezt a Beállítások ablakban
külön be/ki kell kapcsolni az új gépen.

## Billentyűparancsok

- `Tab` / `Shift+Tab` — mozgás a mezők között
- `Esc` — párbeszédablak bezárása mentés nélkül
- `Ctrl+S` — mentés az üzenetszerkesztőben
- `Ctrl+N` — új üzenet a főablakból
