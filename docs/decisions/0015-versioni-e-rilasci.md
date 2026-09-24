# ADR-0015: Versioni, canali e nomi degli artefatti

- **Stato:** Accettata
- **Data:** 2026-09-24
- **Responsabile:** Vabax (Project Lead)

## Contesto

DOC-12 propone `major.minor.patch`, i canali nightly/alpha/beta/RC/stable e un nome per le ISO, ma lascia aperti lo schema, la cadenza e la firma.

## Decisione

- **Versione del sistema:** `MAJOR.MINOR.PATCH` con suffisso di canale, per esempio `0.1.0-alpha.1`, `0.1.0`, `1.0.0-rc.2`. MINOR segue la roadmap (0.1 = Proof of Concept … 0.9 = Release Candidate).
- **Canali:** `nightly` (costruita dalla CI su `main`, solo per chi sviluppa), `alpha`, `beta`, `rc`, `stable`.
- **Tag Git:** `v0.1.0-alpha.1`, sempre su `main`.
- **Nome della ISO:** `VabaxOS-<versione>-amd64.iso`, per esempio `VabaxOS-0.1.0-alpha.1-amd64.iso`. Per le nightly: `VabaxOS-nightly-<AAAAMMGG>-<commit>-amd64.iso`.
- **Accanto a ogni ISO:** `SHA256SUMS`, il manifest della build (commit, data dello snapshot Debian, pacchetti) e le note di rilascio con i limiti noti.
- **Pubblicazione:** GitHub Releases per alpha e successive. Le nightly restano artefatti della CI, non release.
- **Firma:** dalla prima alpha pubblica il file `SHA256SUMS` è firmato con una chiave OpenPGP del progetto, custodita fuori dal repository, con impronta pubblicata su GitHub e su vabax.it.
- **Nessuna data promessa:** una versione esce quando passa i suoi criteri (ROADMAP), non in un giorno stabilito.

## Alternative considerate

- **Versioni per data (26.10):** adatte a rilasci a cadenza fissa, ma la roadmap è a traguardi.
- **Sigstore per la firma:** interessante, ma meno familiare per chi deve verificare a mano. Da rivalutare.

## Motivazione

Nomi prevedibili e verificabili permettono a chiunque, anche da tastiera e con lettore di schermo, di capire cosa sta scaricando e di controllarlo.

## Conseguenze

- `CHANGELOG.md` segue le sezioni di [Keep a Changelog](https://keepachangelog.com/it/1.1.0/).
- La procedura di verifica della firma va scritta in modo accessibile prima della prima alpha.

## Riesame

Alla v0.9: politica del supporto a lungo termine e durata del supporto della 1.0.
