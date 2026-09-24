# ADR-0010: Programmi Vabax — GTK 4 + libadwaita, Python e Rust

- **Stato:** Accettata
- **Data:** 2026-09-24
- **Responsabile:** Vabax (Project Lead), Principal Software Engineer

## Contesto

La roadmap prevede programmi Vabax: configurazione iniziale, Centro Accessibilità, Impostazioni, Diagnostica, Store e altri (DOC-01 §9, §12, §20). DOC-08 lascia aperti i linguaggi per sottosistema. Il desktop è GNOME (ADR-0004).

## Decisione

- **Interfaccia grafica:** **GTK 4 + libadwaita**. Niente Qt nei programmi Vabax.
- **Linguaggio dei programmi con interfaccia:** **Python** con **PyGObject**. Veloce da scrivere e da cambiare dopo i test con gli utenti, e noto al fondatore.
- **Servizi di sistema che restano sempre attivi** (i `vabax-*d` della roadmap §58): **Rust**, quando un servizio lo giustifica (memoria, sicurezza, concorrenza). Prima si verifica se basta configurare un servizio esistente.
- **Script di costruzione:** **Bash** (POSIX dove possibile), controllato con ShellCheck.
- **Comunicazione fra componenti:** **D-Bus**, lo standard del desktop Linux.
- **Traduzioni:** **gettext**. Nessuna stringa rivolta all'utente scritta direttamente nel codice. Lingue iniziali: italiano e inglese (DOC-01 §28).
- **Accessibilità obbligatoria:** ogni controllo ha nome, ruolo e stato accessibili, e ogni programma si usa da tastiera. È una condizione per accettare il codice (DOC-05).

## Alternative considerate

- **Qt / PySide:** l'esperienza del progetto Vabax Studio mostra che Qt espone male gli elementi al lettore di schermo (elenchi senza nome, contenitori appiattiti). Su Linux l'accessibilità di Qt con Orca è meno curata di quella di GTK.
- **C/C++:** più lavoro e più rischi di sicurezza della memoria, senza vantaggi per programmi di configurazione.
- **Web (Electron, Tauri):** più memoria e un secondo motore di accessibilità da controllare.

## Motivazione

GTK 4 è il toolkit di GNOME, con l'accessibilità progettata dentro. Python accelera il ciclo prototipo → test con utenti → correzione, che per l'accessibilità conta più della velocità di esecuzione.

## Conseguenze

- Ogni programma Vabax ha test automatici che controllano l'albero accessibile (nomi, ruoli) tramite AT-SPI.
- Stile del codice: Ruff per Python, rustfmt e Clippy per Rust, ShellCheck per Bash.
- Serve un modello di programma Vabax (il futuro `vabax create-app` della roadmap §59).

## Riesame

Se un programma Vabax ha requisiti di prestazioni che Python non soddisfa (misurati), oppure alla v0.4 con i risultati dei test.
