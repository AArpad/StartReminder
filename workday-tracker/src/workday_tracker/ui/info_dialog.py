"""Info/about dialog: who built it and when, a short blurb, and detailed help."""

from __future__ import annotations

from PySide6.QtWidgets import QDialogButtonBox, QDialog, QTextBrowser, QVBoxLayout, QWidget

_INFO_MARKDOWN = """\
# WorkDay Tracker

**Készítette:** Claude Code (Anthropic AI) — Nagykékesi Árpád megbízásából és
igényei alapján, közös egyeztetéssel kialakítva.

**Készült:** 2026. szeptember 17–18.

**Verzió:** 1.0

---

## Mi ez a program?

A WorkDay Tracker egy asztali alkalmazás, amely segít nyomon követni, hogy az
egyes napokon hol dolgoztál (iroda, home office, szabadság, betegszabadság,
ünnepnap), havi statisztikát vezet ezekről, és lehetővé teszi, hogy rövid,
Markdown-formázott üzeneteket hagyj magadnak egy-egy jövőbeli napra.

---

## Részletes súgó

### Naptár

- A hónap címére kattintva egyből visszaugorhatsz a mai hónapra; a nyilakkal
  léphetsz hónapot előre/hátra.
- Kattints egy napra a státusz beállításához: választhatsz egész napos vagy
  délelőtt/délután bontású (félnapos) státuszt, vagy törölheted a rögzítést.
- A kocka háttérszíne mutatja a napi státuszt; félnapos bontásnál a kocka
  átlósan két színre oszlik.
- A mai nap kiemelt kerettel jelenik meg, a hétvégék halványabban.

### Havi összesítés

- Irodai / Home Office / Szabadság / Betegszabadság / Ünnepnap napok száma
  (a félnapok 0,5-ként számítanak).
- **Utazási napok**: minden nap, amikor akár csak fél napra is be kellett
  menni az irodába, egy egész napnak számít — hiszen az utazás megtörtént.
- **Rögzítetlen munkanapok**: azok a hétköznapok, amelyekhez még nincs
  megadva státusz.

### Üzenetek

- A jobb oldali listában dátum szerint látod az üzeneteket; a pipa jelzi,
  hogy az üzenet már megjelent-e neked induláskor.
- Kattints egy üzenetre az előnézetéhez, vagy használd a Szerkesztés /
  Törlés gombokat.
- Az „Új üzenet” gombbal (`Ctrl+N`) írhatsz üzenetet egy tetszőleges napra,
  Markdown formázással és élő előnézettel.
- Az eszköztár gombjaival (félkövér, dőlt, címsor, listák, idézet, kód,
  link) gyorsan formázhatod a szöveget.

### Napindító ablak

- Induláskor megjelenik, ha a mai nap státusza még nincs megadva, vagy ha
  van olvasatlan (be nem pipált) üzeneted a mai napra.
- Ha a nap már meg van határozva és az üzenet pipája be van jelölve, a
  program egyből a főablakot mutatja.

### Beállítások

- Automatikus indítás a Windowsszal.
- Téma (sötét / világos / rendszertől függő) és színvilág (alapértelmezett,
  Solarized, Nord, nagy kontraszt) — azonnal érvényesül.
- Ablakméret szerkesztése, valamint az adatok tárolási helyének megtekintése.

### Billentyűparancsok

- `Ctrl+N` — új üzenet
- `Ctrl+S` — mentés az üzenetszerkesztőben
- `Esc` — párbeszédablak bezárása mentés nélkül
- `Tab` / `Shift+Tab` — mozgás a mezők között

### Adatok helye

- Az alkalmazás három JSON fájlban tárolja az adatokat (naptár, üzenetek,
  beállítások) az EXE mellett, vagy ha az a hely nem írható, a
  `%LOCALAPPDATA%\\WorkDayTracker` mappában.
- A pontos elérési út a Beállítások ablakban tekinthető meg.
"""


class InfoDialog(QDialog):
    """Shows who/when/what (short) and a detailed help text, markdown-rendered."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Információ")
        self.resize(560, 620)

        layout = QVBoxLayout(self)

        browser = QTextBrowser()
        browser.setOpenExternalLinks(False)
        browser.setMarkdown(_INFO_MARKDOWN)
        layout.addWidget(browser, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText("Bezárás")
        buttons.rejected.connect(self.accept)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
