#!/usr/bin/env python3
"""Writes the key lists of the guide «I tasti di Orca» (docs/utente/tasti-orca.md)
from the key schemes of vabaxos-screen-reader, so the guide and the keys
never differ (tests/screen-reader/test_keys.py checks it).

    make-orca-keys-guide.py            print the tables
    make-orca-keys-guide.py --write    replace them in the guide
"""

import os
import re
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO, "packages", "vabaxos-screen-reader", "root", "usr", "lib", "python3",
                                "dist-packages"))
from vabaxos_screen_reader import keymaps  # noqa: E402

GUIDE = os.path.join(REPO, "docs", "utente", "tasti-orca.md")
START, END = "<!-- tabella dei tasti: inizio -->", "<!-- tabella dei tasti: fine -->"

# (section, [(command, what it does)]), in Italian.
SECTIONS = [
    ("Leggere", [
        ("sayAllHandler", "Leggi tutto, dal punto in cui sei"),
        ("reviewCurrentLineHandler", "Leggi la riga"),
        ("whereAmIBasicHandler", "Dove sono: il comando con il focus"),
        ("whereAmIDetailedHandler", "Dove sono, con più dettagli"),
        ("getTitleHandler", "Titolo della finestra"),
        ("flatReviewSayAllHandler", "Leggi tutta la finestra"),
        ("getStatusBarHandler", "Barra di stato"),
        ("presentTimeHandler", "Ora"),
        ("presentDateHandler", "Data"),
        ("present_clipboard_contents", "Contenuto degli appunti"),
        ("readCharAttributesHandler", "Formattazione del testo"),
        ("whereAmISelectionHandler", "Testo selezionato"),
        ("presentSizeAndPositionHandler", "Posizione e dimensione"),
        ("whereAmILinkHandler", "Indirizzo del collegamento"),
        ("present_battery_status", "Stato della batteria"),
        ("present_cpu_and_memory_usage", "Uso del processore e della memoria"),
        ("present_last_notification", "Ultima notifica"),
        ("show_notification_list", "Elenco delle notifiche"),
    ]),
    ("Elenchi, nelle pagine web e nei documenti", [
        ("linkShowList", "Elenco dei collegamenti"),
        ("headingShowList", "Elenco dei titoli"),
        ("formFieldShowList", "Elenco dei campi dei moduli"),
        ("buttonShowList", "Elenco dei pulsanti"),
        ("tableShowList", "Elenco delle tabelle"),
        ("landmarkShowList", "Elenco dei punti di riferimento"),
        ("listShowList", "Elenco degli elenchi"),
        ("imageShowList", "Elenco delle immagini"),
        ("radioButtonShowList", "Elenco dei pulsanti di opzione"),
        ("checkBoxShowList", "Elenco delle caselle di controllo"),
        ("comboBoxShowList", "Elenco delle caselle combinate"),
        ("entryShowList", "Elenco dei campi di testo"),
    ]),
    ("Tasti rapidi nelle pagine web (modalità navigazione; con Maiusc all'indietro)", [
        ("headingGoNext", "Titolo successivo"),
        ("headingGoNextLevel1Handler", "Titolo di livello 1 (da 1 a 6 per i livelli)"),
        ("linkGoNext", "Collegamento successivo"),
        ("unvisitedLinkGoNext", "Collegamento non visitato"),
        ("visitedLinkGoNext", "Collegamento visitato"),
        ("formFieldGoNext", "Campo del modulo successivo"),
        ("entryGoNext", "Campo di testo"),
        ("buttonGoNext", "Pulsante"),
        ("comboBoxGoNext", "Casella combinata"),
        ("checkBoxGoNext", "Casella di controllo"),
        ("radioButtonGoNext", "Pulsante di opzione"),
        ("tableGoNext", "Tabella"),
        ("listGoNext", "Elenco"),
        ("listItemGoNext", "Voce di elenco"),
        ("landmarkGoNext", "Punto di riferimento (intestazione, navigazione, contenuto principale)"),
        ("iframeGoNext", "Riquadro"),
        ("imageGoNext", "Immagine"),
        ("paragraphGoNext", "Paragrafo"),
        ("blockquoteGoNext", "Citazione"),
        ("separatorGoNext", "Separatore"),
        ("liveRegionGoNext", "Zona che si aggiorna da sola"),
    ]),
    ("Modalità e impostazioni", [
        ("togglePresentationModeHandler", "Modalità navigazione o modalità focus"),
        ("toggleStructuralNavigationHandler", "Cambia il tipo di tasti rapidi"),
        ("toggle_enabled", "Cursore di Orca o del programma, nelle pagine"),
        ("toggleSilenceSpeechHandler", "Voce spenta e accesa"),
        ("cycleKeyEchoHandler", "Eco dei tasti"),
        ("cycleSpeakingPunctuationLevelHandler", "Livello della punteggiatura"),
        ("cycleCapitalizationStyleHandler", "Come si dicono le maiuscole"),
        ("enterLearnModeHandler", "Aiuto dei tasti: ogni tasto dice cosa fa; Esc per uscire, F2 per l'elenco"),
        ("bypass_mode_toggle", "Passa i tasti al programma"),
        ("preferencesSettingsHandler", "Preferenze di Orca"),
        ("appPreferencesSettingsHandler", "Preferenze di Orca per il programma in uso"),
        ("cycleSettingsProfileHandler", "Profilo successivo"),
        ("shutdownHandler", "Chiudi Orca"),
    ]),
    ("Voce al volo", [
        ("increaseSpeechRateHandler", "Più veloce"),
        ("decreaseSpeechRateHandler", "Più lenta"),
        ("increaseSpeechVolumeHandler", "Più forte"),
        ("decreaseSpeechVolumeHandler", "Più piano"),
        ("increaseSpeechPitchHandler", "Tono più alto"),
        ("decreaseSpeechPitchHandler", "Tono più basso"),
    ]),
    ("Navigazione a oggetti (tastiera fissa)", [
        ("object_navigator_up", "Oggetto che contiene"),
        ("object_navigator_down", "Primo oggetto contenuto"),
        ("object_navigator_previous", "Oggetto precedente"),
        ("object_navigator_next", "Oggetto successivo"),
        ("object_navigator_perform_action", "Attiva l'oggetto"),
    ]),
    ("Segnalibri (sul portatile con Ins+Alt+parentesi)", [
        ("goToNextBookmark", "Segnalibro successivo"),
        ("goToPrevBookmark", "Segnalibro precedente"),
        ("goToBookmark", "Vai al segnalibro 1 (con i numeri da 1 a 6; Ins+Alt+numero lo aggiunge)"),
    ]),
]


def tables():
    nvda, jaws, orca = keymaps.overrides("nvda"), keymaps.overrides("jaws"), keymaps.defaults("desktop")
    effective_nvda = keymaps.effective(keymaps.entries("nvda"))
    effective_jaws = keymaps.effective(keymaps.entries("jaws"))
    lines = []
    for title, commands in SECTIONS:
        lines += [f"### {title}", ""]
        for name, text in commands:
            nv, ja, orig = (keymaps.label(keys.get(name)) for keys in (effective_nvda, effective_jaws, orca))
            same = "uguale in JAWS" if ja == nv else f"JAWS {ja}"
            lines.append(f"- **{text}:** {nv} ({same}; originale di Orca: {orig})")
        lines.append("")
    missing = [name for name in set(nvda) | set(jaws)
               if not any(name == n for _t, commands in SECTIONS for n, _x in commands)
               and not name.startswith(("review", "previous_")) and not name.endswith("GoPrevious")]
    if missing:
        raise SystemExit(f"commands of the schemes missing from the guide: {sorted(missing)}")
    return "\n".join(lines).rstrip() + "\n"


def main(argv):
    text = tables()
    if argv[1:] == ["--write"]:
        with open(GUIDE, encoding="utf-8") as f:
            guide = f.read()
        guide = re.sub(re.escape(START) + ".*?" + re.escape(END), START + "\n\n" + text + "\n" + END, guide,
                       flags=re.S)
        with open(GUIDE, "w", encoding="utf-8") as f:
            f.write(guide)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
