# packages/

Pacchetti Debian di VabaxOS, uno per cartella, con prefisso `vabaxos-` ([ADR-0008](../docs/decisions/0008-pacchetti-e-applicazioni.md)). Fino al repository APT Vabax (v0.2) stanno solo dentro la ISO.

| Pacchetto | Cosa fa |
|---|---|
| `vabaxos-accessibility` | Voce della console (Speakup con eSpeak NG) nella lingua del sistema, Orca attivo di default, «senza voce» che spegne entrambi |
| `vabaxos-settings` | Impostazioni di GNOME: niente tour, niente sospensione automatica, niente blocco dello schermo con password |
| `vabaxos-welcome` | Il [benvenuto parlato](../docs/utente/benvenuto.md) prima del desktop (ADR-0016) |

Previsto per la v0.1: `vabaxos-branding` (nome, logo, sfondo, suoni).

## Com'è fatta una cartella

- `control`: il file `DEBIAN/control`, senza la riga `Version` (la aggiunge lo script);
- `root/`: i file da installare, nella posizione che avranno nel sistema;
- `postinst`, `postrm`: script del pacchetto, facoltativi;
- `po/*.po`: traduzioni gettext del programma, facoltative.

`scripts/build-packages.sh CARTELLA` costruisce tutti i pacchetti senza privilegi di root. `scripts/build.sh` lo chiama da solo e mette i pacchetti nella ISO.

## Test

```bash
python3 tests/welcome/test_welcome.py
```

Prova il benvenuto in un terminale finto, senza voce e senza cambiare il sistema: il programma scrive in un file cosa avrebbe detto e fatto (`VABAXOS_WELCOME_DRY_RUN`).
