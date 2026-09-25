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
- Voce naturale Kokoro per Orca (`vabaxos-voice`, ADR-0019): modulo per speech-dispatcher con cache delle frasi, frasi spezzate, silenzio tagliato, arresto immediato; velocità con Sonic; misura del computer a ogni avvio (Kokoro se è abbastanza veloce, altrimenti eSpeak NG); scelta della voce nella configurazione iniziale.
- Menu Start con il logo (ArcMenu, ADR-0018): tasto Super, ricerca, programmi, cartelle, menu Spegni con i nomi scritti; ogni comando ha un nome per Orca.
- Sistema installato: benvenuto solo al primo avvio; `vabaxos-report` esporta il log di avvio e i dati dell'hardware in un file di testo; prova automatica di installazione in QEMU (`scripts/test-install.sh`).
- Suoni di sistema VabaxOS in tre stili (Cristallo, Morbido, Aria); font Atkinson Hyperlegible Next nel desktop e nel menu di avvio; colore d'accento viola; logo nella schermata di accesso.
- `vabaxos-status` (Super+Alt+I): ora, batteria, rete, Bluetooth e volume letti da Orca.
- Lettore di documenti con voce naturale (`vabaxos-reader`): testo, PDF, Word, EPUB, HTML; frasi, paragrafi, segnalibri, esportazione audio.
- `vabaxos-update`: aggiornamenti annunciati a voce, subito o al riavvio, anche Flatpak; proposta ADR-0020 su aggiornamenti e sicurezza. Flatpak nella ISO.
- Tema sonoro VabaxOS, scelto da Vabax: il timbro dei suoni di Ubuntu (Yaru) con melodie nostre; cattura dello schermo di freedesktop.
- Sistema completo: LibreOffice con dizionario italiano, Thunderbird, Braille (brltty), riconoscimento del testo (anche nel lettore di documenti), Rhythmbox, libri DAISY, registratore, backup, archivi, password; aiuto di VabaxOS nel sistema e nel menu Start; proposta ADR-0021 su firewall e cifratura.
- Interfaccia familiare: barra delle applicazioni, icone di sistema, pulsanti Riduci e Ingrandisci, icone sul desktop, cronologia degli appunti, finestre affiancate, Ctrl+Maiusc+Esc; programma «Programmi di VabaxOS» per l'avvio automatico, la disinstallazione e i programmi di Windows (Bottles).
- I tasti di Windows 11: Super+T barra delle applicazioni, Super+B area di notifica, Super+A impostazioni rapide, Super+N notifiche, Super+D e Super+M desktop, Super+Freccia giù riduce a icona, Super+V appunti, Super+E, Super+I, Super+U, Super+R, Super+S; Alt+Tab per finestre; Alt+F4 sul desktop chiede di spegnere. Estensione `vabaxos-keys` e guida «I tasti di VabaxOS».
