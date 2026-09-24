# Architettura di VabaxOS

Questa pagina descrive come è fatto VabaxOS dopo le decisioni degli [ADR](docs/decisions/README.md). Il modello completo con principi, flussi e confini di sicurezza è in [DOC-03](docs/specs/03_Architecture_Specification.md).

## Idea di fondo

VabaxOS **non riscrive Linux**. Prende Debian stable, che funziona, e ci lavora sopra dove serve: far parlare il sistema dal primo secondo, renderlo usabile senza vista e senza mouse in ogni fase, e dargli un'identità coerente. Tutto quello che si può correggere upstream (Debian, GNOME, Orca) si corregge lì.

## Strati

Dal basso verso l'alto:

1. **Firmware e avvio:** UEFI con Secure Boot oppure BIOS. Shim e GRUB firmati da Debian. Il menu di avvio emette un segnale acustico. (ADR-0003, ADR-0014)
2. **Kernel:** Linux di Debian, firmato. Speakup, il lettore di schermo del kernel, legge la console. (ADR-0003, ADR-0005)
3. **Sistema di base:** Debian 13 «trixie» con systemd, NetworkManager, PipeWire e WirePlumber. (ADR-0001)
4. **Voce e Braille:** speech-dispatcher con eSpeak NG (Piper opzionale), espeakup per la console, BRLTTY per il Braille. (ADR-0005, ADR-0006)
5. **Accessibilità:** AT-SPI2, il bus attraverso cui le applicazioni descrivono al lettore di schermo cosa c'è sullo schermo. (ADR-0004)
6. **Desktop:** GNOME 48 su Wayland, con XWayland, configurato da VabaxOS. Orca parte da solo, anche nella schermata di accesso. (ADR-0004, ADR-0005)
7. **Componenti Vabax:** pacchetti `vabaxos-*` (impostazioni, accessibilità, marchio) e programmi GTK 4 (configurazione iniziale, poi Centro Accessibilità e gli altri). (ADR-0008, ADR-0010)
8. **Applicazioni:** pacchetti Debian e Flatpak. (ADR-0008)

## Dalla sorgente alla ISO

```text
repository Git (image/, packages/, scripts/)
        │
        ▼
scripts/build.sh  ── Debian 13 (WSL2 oppure container in CI)
        │   pacchetti da snapshot.debian.org a data fissa
        ▼
live-build  ──►  out/VabaxOS-<versione>-amd64.iso
                 out/SHA256SUMS
                 out/manifest.txt   (commit, snapshot, pacchetti)
                 out/logs/build-AAAA-MM-GG-HHMMSS.log
        │
        ▼
scripts/run-qemu.sh  ── QEMU + OVMF, con audio
        │
        ▼
PC fisico di prova, in modalità live
```

## Componenti di VabaxOS

| Componente | Cosa fa | Stato |
|---|---|---|
| `image/` | Configurazione di live-build: pacchetti, file, hook, menu di avvio | da fare (v0.1) |
| `vabaxos-settings` | Valori predefiniti di GNOME e del sistema | da fare (v0.1) |
| `vabaxos-accessibility` | Orca automatico, profilo Orca, Speakup, BRLTTY | da fare (v0.1) |
| `vabaxos-branding` | Nome, logo, sfondo, suoni | da fare (v0.1) |
| Configurazione iniziale Vabax | Lingua, voce, tastiera, rete al primo avvio | da fare (v0.1) |
| `vabaxctl` e servizi `vabax-*` | Strumenti di sistema della v0.2 | futuro |
| Centro Accessibilità Vabax | Tutte le impostazioni di accessibilità in un posto | futuro (v0.4) |

## Regole per chi aggiunge componenti

- Prima si cerca un componente open source esistente, mantenuto e con licenza compatibile (DOC-01 §1).
- Ogni componente nuovo deve essere usabile da tastiera e dal lettore di schermo, localizzabile e diagnosticabile (DOC-01 §66, «principio di completezza»).
- Nessun cambiamento di base, kernel, desktop o lettore di schermo senza un nuovo ADR.
