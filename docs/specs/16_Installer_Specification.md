# VabaxOS — Installer Specification

| Campo | Valore |
|---|---|
| ID | VABAX-DOC-16 |
| Versione | 0.1.0 |
| Stato | Bozza — Calamares o installer dedicato non deciso |
| Data | 2026-09-23 |
| Dipendenze | DOC-03, DOC-04, DOC-05, DOC-06, DOC-10, DOC-11, DOC-12 |

## 1. Scopo e gate

Definisce il flusso per installare VabaxOS autonomamente e in sicurezza. La roadmap v0.1 richiede configurazione iniziale accessibile e desktop, mentre installer completo arriva come milestone v0.5. La specifica copre il target finale senza pretendere che la prima ISO includa già partizionamento distruttivo.

## 2. Flusso previsto

Boot live → lingua/accessibilità prima della UI → accesso demo/sessione o installa → rete opzionale → destinazione disco e layout → cifratura opzionale/decisione → fuso orario → utente/credenziali → riepilogo leggibile → conferma esplicita scritture → installazione con progresso → bootloader → completamento/reboot → primo boot parlante.

Offline install e install da immagine locale sono da considerare. Wi-Fi deve poter essere configurato da tastiera; password non ripetuta in chiaro nello screen reader/log.

## 3. Sicurezza dati e requisito di accessibilità

- Nessuna modifica irreversibile prima di riepilogo e conferma chiara, operabile da tastiera/AT.
- Identificare dischi con modello/capacità e label, evitando solo icone/colore.
- Presentare partizioni e azioni con semantica tabellare navigabile; annunciare unità.
- Conferme distruttive distinguono disco e partizioni; offrire annulla.
- Mostrare stato/progresso e fase; errori spiegano recovery e preservazione dati.
- Installer e privilegi devono essere separati; non esporre shell root accidentalmente.
- Cifratura e secure boot possono rendere più complesso recovery/AT: non abilitarli senza flusso testato.

## 4. Requisiti

| ID | Requisito verificabile |
|---|---|
| INS-001 | Installer completo dall'avvio alla conclusione utilizzabile senza vista e senza rete, salvo step opzionali. |
| INS-002 | Lingua, layout tastiera e avvio AT sono selezionabili prima di operazioni disco. |
| INS-003 | Layout live preview e install target sono distinti; conferma mostra il target letteralmente. |
| INS-004 | Errore o perdita alimentazione produce stato noto e recovery; ripetizione non corrompe target senza avviso. |
| INS-005 | Log non include password, chiavi o contenuto utente; export log richiede consenso. |
| INS-006 | Installazione VM/UEFI e install su almeno hardware compatibili della matrice superano smoke test. |
| INS-007 | Aggiornamenti del sistema installato sono separati dall'installer e non obbligano reinstallazione per update ordinari. |

## 5. Alternative

Calamares è candidato modulare citato dalla roadmap; va sottoposto a audit accessibilità completa. Alternativa: frontend/installer Vabax dedicato, costo/manutenzione da stimare. Riutilizzare moduli upstream se le interfacce e il modello disco sono testabili e accessibili. Decisione prima del milestone v0.5, con prototipo tastiera/AT e test dischi VM.

## 6. Test e accettazione

VM con disco vuoto, disco con dati di prova, più dischi, spazio insufficiente, rete assente, TTS non disponibile, annullamento, errore a metà, reboot e reinstall/repair. Nessuna prova iniziale su PC utente con dati reali. Test con persone cieche per flusso completo e review partizionamento. Release installer bloccata da qualunque operazione distruttiva non annunciata/confermabile o flusso A0 irraggiungibile.

## 7. Decisioni aperte

Framework; partizionamento manuale/automatico; default ext4 (roadmap preliminare) o alternative; LUKS2; bootloader; secure boot; offline sources; account admin; OEM install; riparazione; requisiti dual boot; lingue e voci incluse.

## Riferimenti

- [Calamares User Guide](https://calamares.io/docs/users-guide/)
- [Debian installation documentation](https://www.debian.org/releases/stable/installmanual)
- [Linux kernel firmware and storage documentation](https://docs.kernel.org/)
- [AT-SPI2 developer guide](https://gnome.pages.gitlab.gnome.org/at-spi2-core/devel-docs/index.html)

## Cronologia

- 0.1.0 — 2026-09-23: specifica iniziale, installer non scelto.
