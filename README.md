# VabaxOS

**VabaxOS è una distribuzione Linux progettata con l'accessibilità al centro.** Chi la avvia la sente parlare dal primo secondo, può configurarla e usarla senza vedere lo schermo e senza mouse, e trova comunque un desktop completo e normale.

> **Stato: in fase di progetto.** Le decisioni tecniche sono prese e scritte (vedi [Decisioni](docs/decisions/README.md)), ma non c'è ancora niente da scaricare. Il primo traguardo è la **v0.1**: una ISO live che si avvia, parla e arriva al desktop. Tutti i limiti vengono pubblicati man mano.

*English summary below.*

## In breve

- **Base:** Debian 13 «trixie» stable, per PC x86-64 con UEFI (e BIOS dove possibile).
- **Desktop:** GNOME su Wayland, personalizzato per VabaxOS.
- **Lettore di schermo:** Orca, con voce eSpeak NG che funziona senza Internet. In console c'è Speakup, così la voce non manca nemmeno fuori dal desktop.
- **Installazione:** installer Debian con sintesi vocale, già usato da persone cieche.
- **Programmi Vabax:** GTK 4, in italiano e in inglese fin dall'inizio.
- **Licenza:** codice GPL-3.0-or-later, documentazione CC BY-SA 4.0.

Il perché di ogni scelta è negli [ADR](docs/decisions/README.md).

## Cosa vuol dire «accessibile dal primo secondo»

Oggi una persona cieca che avvia una ISO live di Debian con GNOME può restare senza voce: nessun segnale all'avvio, Orca che non parte, un tour del desktop da cui non si esce, il sistema che va in sospensione e al risveglio ha un lettore di schermo muto. Sono problemi segnalati davvero, a maggio 2026, sulla lista debian-accessibility.

La v0.1 di VabaxOS esiste per risolvere proprio questi problemi, e ognuno diventa un test di accettazione. L'elenco è nella [Roadmap](ROADMAP.md).

## Come è organizzato il repository

| Cartella o file | Contenuto |
|---|---|
| [ROADMAP.md](ROADMAP.md) | Traguardi dalla v0.1 alla v1.0 e criteri della v0.1 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Come è fatto il sistema, strato per strato |
| [BUILD.md](BUILD.md) | Come si costruisce la ISO (in preparazione) |
| [docs/decisions/](docs/decisions/README.md) | Decisioni architetturali (ADR) |
| [docs/specs/](docs/specs/README.md) | I 32 documenti di progetto originali |
| [docs/sviluppo/](docs/sviluppo/postazione-windows.md) | Guida alla postazione di sviluppo su Windows |
| [CLAUDE.md](CLAUDE.md) | Istruzioni per Claude, che sviluppa VabaxOS con il fondatore |
| `image/` | Configurazione della ISO (live-build) |
| `packages/` | Pacchetti Debian di VabaxOS |
| `scripts/` | Script di costruzione, avvio in QEMU e test |
| `tests/` | Test automatici e casi di test di accessibilità |
| `hardware/` | Schede di compatibilità hardware |
| `artwork/` | Logo, sfondi, suoni di sistema |

## Partecipare

Si può contribuire anche senza scrivere codice: provando il sistema, segnalando barriere di accessibilità, traducendo, scrivendo documentazione o descrivendo il proprio hardware. Leggi [CONTRIBUTING.md](CONTRIBUTING.md).

- Problemi, proposte e domande: [Issues](https://github.com/Vabax-dev/VabaxOS/issues)
- Vulnerabilità di sicurezza: **non aprire una issue pubblica**, segui [SECURITY.md](SECURITY.md)

## Chi c'è dietro

VabaxOS è un progetto di [Vabax](https://vabax.it), scrittore e divulgatore non vedente che si occupa di accessibilità digitale. Per ora il progetto è guidato dal fondatore (vedi [GOVERNANCE.md](GOVERNANCE.md)).

---

## English summary

**VabaxOS is a Linux distribution designed around accessibility.** It speaks from the first second of boot, and it can be set up and used without seeing the screen and without a mouse, while still being a complete, ordinary desktop.

**Status: design phase.** The technical decisions are made and recorded as [ADRs](docs/decisions/README.md), but there is nothing to download yet. The first milestone is **v0.1**: a live ISO that boots, talks and reaches the desktop.

Stack: Debian 13 "trixie", GNOME on Wayland, the Orca screen reader with offline eSpeak NG speech, Speakup on the console, and the speech-enabled Debian Installer. Vabax apps use GTK 4. Code is licensed under GPL-3.0-or-later and documentation under CC BY-SA 4.0.

Project documents are in Italian for now. Code, commit messages and identifiers are in English. Issues in either language are welcome.
