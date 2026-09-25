# Decisioni architetturali (ADR)

Un ADR (Architecture Decision Record) registra una decisione importante: il contesto, cosa si è scelto, le alternative scartate e le conseguenze. Serve a evitare che il progetto cambi direzione per caso.

## Regole

- Una decisione accettata si cambia solo con un **nuovo ADR** che la sostituisce. Quello vecchio resta, marcato «Sostituita da ADR-XXXX».
- Il codice non può contraddire un ADR accettato. Se serve farlo, prima si scrive l'ADR.
- Ogni ADR ha un **momento di riesame**: l'evento che obbliga a rimetterlo in discussione.
- Per scriverne uno nuovo copia [il modello](0000-modello.md).

## Stati

- **Proposta:** in discussione, non vincolante.
- **Accettata:** vincolante per il codice e la documentazione.
- **Sostituita:** superata da un ADR successivo (indicato).
- **Respinta:** valutata e scartata, conservata per memoria.

## Elenco

Queste decisioni chiudono le dieci «decisioni da prendere prima della v0.1» della roadmap originale (DOC-01, sezione 26), più quelle che servono per aprire il repository.

| ADR | Decisione | Stato |
|---|---|---|
| [0001](0001-base-debian-trixie.md) | Base del sistema: Debian 13 «trixie» stable | Accettata; per la serie 0.x vedi ADR-0017 |
| [0002](0002-build-live-build.md) | Costruzione della ISO: live-build di Debian | Accettata |
| [0003](0003-kernel-e-avvio.md) | Kernel e avvio: kernel Debian firmato, GRUB con Secure Boot | Accettata |
| [0004](0004-desktop-gnome-wayland.md) | Desktop: GNOME su Wayland | Accettata |
| [0005](0005-lettore-di-schermo-orca.md) | Lettore di schermo: Orca upstream, più Speakup in console | Accettata |
| [0006](0006-sintesi-vocale.md) | Sintesi vocale: speech-dispatcher + eSpeak NG, Piper opzionale | Accettata |
| [0007](0007-installer.md) | Installer: Debian Installer con sintesi vocale | Accettata |
| [0008](0008-pacchetti-e-applicazioni.md) | Pacchetti: APT + repository Vabax, Flatpak opzionale | Accettata |
| [0009](0009-filesystem.md) | Filesystem: ext4, LUKS2 opzionale | Accettata |
| [0010](0010-programmi-vabax-gtk.md) | Programmi Vabax: GTK 4 + libadwaita, Python e Rust | Accettata |
| [0011](0011-licenze.md) | Licenze: GPL-3.0-or-later, CC BY-SA 4.0, REUSE, DCO | Accettata |
| [0012](0012-repository-e-flusso-di-lavoro.md) | Repository e flusso di lavoro: monorepo, trunk-based | Accettata |
| [0013](0013-ambiente-di-sviluppo.md) | Ambiente di sviluppo: Windows 11 + WSL2 Debian + QEMU | Accettata |
| [0014](0014-voce-dal-primo-secondo.md) | Voce dal primo secondo: accessibilità attiva di default | Accettata |
| [0015](0015-versioni-e-rilasci.md) | Versioni, canali e nomi degli artefatti | Accettata |
| [0016](0016-benvenuto-parlato.md) | Benvenuto parlato all'avvio, prima del desktop | Accettata |
| [0017](0017-base-debian-testing-forky.md) | Base di sviluppo: Debian testing «forky» a data fissa (serie 0.x) | Accettata |
| [0018](0018-menu-start.md) | Menu Start con il logo di VabaxOS (ArcMenu) | Accettata |
| [0019](0019-voce-naturale-kokoro.md) | Voce naturale Kokoro per il desktop, eSpeak NG come riserva | Accettata |
| [0020](0020-aggiornamenti-e-sicurezza.md) | Aggiornamenti e sicurezza | Proposta |
| [0021](0021-firewall-e-cifratura.md) | Firewall e cifratura del disco | Proposta |
| [0022](0022-nomi-dei-pulsanti-di-gnome-shell.md) | Nomi dei pulsanti di GNOME Shell, corretti da VabaxOS | Accettata |
| [0023](0023-installare-dal-benvenuto.md) | Installare dal benvenuto, con le scelte di accessibilità | Accettata |
| [0024](0024-espeak-predefinito.md) | eSpeak NG voce predefinita, Kokoro a scelta dell'utente | Accettata |
