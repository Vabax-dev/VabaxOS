# ADR-0008: Pacchetti — APT + repository Vabax, Flatpak opzionale

- **Stato:** Accettata
- **Data:** 2026-09-24
- **Responsabile:** Vabax (Project Lead)

## Contesto

La roadmap propone pacchetti nativi più Flatpak (DOC-01 §26, punto 7). DOC-13 lascia aperti il gestore dei pacchetti, i repository, le firme e AppImage.

## Decisione

- **Sistema:** pacchetti **.deb** gestiti da **APT**, come in Debian.
- **Componenti VabaxOS:** pacchetti con prefisso `vabaxos-` (per esempio `vabaxos-settings`, `vabaxos-accessibility`, `vabaxos-branding`) e un **repository APT Vabax firmato**, separato dai repository Debian. Fino alla prima alpha pubblica i pacchetti Vabax sono inclusi direttamente nella ISO; il repository online arriva con la v0.2.
- **Applicazioni desktop di terze parti:** **Flatpak** preinstallato, con **Flathub attivabile** dall'utente. VabaxOS non preinstalla applicazioni Flatpak.
- **AppImage:** si avvia, ma non viene integrato né promosso.
- **Metadati di accessibilità:** ogni applicazione dello store Vabax (v0.7) dichiarerà cosa è stato provato (tastiera, lettore di schermo, Braille, contrasto), con stato «provata», «parziale», «non provata» o «barriere note».

## Alternative considerate

- **Solo Flatpak (sistema immutabile):** interessante per gli aggiornamenti atomici, ma è una seconda rivoluzione da fare dopo avere un sistema accessibile che funziona.
- **Snap:** legato a un solo store centralizzato.

## Motivazione

APT è il sistema della base scelta (ADR-0001): usarlo non costa niente e permette di distribuire le parti Vabax come normali pacchetti, aggiornabili e rimovibili. Flatpak serve ad avere applicazioni recenti senza toccare la base stabile.

## Conseguenze

- Serve una chiave di firma del repository, custodita fuori dal repository Git, prima di pubblicarlo (DOC-10).
- I pacchetti `vabaxos-*` stanno in `packages/`, uno per cartella, costruiti da `scripts/`.

## Riesame

Quando si valutano gli aggiornamenti atomici e il rollback (v1.5).
