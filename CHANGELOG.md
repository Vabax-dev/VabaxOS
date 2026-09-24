# Registro delle modifiche

Tutte le modifiche importanti a VabaxOS sono registrate qui, secondo [Keep a Changelog](https://keepachangelog.com/it/1.1.0/) e il versionamento di [ADR-0015](docs/decisions/0015-versioni-e-rilasci.md).

## [Non rilasciato]

### Aggiunto

- Repository iniziale: README, roadmap operativa, architettura, guida alla costruzione (in preparazione), regole per contribuire, sicurezza, governance e codice di condotta.
- Decisioni architetturali ADR-0001–0015, che chiudono le dieci decisioni da prendere prima della v0.1.
- I 32 documenti di progetto originali in `docs/specs/`.
- Modelli per issue e pull request, CI di controllo delle licenze (REUSE).
- Guida alla postazione di sviluppo su Windows con NVDA e script di preparazione e verifica (`scripts/postazione/`).
- `CLAUDE.md` e prompt di avvio per lo sviluppo con Claude.
- CI: ShellCheck, verifica dei pacchetti Debian della postazione, analisi degli script PowerShell.
- Prima ISO minima con live-build (`image/`): pacchetti da snapshot.debian.org a data fissa, avvio GRUB in UEFI, Secure Boot e BIOS, console seriale per i test.
- Script `check-deps.sh`, `build.sh` (ISO, `SHA256SUMS`, manifest, log datato), `run-qemu.sh` (UEFI, Secure Boot, BIOS, audio) e `test-boot.sh` (test di avvio dalla console seriale).
- CI: controllo della configurazione di live-build.
