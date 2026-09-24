# VabaxOS — Development Standards

| Campo | Valore |
|---|---|
| ID | VABAX-DOC-08 |
| Versione | 0.1.0 |
| Stato | Bozza — standard proposti, da approvare |
| Data | 2026-09-23 |
| Dipendenze | DOC-01 roadmap, DOC-02 ambiente Windows, DOC-03 architettura, DOC-04 requisiti, DOC-07 QA |

## 1. Scopo e regole

Stabilisce un processo ripetibile per contributi umani e assistiti da AI. Il repository Git è la fonte canonica; nessuna implementazione deve contraddire una specifica approvata o introdurre decisioni architetturali silenziose. Gli standard linguaggio-specifici restano da selezionare quando il codice e la toolchain vengono fissati.

## 2. Repository e flusso Git

- Proteggere `main`; vietare push diretti salvo emergenza documentata.
- Usare branch brevi: `feature/VABAX-123-short-name`, `fix/...`, `docs/...`.
- Ogni change deve riferirsi a issue o requisito; una PR contiene motivazione, impatto, test, documentazione e decisioni/TBD.
- Commit piccoli e descrittivi; convenzione Conventional Commits è proposta e richiede approvazione.
- Richiedere review di almeno un maintainer diverso dall'autore appena il team consente; per prototipo personale, usare checklist di self-review esplicita.
- Merge solo dopo CI applicabile, review, conflitti risolti e migrazioni/rollback valutati.
- Tag release immutabili e firmati quando l'infrastruttura chiavi è approvata.

## 3. Codice, API e dipendenze

- Preferire upstream mantenuti invece di fork; ogni patch locale ha motivazione, upstream issue e piano di rimozione.
- Non aggiungere dipendenze senza necessità, licenza verificata, versione fissata e impatto su dimensione, accessibilità, sicurezza e build.
- API pubbliche richiedono semver o policy di compatibilità equivalente, documentazione, error model e test.
- C/C++, Rust, Python e shell sono disponibili nella guida di sviluppo; l'uso per sottosistema è TBD. Evitare di imporre CMake/Ninja quando upstream usa un sistema nativo.
- Segreti, token, dati personali e chiavi private non vanno nel repository, log o prompt esterni.
- Non inserire output generato se può essere riprodotto; annotare eccezioni, fonti e strumenti.

## 4. Documentazione, test e accessibilità

Ogni componente non banale documenta scopo, installazione, configurazione, API, errori, privilegi, logging e recovery. Ogni UI segue DOC-05; ogni test segue DOC-07. Modifiche a protocollo, dipendenze, privilegi, boot, update o licenza richiedono ADR o review specialistica. Le modifiche alle stringhe includono cataloghi traduzione e test overflow/localizzazione.

## 5. Tooling minimo proposto

Git, review via PR, formatter e linter per linguaggio, analisi dipendenze, test automatizzati, build riproducibile e CI sono richiesti come capacità; prodotti specifici sono TBD. La workstation di riferimento resta Windows 11 + WSL2/Ubuntu 24.04 + VS Code Remote WSL + QEMU come in DOC-02.

## 6. Definition of Done

Requisito/issue collegato; implementazione leggibile e reviewata; test pertinenti passati; test keyboard/AT per UI; documentazione e traduzioni aggiornate; dipendenze/licenze/inventario aggiornati; errori e logging adeguati; nessun segreto; limiti noti registrati. Le deroghe hanno owner, rischio e scadenza.

## 7. Decisioni aperte

Licenza del progetto, convenzione commit, policy branch/review, stack CI, formatter/linter, soglia copertura, linguaggi per sottosistema, policy versionamento API e modalità firma dei tag richiedono approvazione.

## Riferimenti

- [Documentazione Git](https://git-scm.com/doc)
- [Linux kernel development process](https://docs.kernel.org/process/)
- [systemd contribution guidelines](https://systemd.io/CONTRIBUTING/)
- [SPDX license identifiers](https://spdx.org/licenses/)

## Cronologia

- 0.1.0 — 2026-09-23: prima bozza.
