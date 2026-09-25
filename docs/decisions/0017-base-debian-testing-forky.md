# ADR-0017: Base di sviluppo — Debian testing «forky» a data fissa

- **Stato:** Accettata
- **Data:** 2026-09-24
- **Responsabile:** Vabax (Project Lead)
- **Sostituisce in parte:** [ADR-0001](0001-base-debian-trixie.md), per la serie 0.x

Vabax ha scelto questa opzione il 2026-09-24, fra tre proposte: passare a testing, restare su trixie con i backports, restare su trixie fino al 2027.

## Contesto

ADR-0001 ha scelto Debian 13 «trixie» stable. Trixie congela le versioni del 2025: a fine settembre 2026 contiene Orca 48, GNOME 48, PipeWire 1.4.2, WirePlumber 0.5.8, AT-SPI 2.56 e il kernel 6.12.

Debian testing, che diventerà Debian 14 «forky» nel 2027, contiene invece (snapshot del 2026-09-20): Orca 50.2, GNOME 50.4, PipeWire 1.6.8, WirePlumber 0.5.17, AT-SPI 2.61.90, speech-dispatcher 0.12.1 e il kernel 7.1.

Nel blocco 1 della v0.1 abbiamo incontrato diversi difetti nella catena della voce (Speakup, PipeWire, Orca dopo il cambio di console). Per un sistema la cui prima funzione è parlare, i miglioramenti di accessibilità delle versioni recenti contano più della stabilità di una base congelata. Anche ADR-0001 prevede già di passare a forky quando uscirà: la v1.0 di VabaxOS sarà comunque su forky.

## Decisione

- Per la serie 0.x VabaxOS si costruisce su **Debian testing «forky»**, architettura amd64.
- Come prima, **ogni pacchetto viene da snapshot.debian.org a una data fissa** (`image/build.conf`). Testing cambia ogni giorno, ma per noi cambia solo quando spostiamo la data, in un commit a parte e dopo le prove.
- Opzioni di live-build come nelle ISO live di testing costruite da Debian: `--distribution forky --security false --updates false`. Testing non ha un archivio di sicurezza separato.
- La ISO si costruisce ancora su **Debian 13 (ADR-0002, ADR-0013)**, ma con **live-build 1:20250814** preso da forky. Questa versione contiene «Prepare for forky» e più supporto a espeakup nell'installer. Il pacchetto si installa sulla postazione dopo averne verificato firma e impronta (`docs/sviluppo/postazione-windows.md`).
- Quando forky diventerà stable, VabaxOS passerà a forky stable e questo ADR sarà sostituito.

## Aggiornamenti

- 2026-09-24: con l'installer (blocco 2) live-build 1:20250814 non basta più: chiede `libfuse2`, che forky non ha più. Si usa live-build dal suo repository Git a un commit fisso (531cdb98 del 2026-09-13), che contiene la correzione e altre migliorie all'installer (installazione offline con voce e Braille). `scripts/install-live-build.sh` ne fa un pacchetto e lo installa.

## Alternative considerate

- **Trixie con i backports** (Orca 50, AT-SPI, PipeWire 1.4.9, kernel 7.1): base stabile con aggiornamenti di sicurezza, ma Orca 50 girerebbe su GNOME 48, una combinazione che Debian non prova insieme, e GNOME resterebbe vecchio.
- **Restare su trixie fino al 2027:** nessun rischio nuovo, ma lo sviluppo dell'accessibilità resterebbe su componenti vecchi di un anno e mezzo.

## Motivazione

Gli strumenti di accessibilità (Orca, AT-SPI, GNOME, PipeWire) migliorano molto da una versione all'altra, e VabaxOS esiste per l'accessibilità. La data fissa dello snapshot toglie il rischio principale di testing, cioè i cambiamenti improvvisi: la ISO resta riproducibile e aggiorniamo solo dopo le prove.

## Conseguenze

- **Sicurezza:** testing non riceve aggiornamenti di sicurezza tempestivi. Le ISO della serie 0.x servono a sviluppare e provare, non all'uso quotidiano con dati personali. Prima della prima alpha pubblica (ADR-0015) si decide come gestire la sicurezza: data dello snapshot recente, avvisi nelle note di rilascio, eventuale passaggio a forky stable.
- **Installer:** il Debian Installer di testing è in versione di sviluppo. Va provato con la sintesi vocale nel lavoro 9.
- **Problemi noti da seguire:** con GNOME 50 su Wayland, Orca in Firefox e nelle applicazioni Electron a volte legge solo le etichette e non il testo ([GNOME Discourse](https://discourse.gnome.org/t/orca-on-gnome-50-wayland-only-reads-element-labels-not-text-content-plus-automatic-language-switching-not-working/38619)). Va verificato quando si prova il browser.
- Il blocco 1 della v0.1 va portato su forky e verificato di nuovo, compreso l'ascolto.
- ADR-0001 resta valido per le ragioni della scelta di Debian; cambia solo la versione per la serie 0.x.

## Riesame

All'uscita di Debian 14 «forky» stable, oppure se testing blocca lo sviluppo con difetti che trixie non ha.
