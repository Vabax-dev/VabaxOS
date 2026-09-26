# packages/

Pacchetti Debian di VabaxOS, uno per cartella, con prefisso `vabaxos-` ([ADR-0008](../docs/decisions/0008-pacchetti-e-applicazioni.md)). Stanno nella ISO e, quando sarà online, nell'archivio APT di VabaxOS ([ADR-0026](../docs/decisions/0026-archivio-apt-e-chiave.md)).

| Pacchetto | Cosa fa |
|---|---|
| `vabaxos-accessibility` | Voce della console (Speakup con eSpeak NG) nella lingua del sistema, Orca attivo di default, «senza voce» che spegne entrambi, nomi dei pulsanti di GNOME Shell con la sola icona (ADR-0022) |
| `vabaxos-settings` | Impostazioni di GNOME: niente tour, niente sospensione automatica, niente blocco dello schermo con password |
| `vabaxos-welcome` | Il [benvenuto parlato](../docs/utente/benvenuto.md) prima del desktop (ADR-0016) |
| `vabaxos-archive-keyring` | La chiave del progetto e le sorgenti APT dell'archivio VabaxOS (ADR-0026) |

Previsto per la v0.1: `vabaxos-branding` (nome, logo, sfondo, suoni).

## Com'è fatta una cartella

- `control`: il file `DEBIAN/control`, senza la riga `Version` (la aggiunge lo script);
- `root/`: i file da installare, nella posizione che avranno nel sistema;
- `postinst`, `postrm`: script del pacchetto, facoltativi;
- `po/*.po`: traduzioni gettext del programma, facoltative;
- `build`: un programma che prepara altri file nel pacchetto, facoltativo.

La versione di tutti i pacchetti è in `VERSION`: la prossima versione da rilasciare, nella forma di Debian (`0.1.0~alpha.1` per `0.1.0-alpha.1`). Le costruzioni di sviluppo aggiungono `+git` e la data del commit, così le versioni crescono sempre.

`scripts/build-packages.sh CARTELLA` costruisce tutti i pacchetti senza privilegi di root. `scripts/build.sh` lo chiama da solo e mette i pacchetti nella ISO.

## Test

```bash
python3 tests/welcome/test_welcome.py
```

Prova il benvenuto in un terminale finto, senza voce e senza cambiare il sistema: il programma scrive in un file cosa avrebbe detto e fatto (`VABAXOS_WELCOME_DRY_RUN`).
