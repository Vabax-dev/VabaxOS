# ADR-0001: Base del sistema — Debian 13 «trixie» stable

- **Stato:** Accettata
- **Data:** 2026-09-24
- **Responsabile:** Vabax (Project Lead)
- **Sostituita in parte da:** [ADR-0017](0017-base-debian-testing-forky.md) (serie 0.x su Debian testing «forky»)

## Contesto

La roadmap (DOC-01 §26, punto 2) chiede di scegliere fra una base Debian/Ubuntu e una costruzione indipendente. DOC-06 elenca Debian, Ubuntu LTS, Fedora, Arch e una base indipendente. Il progetto ha un fondatore e zero manutentori: ogni pacchetto che VabaxOS mantiene da solo è lavoro sottratto all'accessibilità, che è il motivo per cui il progetto esiste.

## Decisione

VabaxOS si basa su **Debian 13 «trixie» stable**, architettura **amd64**. VabaxOS non ricompila la distribuzione: aggiunge pacchetti propri, configurazione e personalizzazione sopra i pacchetti Debian.

## Alternative considerate

- **Ubuntu LTS:** buona base, ma porta con sé snap (Firefox come snap), decisioni commerciali di Canonical e una derivazione in più da seguire. Debian è la fonte da cui Ubuntu stessa deriva.
- **Fedora:** software più recente, ma ciclo di 13 mesi circa: una distribuzione piccola dovrebbe rincorrere un aggiornamento maggiore ogni anno.
- **Arch / rolling:** gli aggiornamenti continui rompono le cose senza preavviso. Per una persona che dipende dalla voce, un aggiornamento che rompe l'audio è un sistema inutilizzabile.
- **Base indipendente (LFS, Buildroot, Yocto):** controllo totale, costo totale. Servirebbe un team di sicurezza e di pacchettizzazione che non c'è. Buildroot e Yocto sono pensati per sistemi embedded.

## Motivazione

- **Stabilità:** Debian stable cambia solo per correzioni e sicurezza. Il comportamento dell'accessibilità non si rompe da un giorno all'altro.
- **Durata:** circa tre anni di supporto di sicurezza, più il supporto LTS fino al 2030 (da verificare sul sito Debian quando serve la data esatta).
- **Accessibilità già presente:** Orca, speech-dispatcher, eSpeak NG, Speakup/espeakup, BRLTTY e l'installer con sintesi vocale sono già pacchettizzati e usati da persone cieche.
- **GNOME 48:** trixie contiene GNOME 48, la prima versione in cui le scorciatoie di Orca funzionano davvero su Wayland (fonte: [LWN](https://lwn.net/Articles/1025127/), [GNOME 48](https://release.gnome.org/48/)).
- **Licenze chiare:** le Debian Free Software Guidelines separano software libero, `contrib` e `non-free-firmware`: l'inventario delle licenze (DOC-09) parte già ordinato.
- **Firmware:** da Debian 12 il firmware non libero sta nella sezione ufficiale `non-free-firmware`, quindi Wi-Fi e audio funzionano su più PC.
- **Strumenti ufficiali:** le ISO live ufficiali di Debian si costruiscono con live-build e si possono riprodurre (vedi ADR-0002).

## Conseguenze

- Il software è quello di Debian stable, quindi non sempre il più recente. Dove serve una correzione di accessibilità più nuova si usano `trixie-backports` oppure un pacchetto Vabax con la patch, ma solo con un ADR o una issue che lo motivi.
- Le correzioni di accessibilità si mandano **prima upstream** (Debian, GNOME, Orca) e solo dopo, se necessario, si tengono come patch in VabaxOS.
- Il passaggio a Debian 14 «forky» sarà una versione maggiore di VabaxOS, pianificata e testata.

## Riesame

All'uscita di Debian 14 «forky» (prevista nel 2027): si passa alla nuova stable quando esce il suo primo aggiornamento (14.1) e i test di accessibilità della v0.x passano.
