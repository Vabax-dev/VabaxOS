# ADR-0013: Ambiente di sviluppo — Windows 11 + WSL2 Debian + QEMU

- **Stato:** Accettata
- **Data:** 2026-09-24
- **Responsabile:** Vabax (Project Lead)

## Contesto

DOC-02 definisce la postazione: Windows 11 con NVDA, WSL2 con **Ubuntu 24.04**, VS Code con Remote WSL e QEMU come laboratorio. Dopo ADR-0001 e ADR-0002 la ISO si costruisce con live-build di Debian, che su Ubuntu è una versione diversa (derivata) e non costruisce ISO Debian affidabili.

## Decisione

- **Postazione:** Windows 11 con NVDA, Windows Terminal, Git, VS Code con l'estensione WSL (come DOC-02).
- **Ambiente Linux:** **WSL2 con Debian** (`wsl --install -d Debian`), portato a Debian 13 se WSL installa una versione precedente. Sostituisce Ubuntu 24.04: l'ambiente di sviluppo è uguale alla base del sistema, e live-build è quello vero di Debian.
- **Repository:** nel filesystem di WSL, `~/projects/VabaxOS` (come DOC-02 §6).
- **Laboratorio:** **QEMU dentro WSL2**, con accelerazione KVM (la virtualizzazione annidata di WSL2 su Windows 11) e audio tramite WSLg, così la voce della macchina virtuale si sente dalle cuffie del PC. In alternativa, QEMU per Windows con WHPX.
- **Firmware UEFI della VM:** OVMF (pacchetto `ovmf`), anche nella variante con Secure Boot per provare ADR-0003.
- **Costruzione automatica:** **GitHub Actions** costruisce la ISO in un container `debian:trixie` a ogni modifica di `main` e la mette a disposizione come artefatto. Chi non vuole costruire in locale può scaricarla e provarla.
- **Primo PC fisico di prova:** una macchina diversa dalla postazione (DOC-02 §32). Candidato: il mini PC AMD Ryzen 7 5800U, 32 GB, da confermare. Si prova sempre in modalità live, senza installare.

## Alternative considerate

- **Ubuntu 24.04 in WSL (DOC-02 originale):** il live-build di Ubuntu è un'altra versione, e si costruirebbe una ISO Debian su una base diversa, con differenze difficili da diagnosticare.
- **Costruire solo in CI:** comodo, ma un ciclo modifica → prova di mezz'ora rallenta il lavoro sul menu di avvio e sulla voce.
- **Docker Desktop su Windows:** un programma in più, e la sua interfaccia non è pensata per NVDA. Il container si usa solo in CI.

## Motivazione

Stessa base in sviluppo, in CI e nel prodotto: un problema che si vede in un posto si riproduce negli altri. L'audio della VM che arriva alle cuffie è indispensabile per provare un sistema il cui primo requisito è parlare.

## Conseguenze

- DOC-02 è superato su questi punti. La guida pratica è [docs/sviluppo/postazione-windows.md](../sviluppo/postazione-windows.md), con gli script in `scripts/postazione/`.
- Claude lavora dall'app Claude in una sessione WSL (ambiente Debian), oppure con Claude Code nel terminale di Debian. Il contesto del progetto per Claude è in `CLAUDE.md`.
- La prima verifica sulla postazione è che KVM e l'audio funzionino dentro WSL2 (`/dev/kvm` presente, audio WSLg udibile).

## Riesame

Se KVM o l'audio non funzionano sulla postazione reale: allora si passa a QEMU per Windows con WHPX, con uno script `.ps1` equivalente.
