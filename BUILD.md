# Costruire VabaxOS

> **In preparazione.** Gli script non esistono ancora: arrivano con i primi lavori della v0.1 (vedi [ROADMAP.md](ROADMAP.md)). Questa pagina descrive come funzioneranno, secondo [ADR-0002](docs/decisions/0002-build-live-build.md) e [ADR-0013](docs/decisions/0013-ambiente-di-sviluppo.md).

## Cosa serve

- Un sistema **Debian 13** amd64: su Windows è la distribuzione Debian di WSL2, in CI il container `debian:trixie`.
- I privilegi di amministratore (`sudo`), perché live-build lavora in un chroot.
- Circa 20 GB liberi e una connessione a Internet per scaricare i pacchetti.

La guida passo passo per preparare la postazione Windows con NVDA è un lavoro della v0.1.

## I tre comandi

```bash
./scripts/check-deps.sh   # controlla che ci sia tutto il necessario
./scripts/build.sh        # costruisce la ISO
./scripts/run-qemu.sh     # avvia la ISO in una macchina virtuale con audio
```

## Cosa produce

Tutto va nella cartella `out/`, che Git ignora:

| File | Contenuto |
|---|---|
| `VabaxOS-<versione>-amd64.iso` | L'immagine da avviare in QEMU o da scrivere su una chiavetta |
| `SHA256SUMS` | Checksum per verificare l'immagine |
| `manifest.txt` | Commit Git, data dello snapshot Debian, elenco dei pacchetti con versione |
| `logs/build-AAAA-MM-GG-HHMMSS.log` | Log completo, mai sovrascritto |

## Riproducibilità

I pacchetti vengono da snapshot.debian.org a una data fissata in `image/`. Due costruzioni dallo stesso commit devono produrre lo stesso filesystem della ISO. Se non succede è un difetto da segnalare.
