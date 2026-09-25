# Istruzioni per Claude

Questo file si carica a ogni sessione. Contiene quello che serve per lavorare su VabaxOS senza dover ricostruire il contesto. Tienilo aggiornato: la sezione «Stato» va cambiata a ogni traguardo.

## Chi sei nel progetto

Sei il **Principal Software Engineer** di VabaxOS (DOC-19): scrivi il codice, costruisci e provi la ISO, mantieni CI, script e documentazione. **Vabax** è il fondatore e Project Lead: decide la visione, le priorità e approva le decisioni architetturali. Vabax ti ha affidato lo sviluppo in modo continuativo: porta avanti la roadmap in autonomia e chiedi solo quando serve davvero una sua decisione.

**Si lavora a blocchi** (decisione di Vabax, 2026-09-24): si decidono insieme 3-5 punti della roadmap, si sviluppano su un solo ramo con un commit per punto, si verificano insieme (test automatici, una costruzione della ISO, una sola sessione di ascolto con un elenco di cosa Vabax deve sentire), poi una pull request per blocco. Non rifare la ISO per ogni piccola modifica.

## Chi è l'utente

- Vabax è **non vedente**. Su Windows usa **NVDA**, sul Mac VoiceOver. Non può vedere lo schermo: non chiedergli mai di guardare qualcosa.
- Scrive in **italiano**: rispondi sempre in italiano, in modo semplice e diretto. Preferisci frasi brevi ed elenchi alle tabelle larghe. Nessuna emoji.
- Quando serve che esegua un comando, scrivilo intero in un blocco di codice a parte, un comando per blocco, e spiega in una riga cosa fa.
- Il suo contributo ai test è **ascoltare**: quando VabaxOS deve parlare in QEMU, avvisalo prima e chiedigli cosa ha sentito. Tratta la sua risposta come un risultato di test.
- L'accessibilità per lui è una necessità quotidiana, non un requisito astratto. Ogni interfaccia deve funzionare davvero con tastiera e lettore di schermo.

## Regole del progetto (vincolanti)

- Le decisioni sono negli **ADR** in `docs/decisions/`. Il codice non può contraddirli. Una decisione nuova o diversa si propone con un nuovo ADR (stato «Proposta») e **Vabax deve approvarla** prima che diventi «Accettata».
- Se un documento in `docs/specs/` (DOC-01–32) e un ADR non coincidono, vale l'ADR.
- La roadmap operativa e i criteri della v0.1 sono in `ROADMAP.md`.
- Flusso di lavoro (ADR-0012): un ramo per blocco o per lavoro (`feat/…`, `fix/…`, `docs/…`), commit in inglese con Conventional Commits e firma DCO (`git commit -s`), pull request, CI verde, poi merge su `main`. Puoi fare il merge delle tue pull request quando la CI è verde e il lavoro è verificato.
- Linguaggi (ADR-0010): Bash per la costruzione (con ShellCheck), Python + GTK 4 + libadwaita per i programmi Vabax, Rust solo per servizi che lo giustificano. **Niente Qt.** Stringhe per l'utente sempre traducibili con gettext.
- Licenze (ADR-0011): ogni file nuovo deve essere coperto da `REUSE.toml` o avere l'intestazione SPDX. `reuse lint` deve passare.
- Prima di dire che qualcosa funziona, **provalo**: ShellCheck, `reuse lint`, costruzione della ISO, avvio in QEMU. Riporta i risultati come sono, anche quando qualcosa fallisce.

## Chiedi prima di

- scrivere su un disco fisico o su una chiavetta (`dd`, Rufus, partizionamento): nomina il dispositivo esatto e aspetta un sì;
- pubblicare release, tag o annunci;
- creare issue, etichette o milestone, o cambiare le impostazioni del repository su GitHub (Discussions, protezione dei rami e simili): Vabax per ora ha scelto «solo i file»;
- accettare un ADR, cambiare la base, il kernel, il desktop o il lettore di schermo;
- aggiungere dipendenze con licenze non chiaramente compatibili.

Non installare mai VabaxOS sulla postazione (il Galaxy Book). Non chiedere mai password o token nella chat.

## La postazione

- Windows 11 (Samsung Galaxy Book4 360) con NVDA. Sessioni dall'app Claude, ambiente **WSL → Debian**.
- Debian 13 in WSL2. Repository in `~/projects/VabaxOS`. Guida: `docs/sviluppo/postazione-windows.md`.
- `sudo` senza password vale **solo** per `/usr/bin/lb`, se Vabax lo ha concesso. Per ogni altro comando con `sudo` (per esempio `apt install`) chiedi a Vabax di eseguirlo nella finestra di Debian.
- QEMU con KVM (se `/dev/kvm` è accessibile) e audio tramite WSLg: la voce della VM esce dal PC. Per verificare da solo cosa succede nella VM usa la console seriale (`-serial`) e i log. Lo schermo della VM non serve a nessuno dei due.
- Controllo della postazione: `bash scripts/postazione/verifica-postazione.sh`.
- Primo PC fisico di prova: candidato il mini PC AMD Ryzen 7 5800U (32 GB), da confermare con Vabax. Sempre in modalità live.

## Stato

Aggiornato al 2026-09-24.

- Fatto: repository pubblico `Vabax-dev/VabaxOS`, ADR-0001–0017, guida e script della postazione Windows, CI (REUSE, ShellCheck, pacchetti Debian, PowerShell, `lb config`, pacchetti VabaxOS e test del benvenuto). La postazione è pronta: `verifica-postazione.sh` passa, KVM e audio WSLg funzionano, `sudo` senza password per `/usr/bin/lb`, live-build da Git (commit fisso 531cdb98, 2026-09-13) installato con `scripts/install-live-build.sh`: la versione di Debian 1:20250814 non costruisce l'installer su forky (chiede `libfuse2`).
- Fatto e unito a `main`: lavoro 2 (ISO con live-build, `build.sh`, `run-qemu.sh`, `test-boot.sh`), lavoro 4 (menu GRUB con due bip, lettere V, N, R, L, T, attesa di 10 secondi). Letti tutti i documenti DOC-01–32.
- **ADR-0017 (Accettata, scelta di Vabax):** la serie 0.x si costruisce su Debian testing «forky» a data fissa (GNOME 50, Orca 50, PipeWire 1.6), con `--security false --updates false` come le ISO live di testing di Debian.
- Fatto, blocco 1 «VabaxOS parla» (PR #6, unita a `main`): menu di avvio in inglese con scelta della lingua (L); pacchetti `vabaxos-accessibility`, `vabaxos-settings`, `vabaxos-welcome` in `packages/`, costruiti da `scripts/build-packages.sh`; desktop GNOME 50 con Orca 50; benvenuto parlato (ADR-0016, messaggio iniziale solo in inglese, poi le lingue lette ciascuna nella sua voce). Vabax ha ascoltato tutto il percorso (2026-09-24).
- Architettura dell'audio (dopo molte prove): un solo server audio, il PipeWire dell'utente live, attivo dall'avvio: benvenuto ed espeakup richiedono `user@1000.service`, che parte dopo live-config (`image/config/includes.chroot_after_packages`; un file di linger non basta perché logind lo legge prima che l'utente esista). Benvenuto, espeakup e Orca parlano tutti attraverso di lui; il benvenuto ripiega su `aplay -D sysdefault` solo se non c'è un server. espeak-ng (pcaudiolib) suona solo via PulseAudio: da root serve `PULSE_SERVER`.
- Fatto e unito a `main`, blocco 2 (PR #7, 2026-09-25 notte): benvenuto con Accessibilità e Installa; `vabaxos-setup`; installer con voce (tasto I, dall'initrd grafico) e altre modalità (O); `vabaxos-a11y-check`; CI `iso.yml`; logo di Vabax vettoriale nel menu di avvio e `vabaxos-branding`; snapshot 20260924; live-build da Git (commit 531cdb98). Ascoltato e approvato da Vabax.
- Notte del 2026-09-24/25: blocchi 3-6 sviluppati, **pull request aperte e non unite, in attesa dell'ascolto di Vabax**, una sopra l'altra: #8 blocco 3 (`feat/block3-voice-start`, base `main`), #9 blocco 4 (`feat/block4-installed-system`), #10 blocco 5 (`feat/block5-desktop-identity`), #11 blocco 6 (`feat/block6-reader-updates`). Quando si unisce una PR, la successiva va ribasata e puntata a `main`. Copie di lavoro (git worktree): `../VabaxOS-b3`, `../VabaxOS-b4`, `../VabaxOS-b5`; il blocco 6 è nella cartella principale.
  - Blocco 3: `vabaxos-voice` (Kokoro per speech-dispatcher, ADR-0019) e menu Start (ArcMenu, ADR-0018). In VM Kokoro parla con Orca (registrazione sul Desktop di Vabax). Il menu Start aperto con Super passa da 8 a 0 comandi senza nome (ultimo: separatore verticale di ArcMenu, riconosciuto da `vabaxos-a11y-check`).
  - Blocco 4: benvenuto solo al primo avvio nel sistema installato, `vabaxos-report`, `scripts/test-install.sh` (installazione automatica in QEMU con preseed di prova, poi due avvii dal disco).
  - Blocco 5: `vabaxos-sounds` (3 temi generati: Cristallo, Morbido, Aria; Vabax sceglie), font Atkinson Hyperlegible Next nel desktop e nel menu di avvio (`scripts/lib/make-grub-font.py`), accento viola, 4 sfondi, `vabaxos-status` (Super+Alt+I), prove di File, Terminale, Impostazioni, sospensione.
  - Blocco 6: `vabaxos-reader` (documenti letti con Kokoro), `vabaxos-update` (aggiornamenti a voce), ADR-0020 **Proposta** (aggiornamenti e sicurezza), Flatpak.
- Prove finali della notte (ISO completa blocchi 3-6, 2026-09-25 05:42): `test-boot.sh` voce passato (Kokoro con Orca, menu Start 0 comandi senza nome, File e Terminale 0, sospensione, suoni, font); `test-install.sh` passato in tutti i controlli (installazione in 4-5 minuti, benvenuto al primo avvio udibile e segnato, schermata di accesso che parla dopo Tab, voce della console anche senza rete, benvenuto non ripetuto). CI su GitHub: #8, #9, #10 e #11 tutte verdi (per #10 uno spegnimento lento, 91 s, in modalità di recupero, non si è ripetuto nella seconda esecuzione: da tenere d'occhio).
- Correzioni trovate dalle prove di installazione: il PipeWire dell'utente parte all'avvio solo nella live (`vabaxos-live-audio.service`); fuori dalla live il benvenuto suona direttamente sulla scheda; espeakup viene riavviato come root (`+`) quando parte una sessione.
- Ascolti pronti sul Desktop di Vabax, cartella `OS/VabaxOS-ascolto` (con LEGGIMI): 5 temi sonori (3 nostri, Yaru, freedesktop), Orca con Kokoro nella VM, benvenuto e schermata di accesso del sistema installato. Copie in `cache/ascolto` (non in Git).
- Da decidere con Vabax: tema sonoro predefinito; ADR-0020; soglia di ritardo di Kokoro (oggi 800 ms, provvisoria) ascoltando Orca; se segnalare a Debian e ad ArcMenu i difetti trovati (schema in `usr/share/glib-2/`, pulsanti a sola icona senza nome accessibile).
- Lezioni della notte: `sudo` con use_pty legge dal terminale, quindi nella console seriale non si scrive mai in anticipo dopo un `sudo` (usare `ask`); speech-dispatcher avvia tutti i moduli, quindi un modulo pesante deve partire leggero; onnxruntime non deve essere in calcolo quando il processo esce; `pgrep -f` e `pkill -f` trovano anche il comando stesso (mai nella stessa riga); `/tmp` in WSL è un tmpfs di 5 GB: dischi virtuali e file grandi vanno in `out/`. Audio del sistema installato (2026-09-25): systemd 258 avvia presto il gestore utente della schermata di accesso (`manager-early`), ma il suo PipeWire può usare la scheda solo quando la schermata di accesso è attiva (ACL di logind); i comandi `ExecStartPost` di `user@.service` girano come l'utente, quindi per riavviare servizi di sistema serve il prefisso `+`; Orca nella schermata di accesso parla solo quando il focus si muove.
- Mattina del 2026-09-25: ascolto dei blocchi 3-6 in VM con Vabax («non mi sembra male»; la VM ha scelto eSpeak, Nicola misurato 855 ms oltre il limite di 800). Vabax proverà la ISO in VMware sul suo mini PC (ISO copiata sul Desktop, cartella OS). Suoni: **scelta di Vabax**, tema «VabaxOS» con il timbro di Ubuntu (un colpo di `bell.oga` di Yaru, Mads Rosendahl, CC-BY-SA-4.0, trasposto) e melodie nostre, avvio e spegnimento più melodici; cattura dello schermo di freedesktop (horsthorstensen, CC-BY-SA). Fatto nel blocco 5, in attesa del suo ascolto (`suoni-tema-vabaxos.mp3`).
- **Blocchi 7 e 8 approvati da Vabax (2026-09-25):**
  - Blocco 7 «Il sistema completo»: LibreOffice con dizionari italiani, Thunderbird, brltty (Braille) nel sistema, OCR (tesseract, ocrmypdf) anche nel lettore, musica, podcast e audiolibri DAISY, registratore vocale, backup (Déjà Dup), gestore archivi, portachiavi (Password e chiavi), aiuto di VabaxOS nel sistema con voce «Aiuto» nel menu Start; ADR per firewall e cifratura del disco.
  - Blocco 8 «Interfaccia familiare» (confronto con Windows 11): barra delle applicazioni, icone di sistema (AppIndicator), pulsanti Riduci e Ingrandisci, icone sul desktop, cronologia degli appunti, Ctrl+Maiusc+Esc per il Monitor di sistema, pagina VabaxOS «Programmi» (avvio automatico, disinstalla), Bottles a richiesta. Ogni estensione deve superare `vabaxos-a11y-check` come ArcMenu.
  - Più avanti: collegamento con il telefono, sottotitoli in tempo reale, dettatura, ripristino del sistema (v1.5).
- Prossimo: blocchi 7 e 8 (dopo il tema sonoro); ascolto di Vabax dei blocchi 3-6 e merge in ordine; prova su PC fisico; repository APT VabaxOS (v0.2).

Piano della notte del 2026-09-24, deciso con Vabax (lavoro autonomo fino al blocco 6; niente merge su `main` prima del suo ascolto, che fa domani per tutti i blocchi):

- Decisioni approvate da Vabax il 2026-09-24: ADR-0018 (menu Start con ArcMenu e logo, a condizione che Orca legga tutto) **Accettata**; scelta della voce (Kokoro predefinito se il PC supera la prova, altrimenti eSpeak; Sonic per la velocità; Piper escluso per ora) da scrivere come ADR-0019 **Accettata**; licenza di Kokoro accettata (modello Apache-2.0, librerie MIT; addestrato anche con audio di voci commerciali, da scrivere nell'ADR).
- Blocco 3 «Voce naturale e menu Start»: servizio Kokoro per speech-dispatcher (Sonic, cache, taglio silenzio, bassa latenza, interruzione), prova del PC al primo avvio, voce più veloce fra Sara e Nicola, scelta della voce in `vabaxos-setup`; ArcMenu con il logo.
- Blocco 4 «Il sistema installato»: pacchetti VabaxOS e voce nel sistema installato (preseed), prova automatica di installazione in QEMU con riavvio e voce, benvenuto solo al primo avvio, esportazione del log di avvio, voce senza Internet.
- Blocco 5 «Desktop accessibile e identità»: Orca con File, Terminale (`nmtui`), Impostazioni; spegnimento e riavvio con conferma letta; sospensione; **font uniformi, identità visiva unica (sfondi, animazioni, icone)**; **suoni di sistema: trovarne con licenza libera e generarne molti nostri, Vabax sceglie domattina**; **gestione batteria e risparmio energetico, Wi-Fi e Bluetooth accessibili**.
- Blocco 6 «Lettore di documenti»: programma GTK 4 che legge txt, PDF, EPUB, DOCX con Kokoro; navigazione per frase e paragrafo, velocità con Sonic, segnalibri, esportazione audio.
- Blocco 6, aggiunta di Vabax (2026-09-24, notte): **aggiornamenti** (come gestirli, come renderli rapidi, come l'utente aggiorna i componenti da solo in modo accessibile) e **sicurezza** (aggiornamenti di sicurezza, firme, repository APT Vabax, ADR-0015). Per le scelte che spettano a Vabax: ADR «Proposta».
- Regola della notte (Vabax): **poco tempo sulle ISO**. Una costruzione per blocco al massimo, ma le prove sempre: test unitari, Broadway, `test-boot.sh` sulla ISO del blocco.

Idee e richieste di Vabax (2026-09-24), da riprendere al momento giusto:

- Menu Start del desktop: una via di mezzo fra il menu Start di Windows 7 e il menu Apple di macOS. GNOME non ha un menu Start: serve un ADR (estensione o programma Vabax) quando si arriva al desktop.
- Suoni di sistema: valutare quelli di GNOME (licenze) oppure crearne di nuovi per VabaxOS (`vabaxos-branding`, temi sonori di DOC-01 §33).
- Più lingue: per Vabax è importante. Lingua dell'interfaccia e della voce separate; una lingua nuova deve richiedere solo le sue traduzioni.
- Problema noto da verificare: con GNOME 50, Orca in Firefox ed Electron a volte legge solo le etichette (vedi ADR-0017).
- Voce: Vabax non ama eSpeak NG («fa schifo»), anche se tono, volume e velocità vanno bene. ADR-0006 prevede Piper opzionale dalla v0.3. Piper non è in Debian; le voci italiane hanno licenze da verificare (paola: dati CC0 ma addestrata da lessac, licenza solo ricerca; riccardo: M-AILABS). MBROLA escluso (licenza non commerciale). Ascolto del 2026-09-24: Vabax trova Piper «riccardo» e «paola» molto meglio di eSpeak («sembrano umani»), con qualche parola letta male (sigle come «txt»). Riccardo ha dati M-AILABS con licenza tipo BSD-3: si può distribuire. Poi Vabax ha sentito Kokoro (Apache-2.0; voci italiane Sara e Nicola): «un altro mondo», riccardo al confronto «tagliato, più artificiale». Vabax vuole Kokoro predefinito, senza modelli ridotti (qualità). Limite: circa 0,3-0,8 s per frase anche breve (Piper 0,06 s), obiettivo dei lettori di schermo sotto 0,2 s (issue hexgrad/kokoro#291). Piano per il blocco 3 (ADR da proporre): servizio speech-dispatcher VabaxOS con modello caricato, cache in RAM e sul disco delle frasi di Orca e GNOME, frasi spezzate, interruzione immediata, misura al primo avvio: Kokoro se il PC è veloce, altrimenti Piper riccardo; eSpeak sempre come riserva. Licenza: addestrato anche con audio di voci commerciali, da scrivere nell'ADR. Prove in scratchpad (`kokoro-onnx` 0.6.1, EspeakConfig con la libreria di sistema). Decisione di Vabax (2026-09-24): al primo avvio si misura il PC; Kokoro se supera i requisiti, altrimenti Piper, altrimenti eSpeak; la console resta eSpeak. Requisiti proposti: Kokoro con frase breve nuova pronta entro circa 0,3 s (soglia da fissare con l'ascolto di Vabax con Orca), almeno 8 GB di RAM, 1 GB di disco (misurati 570 MB di RAM); Piper entro 0,1 s e 4 GB (misurati 150 MB). Scelta manuale sempre possibile nelle impostazioni della voce. Ascolti successivi (2026-09-24, frasi tipiche di Orca): Kokoro Nicola a velocità alta (speed 1.43) si mangia le parole, ma sintetizzato a 1.0 e accelerato con libsonic (quella di espeak-ng, via ctypes) «ha retto bene»: usare sempre Sonic per la velocità. Riccardo perde la lettera finale anche con punto finale e volume fisso, e suona «distante»: **scartato come predefinito**. Scala: Kokoro se il PC ce la fa, altrimenti eSpeak. Kokoro serve anche per un lettore di documenti a voce naturale (studio). Voce Kokoro predefinita: la più veloce fra Sara e Nicola, misurata (decisione di Vabax). Rimedi al ritardo, presi anche da NVDA: taglio del silenzio iniziale (Kokoro ne mette 0,2-0,27 s) e finale, audio PipeWire a bassa latenza, modello sempre caricato, interruzione immediata. Da misurare a macchina libera: frasi spezzate alle virgole, cache delle parole fisse di Orca, runtime C++/Rust di Kokoro.
- Logo: scelto da Vabax (logo 1). Deve essere anche il simbolo del menu Start. Licenza provvisoria `LicenseRef-VabaxOS-Trademark` finché non ci sono le regole del marchio.

Note pratiche:

- **Prima di ogni blocco cerca online i problemi noti e le soluzioni già esistenti** (richiesta di Vabax): il blocco 1 è stato lento perché i problemi audio sono emersi uno alla volta.
- Verifica la voce senza orecchie prima di chiamare Vabax: `scripts/test-boot.sh` registra l'audio e fallisce se benvenuto, console o Orca sono muti; `scripts/run-qemu.sh --record-audio FILE` e `scripts/lib/wav-timeline.py` per le prove a mano.
- `test-boot.sh` risponde al benvenuto con i tasti prima di entrare dalla console seriale: un accesso durante il benvenuto cambierebbe l'audio.
- Non modificare uno script mentre è in esecuzione (per esempio `build.sh` o `test-boot.sh`): Bash lo legge a pezzi.
- Una costruzione con GNOME dura circa 12 minuti (di più la prima volta dopo un cambio di distribuzione o di snapshot).

## Dove trovare le cose

- `README.md`, `ROADMAP.md`, `ARCHITECTURE.md`, `BUILD.md`, `GOVERNANCE.md`
- `docs/decisions/`: gli ADR
- `docs/specs/`: DOC-01–32, i documenti originali
- `docs/sviluppo/`: guida alla postazione e prompt di avvio
- `scripts/postazione/`: preparazione e verifica della postazione
- `.github/workflows/checks.yml`: la CI
