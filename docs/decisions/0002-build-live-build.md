# ADR-0002: Costruzione della ISO — live-build di Debian

- **Stato:** Accettata
- **Data:** 2026-09-24
- **Responsabile:** Vabax (Project Lead), Principal Software Engineer

## Contesto

La roadmap (DOC-01 §26, punto 3) chiede di scegliere fra live-build di Debian e una pipeline VabaxOS completamente personalizzata. DOC-06 aggiunge mkosi, Buildroot e Yocto. La v0.1 richiede una ISO live x86-64 che si avvii con UEFI, e la guida di sviluppo (DOC-02) chiede un unico comando riproducibile: `./scripts/build.sh`.

## Decisione

La ISO si costruisce con **live-build**, lo strumento con cui Debian costruisce le sue ISO live ufficiali. live-build è avvolto dagli script di VabaxOS:

- La configurazione della ISO sta in `image/` (liste di pacchetti, file da aggiungere, hook, menu di avvio).
- `scripts/build.sh` è l'unico punto d'ingresso: controlla l'ambiente, fissa le versioni, chiama live-build, calcola i checksum e scrive il log.
- I pacchetti vengono da **snapshot.debian.org** a una data fissata e registrata nel manifest della build. Così la stessa configurazione produce la stessa ISO anche fra un anno.
- I risultati vanno in `out/` (ignorata da Git): ISO, `SHA256SUMS`, manifest dei pacchetti, log datato che non sovrascrive i precedenti.
- L'ambiente di costruzione è **Debian 13**: la distribuzione Debian di WSL2 sul PC di sviluppo (ADR-0013) e il container `debian:trixie` su GitHub Actions. Lo stesso script gira in entrambi.

## Alternative considerate

- **Pipeline personalizzata** (debootstrap + squashfs + xorriso scritti a mano): riscriverebbe live-build peggio, e andrebbe mantenuta da noi.
- **mkosi:** ottimo per immagini disco e sistemi immutabili, ma non è lo strumento con cui Debian produce le ISO live ibride con installer. Da rivalutare se VabaxOS passerà ad aggiornamenti atomici.
- **Buildroot / Yocto:** pensati per sistemi embedded (lo dice già DOC-01). Sul desktop moltiplicano il lavoro.

## Motivazione

- È lo strumento ufficiale di Debian: le ISO live di trixie sono fatte così, e Debian documenta come riprodurle ([wiki Debian](https://wiki.debian.org/ReproducibleInstalls/LiveImages)).
- Produce ISO ibride (DVD e chiavetta USB) con avvio UEFI e BIOS e con l'installer Debian incluso: sono esattamente i requisiti della v0.1.
- Permette di aggiungere pacchetti, file di configurazione e script (hook) senza toccare il codice di live-build.
- È in Debian stesso: nessuna dipendenza da scaricare da fonti esterne.

## Conseguenze

- Il kernel **non** si compila nel progetto: si usa quello Debian (ADR-0003). La fase «compilare kernel» di DOC-02 §19 cade.
- La costruzione richiede i privilegi di root (chroot). In CI il container gira in modalità privilegiata.
- Obiettivo di riproducibilità: due build dallo stesso commit e dalla stessa data di snapshot devono dare lo stesso squashfs. Dove la ISO intera differisce, il motivo va documentato (come fa Debian per trixie).
- Ogni ISO porta con sé un manifest: commit Git, data dello snapshot, versione di live-build, elenco dei pacchetti con versione.

## Riesame

Se VabaxOS adotta aggiornamenti atomici o un'immagine immutabile (non prima della v1.5), oppure se live-build smette di essere mantenuto da Debian.
