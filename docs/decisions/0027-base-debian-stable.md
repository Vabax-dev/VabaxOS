# ADR-0027: Base di VabaxOS — Debian stable «trixie»

- **Stato:** Accettata (Vabax, 2026-09-27)
- **Data:** 2026-09-27
- **Responsabile:** Vabax (Project Lead)
- **Sostituisce:** [ADR-0017](0017-base-debian-testing-forky.md); torna alla scelta di [ADR-0001](0001-base-debian-trixie.md) anche per la serie 0.x

Decisione di Vabax (2026-09-27): «sono usciti troppi bug, e tu li puoi correggere, ma non possiamo creare un OS su una base instabile, perciò ricostruisci tutto quello fatto fin ora sull'ultima versione stabile di Debian. Le funzioni utili che sono nelle ultime versioni di testing magari le portiamo noi con estensioni o altre modifiche.»

## Contesto

Con ADR-0017 la serie 0.x si costruiva su Debian testing «forky» (GNOME 50, Orca 50). Le prove del gruppo di blocchi 13-15 hanno trovato difetti in programmi di testing che non sono di VabaxOS: GNOME Shell che si blocca all'avvio (GJS 1.88.1), speech-dispatcher che smette di parlare, il kernel e l'installer da prendere da Git, live-build che non costruisce l'installer. Ogni difetto si può correggere, ma una base che cambia ogni giorno ne porta di nuovi.

Debian 13 «trixie» è la versione stabile: il 2026-09-27 è alla 13.7, con correzioni di sicurezza e aggiornamenti per anni.

| Componente | forky (prima) | trixie 13.7 (ora) |
|---|---|---|
| GNOME Shell, Mutter | 50.5 | 48.7 |
| Orca | 50.2 | 48.1 |
| speech-dispatcher | 0.12.1 | 0.12.0 |
| GJS | 1.88.1 | 1.82.3 |
| PipeWire | 1.6 | 1.4.2 |
| systemd | 258 | 257 |
| kernel | 7.2 | 6.12 (LTS) |
| Firefox ESR | 140 | 140 |

## Decisione

1. VabaxOS si costruisce su **Debian 13 «trixie» stable**, con `trixie-security` e `trixie-updates`, a data fissa di snapshot.debian.org come prima (due costruzioni danno lo stesso sistema).
2. **Si porta tutto il lavoro fatto** (blocchi 1-15) sulla nuova base; ogni funzione deve funzionare come prima con la voce.
3. Le funzioni che ci sono solo in testing si portano **da VabaxOS**, con estensioni, programmi o correzioni piccole (ADR-0026), non cambiando la base. Per esempio:
   - Orca 48 tiene le impostazioni in un file JSON e non ha il servizio D-Bus di Orca 50: il programma «Impostazioni del lettore di schermo» (blocco 9) e gli schemi dei tasti (blocco 10) si riscrivono per Orca 48;
   - le estensioni di GNOME Shell di VabaxOS si adattano a GNOME 48;
   - i nomi dei pulsanti delle notifiche (ADR-0022) si controllano anche in GNOME 48.
4. L'installer è quello di trixie (niente più installer e kernel da Git).
5. I difetti trovati in testing si ricontrollano su trixie: la stessa prova (`tests/upstream/`) dice se ci sono ancora.

## Conseguenze

- Più stabilità e correzioni di sicurezza vere (`trixie-security`), che PackageKit riconosce.
- Versioni più vecchie di un anno: le novità di GNOME 49 e 50 e di Orca 49 e 50 arrivano solo se le portiamo noi.
- Lavoro di trasferimento, a blocchi come sempre, con una ISO completa e le prove con la voce alla fine.
- Da decidere con Vabax: se il sistema installato segue direttamente `trixie-security` (le correzioni di sicurezza arrivano subito), oppure resta a date controllate come dice ADR-0020.

## Alternative considerate

- **Restare su forky e correggere i difetti:** ogni settimana ne arrivano di nuovi.
- **trixie con i backports** (GNOME e Orca più nuovi): mescola di nuovo versioni non provate insieme.
