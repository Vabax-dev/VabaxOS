# VabaxOS — Testing & QA Plan

| Campo | Valore |
|---|---|
| ID | VABAX-DOC-07 |
| Versione | 0.1.0 |
| Stato | Bozza operativa — piano e soglie da approvare |
| Data | 2026-09-23 |
| Ambito | Verifica di requisiti, accessibilità, immagini, compatibilità e release |
| Dipendenze | DOC-03/04/05/06; roadmap originale e Windows Development Environment |

## 1. Scopo

Stabilire un ciclo verificabile per dimostrare che le funzioni VabaxOS lavorano, restano accessibili e non introducono regressioni. Il piano copre sviluppo, integrazione, immagini di prova e release. QEMU è il primo ambiente indicato nella conversazione; i test VM non sostituiscono test su hardware reale.

## 2. Principi QA

La roadmap fissa un criterio di successo minimo per v0.1: ISO Live x86-64 → boot UEFI → voce/TTS offline → configurazione minima accessibile → desktop, con prova in VM e su almeno un PC fisico compatibile. La guida di sviluppo individua QEMU come laboratorio principale e prescrive di verificare prima la VM, poi l'hardware fisico; per l'ISO va registrato almeno il checksum e la build deve essere diagnosticabile.


- Ogni requisito approvato ha almeno un metodo di verifica e un test case o motivazione di non testabilità.
- L'accessibilità si verifica nei flussi reali con tastiera e AT, non solo tramite scanner.
- I test sono ripetibili: versione artefatto, commit, configurazione, lingua, hardware/VM e tool sono registrati.
- I test distruttivi e d'installazione sono limitati a dischi VM o hardware di laboratorio dichiarato.
- Le prove di compatibilità distinguono testato, non testato, bloccato e non supportato.
- Un test instabile è tracciato come tale; non si elimina senza causa e owner.
- Ogni difetto include passi di riproduzione, impatto, log accessibile e requisito interessato.

## 3. Livelli di test

| Livello | Scopo | Esempi |
|---|---|---|
| Unit | Logica isolata e confini errore | parser configurazioni, profili, shortcut map |
| Component | Interazione di servizio/API | broker AT, localizzazione, audio settings |
| Integration | Stack con componenti upstream | compositor + toolkit + AT-SPI + screen reader |
| System/image | Avvio e funzioni prodotto | boot, login, desktop, rete, aggiornamento |
| Accessibility | Usabilità da tastiera/AT e semantica | focus, dialoghi, annunci, errori |
| Compatibility | Hardware e applicazioni | QEMU, GPU/hardware campione, app versionate |
| Security/provenance | Integrità e controllo accesso | firma/hash, update interrotto, manifest |
| User validation | Task realistici con utenti | test consensuali e issue prioritarie |

## 4. Strategia per ambiente

### Ambiente workstation canonico

Per riprodurre le procedure della guida, lo sviluppatore usa Windows 11, WSL2, Ubuntu 24.04 LTS, Git e VS Code Remote WSL; repository/build Linux risiedono preferibilmente nel filesystem WSL, mentre QEMU è il laboratorio. Annotare versioni effettivamente installate, non assumere che due workstation siano identiche. Questo ambiente non è il target QA finale.


### CI/host di build

Eseguire lint, unit/component test, scansione dipendenze e produzione manifest per ogni change dove l'infrastruttura lo consente. L'host CI, il sistema di build e le soglie non sono ancora selezionati. Nessun requisito si considera coperto solo perché la compilazione termina.

### VM QEMU

Configurazione di riferimento iniziale da fissare in DOC-06: firmware UEFI, CPU/RAM/disk, display/input/audio virtuali, rete e accelerazione. Conservare configurazione macchina e comando d'avvio. Eseguire boot, installazione su disco vuoto VM, avvio AT, sessione, riavvio, update/recovery e raccolta log.

### Hardware reale

Solo dopo gate VM; usare un elenco di macchine con modello, firmware, CPU/GPU, Wi-Fi, audio, touchpad, display e dispositivi assistivi. Testare da supporto live e disco separato o macchina di laboratorio. Il PC Windows principale non è target di installazione finché il proprietario non dispone di un piano esplicito e l'installer non ha superato i gate; questo riflette il contesto della conversazione, non un limite architetturale.

## 5. Suite minima per ogni immagine candidata

### Gate obbligatorio v0.1 dalla roadmap

Dimostrare tutti i seguenti passaggi sulla build candidata: ISO Live x86-64 e boot UEFI; audio e TTS funzionanti offline; screen reader attivo; configurazione iniziale da tastiera/AT; Wi-Fi e selezione/creazione utente; sessione desktop, menu, terminale, file manager e impostazioni; shutdown/reboot; logging di base. Eseguire l'intera prova prima in VM e poi su almeno un PC fisico compatibile, riportando l'hardware esatto. Le parti non ancora implementate sono gap di roadmap, non pass.


1. Verifica hash, manifest, firma/provenienza secondo la strategia approvata.
2. Avvio UEFI in QEMU da immagine live senza scrittura intenzionale al disco.
3. Scelta di lingua/layout disponibile, navigazione senza mouse, avvio AT/TTS quando implementati.
4. Test navigazione desktop: finestre, focus, dialoghi, impostazioni, notifiche, input e terminale.
5. Test rete/audio/storage e reazione a dispositivo mancante o servizio fallito.
6. Installazione su disco VM vuoto, riavvio e test boot installato; verificare anche annullamento e conferma distruttiva.
7. Test update riuscito e interrotto; verificare rollback/recovery se implementato.
8. Confronto con regressioni note, smoke test applicazioni e raccolta log.
9. Aggiornare compatibilità, difetti noti, limiti accessibilità e decisioni di rilascio.

Elementi non implementati restano “non applicabile/non disponibile”, non “pass”. La suite e le soglie di release devono essere approvate quando esiste il primo prototipo.

## 6. Accessibilità QA

Per i test A0 seguire DOC-05: tastiera senza puntatore; AT e versione nominate; annunci/focus attesi confrontati; prova di ritorno da dialogo; errore e recovery; almeno una lingua supportata dal prototipo. Registrare screenshot solo se aggiunge evidenza, insieme a trascrizione testuale accessibile. Per test utente ottenere consenso informato, minimizzare dati e restituire esiti in formato utilizzabile dal team.

### Criteri di passaggio proposti

- 100% test P0 applicabili superati, oppure blocco release.
- Zero difetti S0/S1 aperti (definizioni nella sezione 8), salvo deroga formale motivata per ogni flusso.
- Difetti A0 aperti bloccano la dichiarazione di release accessibile.
- I test falliti o saltati sono visibili nel report e non vengono omessi dal conteggio.
- Copertura di applicazioni/hardware è dichiarata con versione e ambiente.

## 7. Versioni, logging e report

Ogni run deve includere: `test_run_id`, data/ora UTC, commit, release candidato, hash ISO, manifest/SBOM se disponibile, host build, configurazione QEMU o hardware, lingua, AT/TTS, suite e commit dei test, esito e link issue. Log possono contenere dati personali: filtrare credenziali e contenuti utente prima di conservarli o condividerli.

Modello difetto: titolo; impatto/gravità; ambiente; prerequisiti; passi; risultato atteso/osservato; riproducibilità; log; requisito; workaround; regressione sì/no; owner; milestone.

## 8. Gravità e triage

| Livello | Definizione | Esempio |
|---|---|---|
| S0 Critical | perdita dati, compromissione o blocco generalizzato che rende impossibile avvio sicuro | immagine non avviabile, update distruttivo |
| S1 Blocker | flusso A0 impossibile senza alternativa accessibile, o installazione/aggiornamento non recuperabile | AT non avviabile e nessun percorso alternativo |
| S2 Major | funzione primaria degradata con workaround accessibile | focus perso in impostazioni, ma percorso alternativo disponibile |
| S3 Minor | difetto circoscritto senza blocco attività essenziale | annuncio ridondante non critico |

Gravità e priorità di correzione si registrano separatamente. Il triage documenta decisione, owner, versione interessata e impatto per utenti assistivi.

## 9. Gestione release e Definition of Done

Una feature è “Done” quando requisiti e design sono collegati; implementazione reviewata; test automatizzati e manuali applicabili passati; test accessibilità DOC-05 completati; localizzazione e documentazione aggiornate; dipendenze/licenze registrate; log/error handling sufficienti; difetti aperti classificati; artefatto identificabile.

Una release candidata richiede inoltre: suite immagine completata; test di aggiornamento/recovery applicabili; matrice compatibilità; elenco known issues accessibile; provenienza dell'artefatto; approvazione del responsabile release. Firma, pipeline CI, support period e processo di rollback restano decisioni da stabilire in DOC-06/ADR.

## 10. Dipendenze e rischi di copertura

- Senza base e build system selezionati non si possono congelare comandi e pipeline CI.
- QEMU non riproduce tutti i problemi GPU, firmware, sleep, Bluetooth, Braille, Wi-Fi o audio reale.
- I test screen reader dipendono dalla combinazione di sessione, compositor, toolkit e API AT.
- La compatibilità di giochi e applicazioni varia per versione, driver, GPU e aggiornamenti upstream.
- Non si deve confondere test tecnico con test di usabilità o conformità normativa.

## 11. Riferimenti ai sorgenti di progetto

La roadmap tecnica v0.1–v1.0 stabilisce il target e i gate di prodotto; la guida Windows Development Environment versione 1.0 stabilisce il laboratorio WSL2/Ubuntu 24.04 + QEMU, la posizione del repository e il flusso di build/test. Entrambe datate 23 settembre 2026. In caso di differenza, registrare la configurazione realmente usata e aprire una correzione documentale invece di assumere che l'ambiente corrisponda.

## 12. Riferimenti ufficiali

- [Linux kernel testing guide](https://docs.kernel.org/dev-tools/testing-overview.html) e [documentazione kernel](https://docs.kernel.org/) — test, strumenti e fault injection.
- [AT-SPI2 development guide](https://gnome.pages.gitlab.gnome.org/at-spi2-core/devel-docs/index.html) — infrastruttura testabile per accessibilità.
- [Documentazione QEMU](https://www.qemu.org/docs/master/) — configurazione di virtualizzazione; i comandi Windows/WSL citati nell'ambiente vanno verificati per host specifico.
- [Debian Live project](https://www.debian.org/devel/debian-live/) — riferimento per immagini live se selezionato.
- [systemd testing documentation](https://systemd.io/CONTRIBUTING/) — pratiche upstream da consultare se systemd verrà scelto.

## 13. Cronologia

- 0.1.0 (2026-09-23): prima bozza di piano QA con soglie proposte e gate da approvare.
