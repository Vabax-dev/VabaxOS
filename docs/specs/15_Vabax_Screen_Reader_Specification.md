# VabaxOS — Vabax Screen Reader Specification

| Campo | Valore |
|---|---|
| ID | VABAX-DOC-15 |
| Versione | 0.1.0 |
| Stato | Specifica di prodotto in bozza — Orca è previsto inizialmente dalla roadmap |
| Data | 2026-09-23 |
| Dipendenze | DOC-03, DOC-05, DOC-14, DOC-16, DOC-17 |

## 1. Obiettivo e percorso

La roadmap richiede Orca come tecnologia di riferimento iniziale per v0.1 con avvio automatico e AT-SPI, mentre un Vabax Screen Reader può evolvere in seguito. Non è deciso se personalizzare/forkare Orca o scrivere un nuovo lettore. NVDA è riferimento funzionale, non portabile direttamente perché dipende fortemente dalle API Windows. La specifica guida il prodotto e non presuppone un'implementazione.

## 2. Ambito funzionale

- speech output; lingua/voce/velocità/volume/separazione modalità; pronuncia e dizionari;
- focus navigation e reading navigation; testo, controlli, link, liste, menu, tabelle, documenti;
- notifiche, dialoghi, errori, progressi e annunci con priorità e interruzione controllate;
- shortcut consistenti, modalità browse/focus se utile, cursore virtuale solo quando semantica applicazione lo permette;
- supporto Braille e input Braille secondo dispositivi testati;
- app web/browser, terminale, desktop shell, installazione/login e recovery;
- log e modalità debug che oscurano testo sensibile.

OCR, immagini, scripting/add-on, game overlays e AI description sono funzioni future: richiedono decisioni di privacy, sicurezza, prestazioni e test separati.

## 3. Requisiti di comportamento

| ID | Requisito |
|---|---|
| SR-001 | V0.1 parte senza rete e vocalizza l'accesso alla configurazione e desktop con hardware audio supportato. |
| SR-002 | Legge nome, ruolo, stato e valore correttamente; aggiornamenti dinamici non sono persi né annunciati in modo incontrollato. |
| SR-003 | Shortcut sono scopribili, rimappabili, documentati e non rubano input senza spiegazione. |
| SR-004 | Speech queue supporta priorità, interruzione, flush e feedback di mute/volume. |
| SR-005 | Cambio finestra/dialogo mantiene focus e contesto di lettura; l'utente può ritornare. |
| SR-006 | Motore/voce, lingua, rate e output audio sono selezionabili indipendentemente dalla lingua UI, se disponibili. |
| SR-007 | Arresto/crash/uscita audio hanno recovery accessibile e non bloccano input globale. |
| SR-008 | Il lettore non verbalizza password o campi sensibili senza policy esplicita. |
| SR-009 | Modalità di navigazione e stato corrente sono percepibili e salvaguardano la digitazione. |

## 4. Prestazioni, accessibilità e compatibilità

Definire target misurabili di latenza, memoria e CPU dopo baseline hardware. Offline speech fallback è richiesto dalla roadmap; dimensione ISO e qualità voce sono trade-off TBD. Testare combinazioni sessione Wayland/XWayland, AT-SPI, toolkit GTK/Qt, browser e input. Annunci possono essere diversi per lingue grammaticali differenti; non concatenare frasi localizzate con ordine inglese hard-coded.

## 5. Architettura candidata

Client AT → AT-SPI2 → screen reader → speech dispatcher/engine, audio stack e Braille service. Orca è il candidato iniziale indicato dalla roadmap; eSpeak NG fallback e TTS locale neurale sono candidati, soggetti a compatibilità, manutenzione e licenza modelli/voce. Definire integrazione, profili Vabax e shortcut in ADR; non mantenere fork diverging senza upstream plan.

## 6. Test e accettazione

V0.1: prove offline da boot in QEMU e PC fisico; annuncio iniziale, scelta/configurazione, login/sessione, navigazione finestre, terminale, file manager, impostazioni, spegnimento/riavvio, errore AT/audio. Per v1.0, tutti i flussi DOC-05 e combinazioni dichiarate nella matrice compatibilità. Zero blocker A0; suite per pronuncia/localizzazione/Braille quando supportato.

## 7. Decisioni aperte

Orca packaging/fork vs implementazione nuova; speech API/dispatcher e motore; voci e licenze; shortcut default; browse/focus interaction; Braille tier; add-on model; supporto browser; telemetria crash.

## Riferimenti

- [Orca project documentation](https://help.gnome.org/orca/)
- [AT-SPI2 developer guide](https://gnome.pages.gitlab.gnome.org/at-spi2-core/devel-docs/index.html)
- [AT-SPI API](https://docs.gtk.org/atspi2/)
- [eSpeak NG](https://github.com/espeak-ng/espeak-ng)
- [NVDA source repository](https://github.com/nvaccess/nvda) — riferimento da studiare; licenza e API Windows da valutare prima di ogni riuso.

## Cronologia

- 0.1.0 — 2026-09-23: specifica iniziale; nessun screen reader Vabax implementato.
