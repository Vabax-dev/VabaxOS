# VabaxOS — Desktop Specification

| Campo | Valore |
|---|---|
| ID | VABAX-DOC-17 |
| Versione | 0.1.0 |
| Stato | Bozza prodotto — shell/desktop base TBD |
| Data | 2026-09-23 |
| Dipendenze | DOC-03, DOC-04, DOC-05, DOC-13, DOC-14, DOC-15 |

## 1. Scopo e confini

Definisce l'esperienza desktop VabaxOS: sessione, finestre, launcher, impostazioni, notifiche e strumenti essenziali. La roadmap lascia da decidere GNOME personalizzato o Wayland minimale e nomina GNOME/GTK, KDE/Qt o ambiente Vabax come alternative. Desktop proprietario completo non è presunto né requisito del prototipo.

## 2. Principi di esperienza

- First-run porta dal boot parlante a configurazione e desktop; layout accessibilità non richiede mouse.
- Nessuna azione essenziale nascosta in menu solo puntatore; shortcut scopribili e rimappabili.
- Stato di focus/finestra/workspace/notifica sempre esposto alle AT.
- Temi, font, contrasto, scala, animazioni e suoni hanno profili distinti e persistenti.
- TTS e notifiche non monopolizzano audio senza possibilità di controllo.
- Componenti standard e app GTK/Qt/X11 restano supportati nella misura dichiarata dalla matrice.

## 3. Superfici e requisiti

| Superficie | Capacità minima | Verifica |
|---|---|---|
| Session/login | selezione utente, sessione accessibile, lock/logout | tastiera, AT, recovery |
| Launcher/menu | ricerca, categorie, app installate, esito annunciato | navigazione solo tastiera |
| Finestre/workspaces | switch, minimize/maximize/fullscreen, snap | annuncio focus e ritorno |
| Notifiche | elenco, priorità, dismiss, quiet mode | AT, suono e persistenza |
| File manager | percorso, elenco, selezione, operazioni file | tastiera, AT, errori |
| Settings | rete, audio, display, accessibilità, input, privacy | impostazioni persistenti |
| System status | rete, volume, batteria, update e task | testo alternativo/semantica |
| Clipboard/drag | copy/paste e operazioni equivalenti | senza drag indispensabile |

Tutte le app incluse devono dichiarare limiti noti; terminale, file manager e settings sono parte del risultato v0.1 in forma minimale.

## 4. Layout tastiera e puntatore

Fornire comandi standard per app switch, launcher, overview, menu, chiusura finestra, workspace, focus navigation e pannelli; combinazioni esatte vanno user-testate e registrate. Mouse, touchpad e touch ampliano l'uso ma non sono requisiti per operazioni fondamentali. Sticky/Slow/Bounce Keys e rimappatura seguono DOC-05.

## 5. Architettura e alternative

Wayland/XWayland è indirizzo preliminare della roadmap; desktop iniziale è decisione da prendere: GNOME custom o sessione Wayland minimale. KDE/Qt e shell Vabax restano alternative da valutare per accessibilità, risorse, manutenzione, configurabilità, localizzazione e compatibilità. Costruire PoC con focus, AT-SPI, input, login e first-run prima di approvare.

## 6. Accettazione

Utente può avviare AT, navigare le superfici di base, aprire/switchare/chiudere finestre, configurare audio e rete, trovare app, gestire file e spegnere da tastiera. Nessun blocker A0; misurare RAM, CPU, tempo avvio e stabilità sulla configurazione di riferimento prima di affermare “leggero/veloce”. Testare app GTK, Qt e XWayland rappresentative.

## 7. Decisioni aperte

Desktop/compositor; GTK vs Qt; shell e display manager; pannello/launcher; sessione accessibile prima del login; temi; shortcut; default notifiche/audio; requisiti RAM/CPU; multi-monitor; touchscreen; accesso remoto.

## Riferimenti

- [Wayland protocol](https://wayland.freedesktop.org/docs/book/Protocol.html)
- [XDG Desktop Entry Specification](https://specifications.freedesktop.org/desktop-entry/latest/)
- [XDG Desktop Portals](https://docs.flatpak.org/en/latest/portal-api-reference.html)
- [GTK accessibility](https://docs.gtk.org/gtk4/section-accessibility.html)
- [AT-SPI API](https://docs.gtk.org/atspi2/)

## Cronologia

- 0.1.0 — 2026-09-23: bozza iniziale, desktop non selezionato.
