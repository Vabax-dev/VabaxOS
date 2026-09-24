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
- Menu di avvio in inglese con scelta della lingua (L); benvenuto parlato «Welcome to VabaxOS» prima del desktop (ADR-0016).
- Pacchetti `vabaxos-accessibility` (voce della console, Orca), `vabaxos-settings` (niente tour, niente sospensione automatica), `vabaxos-welcome`.
- Desktop GNOME 50 con Orca 50; un solo server audio per benvenuto, voce della console e Orca.
- Base di sviluppo Debian testing «forky» a data fissa (ADR-0017).
- `test-boot.sh` registra l'audio e controlla che benvenuto, voce della console e Orca si sentano.
- Benvenuto: menu Accessibilità (voce più lenta o più veloce, tastiera, testo grande, alto contrasto, zoom, tasti permanenti) e voce Installa.
- Programma `vabaxos-setup`: configurazione iniziale accessibile (vista, voce, tastiera e movimento, rete), letta da Orca e usabile con tastiera, zoom e contrasto.
- Installazione con voce (tasto I) e altre modalità (O): grafica ad alto contrasto, grafica, testuale.
- `vabaxos-a11y-check`: controlla che ogni comando di un programma abbia un nome leggibile dal lettore di schermo.
- CI: costruzione della ISO e prove di avvio in QEMU con controllo dei suoni.
- Logo VabaxOS in formato vettoriale; menu di avvio con il logo e colori ad alto contrasto; pacchetto `vabaxos-branding` (icona, sfondo, logo in Impostazioni > Informazioni).
- Guide per l'utente: benvenuto, configurazione iniziale, installazione.
