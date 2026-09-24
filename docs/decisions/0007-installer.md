# ADR-0007: Installer — Debian Installer con sintesi vocale

- **Stato:** Accettata
- **Data:** 2026-09-24
- **Responsabile:** Vabax (Project Lead)

## Contesto

La roadmap chiede di scegliere fra Calamares modificato e un installer VabaxOS dedicato (DOC-01 §26, punto 4). Il requisito critico della v0.5 è che **una persona cieca possa installare VabaxOS da sola** (DOC-01 §10).

## Decisione

- **Dalla v0.1 alla v0.4:** l'installazione usa il **Debian Installer** incluso nella ISO, con la **sintesi vocale** (voce del menu di avvio). Si installa senza vedere lo schermo: il supporto vocale viene attivato anche nel sistema installato.
- **Calamares non è l'installer predefinito.** È scritto in Qt e la sua accessibilità con Orca va dimostrata, non presunta. Si può fare un audit, ma non blocca niente.
- **Alla v0.5** si decide, con un prototipo e test con utenti ciechi, se serve un **installer Vabax** (per esempio un'interfaccia GTK 4 sopra gli stessi strumenti di partizionamento).

## Alternative considerate

- **Calamares personalizzato:** moderno e modulare, ma con un rischio di accessibilità proprio nel passaggio più delicato (i dischi).
- **Installer Vabax subito:** è il componente più pericoloso da scrivere (può cancellare dati). Farlo prima di avere un sistema che funziona significa rimandare tutto il resto.

## Motivazione

L'installer Debian con sintesi vocale è usato da anni da persone cieche e installa anche il supporto vocale nel sistema finale. È l'unica opzione con un'accessibilità già dimostrata sul campo.

## Conseguenze

- Nella v0.1 si installa dal menu di avvio (voce «Installa con sintesi vocale»), non da un'icona sul desktop live.
- Va verificato che l'installer della ISO VabaxOS abbia il firmware non libero necessario: è un difetto segnalato per le ISO live di Debian (vedi ROADMAP, criteri v0.1).
- Il sistema installato deve ricevere la configurazione Vabax (pacchetti `vabaxos-*`): si ottiene con un file di preconfigurazione (preseed).

## Riesame

Alla v0.5 (Installer Alpha).
