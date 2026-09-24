# VabaxOS — Requirements Specification

| Campo | Valore |
|---|---|
| ID | VABAX-DOC-04 |
| Versione | 0.1.0 |
| Stato | Bozza tecnica — requisiti proposti, non baseline approvata |
| Data | 2026-09-23 |
| Ambito | Requisiti funzionali, qualità, compatibilità e verifica |
| Dipendenze | Roadmap v0.1–v1.0 e Windows Development Environment citati nella conversazione, ma non presenti nel workspace; DOC-03 e DOC-05 |

## 1. Scopo e convenzioni

Questo documento trasforma gli obiettivi della roadmap tecnica VabaxOS v0.1–v1.0 in requisiti identificabili e verificabili. I requisiti sono proposte per una baseline v0.1; priorità, release target e soglie quantitative vanno ratificate. **MUST** è un criterio obbligatorio per accettare il requisito dopo l'approvazione della baseline; **SHOULD** è raccomandato e può essere derogato con motivazione; **TBD** indica decisione/soglia da stabilire. Le righe non diventano impegni di release solo perché sono scritte qui.

Priorità: **P0** fondazione/prototipo; **P1** esperienza desktop utilizzabile; **P2** evoluzione e compatibilità estesa. Le fasi sono orientative e vanno allineate alla roadmap originale.

## 2. Principi e ambito

VabaxOS deve perseguire accessibilità integrata, uso da tastiera, localizzazione, affidabilità, privacy, sicurezza, compatibilità Linux e possibilità di evolvere verso gioco e più architetture. Le prime prove devono avvenire in ambiente virtuale prima dell'installazione su hardware fisico. La preview cita Windows 11, WSL2/Ubuntu, Git, VS Code, toolchain C/C++/Python/Rust, CMake/Ninja e QEMU: sono elementi di contesto per la workstation, non dipendenze runtime o scelte definitive della distro.

Fuori baseline finché non deciso: supporto a ogni GPU/dispositivo; compatibilità universale con software Linux/Windows; installazione in dual boot; ARM64 nella prima release; certificazione di conformità normativa; garanzia di accessibilità di applicazioni di terzi non controllate.

## 3. Requisiti di sistema

### Baseline esplicita v0.1 dalla roadmap

La roadmap definisce v0.1 come Proof of Concept, non OS completo: ISO Live x86-64; boot UEFI; Linux kernel e init system; rilevamento hardware essenziale; audio e TTS offline; screen reader attivo; configurazione iniziale accessibile; Wi-Fi; selezione/creazione utente; desktop con menu applicazioni, terminale, file manager e impostazioni; spegnimento/riavvio; logging di base. La verifica deve coprire VM e almeno un PC fisico. Il risultato atteso è ISO → boot → voce → configurazione minima → desktop.

I componenti proposti nella roadmap per la base includono systemd, Wayland/XWayland, AT-SPI2, PipeWire/WirePlumber e NetworkManager; restano soggetti alla verifica e agli ADR previsti. La guida di sviluppo definisce come workstation Windows 11 + WSL2 + Ubuntu 24.04 LTS, Git/GitHub, VS Code Remote WSL, toolchain Linux e QEMU; questi non sono requisiti runtime del sistema.


| ID | Pri. | Requisito verificabile | Verifica proposta |
|---|---:|---|---|
| SYS-001 | P0 | La v0.1 deve avviarsi come ISO Live x86-64 in una VM UEFI (target fissato dalla roadmap). | Avvio pulito UEFI in QEMU; registrare configurazione e log, quindi ripetere il test su almeno un PC fisico compatibile. |
| SYS-002 | P0 | Ogni build candidata deve riportare versione, commit sorgente, manifest delle dipendenze e checksum degli artefatti. | Ispezione metadata e confronto tra build. |
| SYS-003 | P0 | Un errore critico di servizio deve essere registrato e reso diagnosticabile senza richiedere l'interfaccia grafica. | Iniettare servizio fallito; verificare log e procedura recovery. |
| SYS-004 | P1 | Installazione, aggiornamento e recovery devono offrire feedback comprensibile e percorso da tastiera/AT. | Test DOC-05 su VM; matrice esiti. |
| SYS-005 | P1 | L'utente deve poter scegliere installazione/uso live senza che il flusso di prova sovrascriva il disco per default. | Test VM con disco di controllo e conferme. |

## 4. Requisiti funzionali

### Accesso, sessioni e desktop

| ID | Pri. | Requisito | Verifica |
|---|---:|---|---|
FUN-001 | P0 | Il sistema deve fornire un percorso documentato dal boot alla prima sessione utilizzabile, indicando esplicitamente i limiti pre-boot. | Test guidato da tastiera e screen reader. |
| FUN-002 | P0 | Le funzioni del prototipo devono essere navigabili da tastiera; ogni controllo deve esporre nome, ruolo, stato e azione quando applicabile. | Ispezione AT + test manuale. |
| FUN-003 | P1 | Il desktop deve supportare più finestre e task concorrenti, con passaggio di focus annunciato e recuperabile. | Sequenza multi-finestra documentata. |
| FUN-004 | P1 | Cambio workspace, minimizza, massimizza, snap, dialoghi e notifiche devono avere operazioni equivalenti da tastiera. | Test funzionale e AT. |
| FUN-005 | P1 | Mouse e touchpad devono essere opzionali per l'uso delle funzioni essenziali; le funzioni puntatore devono avere alternative da tastiera ove applicabile. | Checklist per attività essenziali. |

### Accessibilità e personalizzazione

| ID | Pri. | Requisito | Verifica |
|---|---:|---|---|
FUN-010 | P0 | Il servizio di screen reader scelto deve poter essere avviato e fermato con modalità definita e feedback accessibile. | Test avvio/stop e recupero AT. |
| FUN-011 | P1 | Voce/TTS, lingua interfaccia, lingua AT, layout tastiera e formato regionale devono essere impostazioni distinguibili. | Cambiare singolarmente e verificare dopo logout/reboot. |
| FUN-012 | P1 | Il sistema deve offrire controlli per suoni, notifiche, velocità/volume della sintesi e profili accessibilità; valori e motori sono TBD. | Test persistenza e stato annunciato. |
| FUN-013 | P1 | Devono essere valutate Sticky Keys, Slow Keys, Bounce Keys e altre funzioni di accesso; l'insieme MVP è TBD. | Decisione registrata e test input. |
| FUN-014 | P2 | Braille, controllo vocale, OCR/descrizione immagini e profili avanzati devono essere valutati senza essere promessi finché hardware, privacy e lingue non siano verificati. | ADR e test specifici, se inclusi. |

### Applicazioni, localizzazione, rete e manutenzione

| ID | Pri. | Requisito | Verifica |
|---|---:|---|---|
| FUN-020 | P1 | Applicazioni incluse o sviluppate dal progetto devono rispettare la specifica DOC-05 e dichiarare i limiti noti. | Audit accessibilità e issue list. |
| FUN-021 | P1 | L'interfaccia deve essere progettata per localizzazione; italiano e inglese sono candidati iniziali dalla roadmap preview, ma le lingue di release vanno confermate. | Test locale per lingua e overflow. |
| FUN-022 | P1 | Operazioni essenziali di file, impostazioni, terminale, software installabile e rete devono essere verificabili senza mouse. | Test attività e tastiera. |
| FUN-023 | P1 | Installazione, aggiornamenti e pacchetti devono verificare integrità/provenienza secondo il modello scelto. | Artefatto non valido rifiutato o segnalato. |
| FUN-024 | P2 | Compatibilità con pacchetti/formati Linux e giochi Proton/Wine è obiettivo di ricerca; per ogni formato supportato deve esistere una matrice di test e limiti. | Matrice versionata e test per campione. |
| FUN-025 | P2 | Profili gaming e performance non devono alterare impostazioni accessibilità senza consenso esplicito e ripristino. | Test passaggio profilo e rollback. |

## 5. Qualità e vincoli non funzionali

| ID | Categoria | Criterio proposto | Misura/soglia |
|---|---|---|---|
NFR-001 | Accessibilità | Tutti i flussi P0 devono essere verificati senza puntatore e con AT abilitata. | 100% casi P0 superati; soglia di release da approvare. |
| NFR-002 | Affidabilità | Boot, login, avvio/stop AT, apertura impostazioni e recovery si ripetono senza blocchi. | Numero di cicli e timeout TBD; registrare ambiente. |
| NFR-003 | Prestazioni | Avvio, latenza TTS e reattività desktop devono essere misurati su VM e hardware target. | Obiettivi numerici TBD dopo baseline hardware. |
| NFR-004 | Sicurezza | Aggiornamenti/artifacts devono avere provenienza e verifica d'integrità. | Verifiche automatizzate e test rifiuto artefatto alterato. |
| NFR-005 | Manutenibilità | Ogni componente non banale deve avere fonte, versione, licenza, patch e owner documentati. | Inventario release completo. |
| NFR-006 | Localizzazione | Nessuna stringa utente deve essere bloccata in un'unica lingua nel software Vabax. | Lint/inspection e test pseudo-localizzazione. |
| NFR-007 | Compatibilità | Le regressioni vanno confrontate con hardware/VM e applicazioni elencati in una matrice versionata. | Matrice e report legati alla release. |
| NFR-008 | Privacy | Funzioni online, telemetria e diagnostica devono essere descritte e configurabili secondo decisione di policy. | Review privacy e test impostazioni; policy TBD. |

## 6. Vincoli e dipendenze

- Dipendenze esterne candidate: kernel Linux; stack display e input; AT-SPI2/toolkit; motore TTS e screen reader; firmware/driver; sistema di build; repository e chiavi; QEMU per la prima verifica.
- Non fissare versione di distribuzione, kernel, desktop, TTS, motori, pacchetti o target hardware fino a ADR e verifica upstream.
- Il documento Windows Development Environment descrive una workstation, mentre questa specifica descrive il prodotto; WSL2, VS Code e tool della workstation non sono requisiti installati su VabaxOS.
- Le fonti upstream e i vincoli di licenza devono essere riesaminati per ogni release, poiché evolvono.

## 7. Tracciabilità e accettazione

Ogni requisito implementato deve collegarsi a issue/commit, test, esito e requisito DOC-05 correlato. Una release candidata può essere dichiarata accettata solo con: baseline approvata; test P0 e P1 applicabili passati o deroghe documentate; difetti bloccanti risolti; artefatti identificati; limiti noti e istruzioni accessibili.

Modello di test case: `TC-ID`, requisito, prerequisiti, passi riproducibili, expected result, actual result, ambiente, versione build, esito, evidenze e difetti collegati.

## 8. Riferimenti ufficiali

- [Linux kernel documentation](https://docs.kernel.org/) — build, API e testing.
- [Wayland protocol](https://wayland.freedesktop.org/docs/book/Protocol.html) — display, input e data transfer.
- [AT-SPI2 development guide](https://gnome.pages.gitlab.gnome.org/at-spi2-core/devel-docs/index.html) — infrastruttura AT.
- [GTK Accessibility](https://docs.gtk.org/gtk4/section-accessibility.html) — semantica accessibile toolkit.
- [Debian Live project](https://www.debian.org/devel/debian-live/) — riferimento da considerare per l'immagine live.
- Riferimenti generali della workstation nella conversazione: Microsoft WSL, QEMU e Git for Windows; link ufficiali puntuali da associare alla copia del documento Windows Development Environment quando archiviata nel repository.

## 9. Cronologia

- 0.1.0 (2026-09-23): prima bozza, requisiti derivati dalla preview della roadmap e marcati come baseline da approvare.
