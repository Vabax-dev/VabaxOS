# ADR-0004: Desktop — GNOME su Wayland

- **Stato:** Accettata
- **Data:** 2026-09-24
- **Responsabile:** Vabax (Project Lead)

## Contesto

La roadmap chiede di scegliere fra GNOME personalizzato e una shell Wayland minimale (DOC-01 §26, punto 1), e fra GNOME/GTK, KDE/Qt o un ambiente Vabax proprio (punto 10). Il criterio che conta più di tutti è uno: **quanto bene il lettore di schermo funziona sul desktop, oggi**.

## Decisione

Il desktop di VabaxOS è **GNOME** (versione 48 in Debian 13) su **Wayland**, con XWayland per le applicazioni X11. L'identità Vabax si ottiene con configurazione e componenti aggiunti, non con una shell nuova:

- valori predefiniti con override di GSettings nel pacchetto `vabaxos-settings`;
- tema, sfondo, suoni e scorciatoie Vabax;
- tour iniziale di GNOME disattivato e sostituito dalla configurazione iniziale Vabax (ADR-0014);
- il minor numero possibile di estensioni della shell, perché si rompono a ogni versione di GNOME.

Una shell Vabax propria («Vabax Shell» della roadmap) non si scrive prima della v0.4, e solo se un ADR dimostra un limite di GNOME che non si può risolvere upstream.

## Alternative considerate

- **KDE Plasma (Qt):** molto configurabile, ma l'accessibilità delle applicazioni Qt tramite AT-SPI è meno curata di quella GTK, e Orca nasce e viene provato soprattutto su GNOME. Anche l'esperienza del progetto Vabax Studio mostra che Qt espone male gli elementi ai lettori di schermo.
- **Shell Wayland minimale (sway, labwc e simili):** leggera, ma dovremmo costruire da zero pannelli, notifiche, impostazioni e integrazione con Orca. Anni di lavoro prima di arrivare a quello che GNOME dà subito.
- **Ambiente Vabax proprietario:** stesso problema, moltiplicato.
- **Sessione X11:** più matura per Orca in passato, ma in via di dismissione in GNOME. Partire su X11 vorrebbe dire migrare di nuovo fra un anno.

## Motivazione

- Con GNOME 48 e AT-SPI 2.56 le scorciatoie di Orca funzionano su Wayland, compreso Bloc Maiusc come tasto Orca ([LWN](https://lwn.net/Articles/1025127/)).
- GTK 4 ha un'accessibilità progettata dentro il toolkit, e le applicazioni GNOME di base (file, impostazioni, terminale) sono quelle più provate con Orca.
- GNOME ha un team di accessibilità attivo (progetto Newton per l'accessibilità nativa su Wayland): lavoriamo con loro, non da soli.

## Conseguenze

- Il consumo di memoria è quello di GNOME: «leggero» si misura (DOC-01 §17), non si promette.
- I problemi di accessibilità di GNOME diventano nostri da segnalare e correggere upstream (DOC-31).
- Con Debian 14 arriverà un GNOME più recente, probabilmente senza sessione X11: va provato prima del passaggio (ADR-0001).

## Riesame

Alla v0.4 (Desktop Alpha): se i test con utenti mostrano barriere che GNOME non risolve e che upstream non accetta.
