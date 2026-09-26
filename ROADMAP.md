# Roadmap di VabaxOS

Questa è la roadmap operativa. La versione originale completa, con tutti i requisiti fino alla v2.0, è [DOC-01](docs/specs/01_VabaxOS_Roadmap_v0.1-v1.0.txt): questa pagina la riassume e la aggiorna con le decisioni prese negli [ADR](docs/decisions/README.md).

**Nessuna data è promessa.** Una versione esce quando supera i suoi criteri.

## Traguardi

| Versione | Nome | Obiettivo |
|---|---|---|
| **v0.1** | Proof of Concept | ISO live che si avvia, parla e arriva al desktop |
| v0.2 | Core System | Repository APT Vabax, recupero, aggiornamenti, `vabaxctl` |
| v0.3 | Accessibility Alpha | Profilo Orca Vabax completo, Braille, voce Piper opzionale |
| v0.4 | Desktop Alpha | Centro Accessibilità Vabax, identità del desktop, impostazioni |
| v0.5 | Installer Alpha | Installazione autonoma provata con persone cieche |
| v0.6 | Hardware & Networking | Matrice hardware, database di compatibilità |
| v0.7 | Applications | Vabax Store con metadati di accessibilità, Flatpak |
| v0.8 | Accessibility Beta + Gaming | Test profondi su browser, ufficio e giochi |
| v0.9 | Release Candidate | Blocco delle funzioni, stabilità |
| v1.0 | Stable | Distribuzione usabile ogni giorno su x86-64 |
| v2.0 | Multi-architecture | ARM64, Chromebook, Mac |

## v0.1 — Proof of Concept

**Obiettivo:** infilare la chiavetta → sentire la voce → configurare → arrivare al desktop, senza vedere lo schermo e senza mouse. Prima in QEMU, poi su almeno un PC fisico (non la postazione di sviluppo).

### Criteri di accettazione

Ogni punto diventerà un caso di test in `tests/`. I punti segnati con ★ correggono problemi segnalati da utenti ciechi sulla ISO live GNOME di Debian trixie (lista debian-accessibility, maggio 2026).

**Avvio**

- [ ] La ISO si avvia in UEFI, anche con Secure Boot attivo (ADR-0003). *Provato in QEMU con `scripts/test-boot.sh`; manca il PC fisico.*
- [ ] La ISO si avvia in modalità BIOS legacy. *Provato in QEMU; manca il PC fisico.*
- [ ] ★ Il menu di avvio emette un segnale acustico quando è pronto. *In QEMU con UEFI Vabax ha sentito due bip ravvicinati (2026-09-24); manca il PC fisico.*
- [ ] Senza premere nulla, dopo il tempo di attesa si avvia «VabaxOS (con voce)». *Provato in QEMU (10 secondi); manca il PC fisico.*
- [ ] Il menu offre «senza voce», «Installa con sintesi vocale» e «Modalità di recupero con voce». *«Senza voce» (N) e «recupero» (R) ci sono e sono provati in QEMU; «Installa» arriva con il lavoro 9.*

**Voce**

- [ ] ★ I messaggi della console vengono letti (Speakup + espeakup). *Provato in QEMU con `test-boot.sh`, che registra l'audio, e ascoltato da Vabax (2026-09-24); manca il PC fisico.*
- [ ] La voce funziona senza connessione a Internet. *eSpeak NG gira in locale; manca una prova con la rete staccata.*
- [ ] ★ Orca parte da solo nella sessione live, in italiano con eSpeak NG. *In italiano quando la lingua è scelta nel menu o nel benvenuto (ADR-0016); in inglese altrimenti.* *Provato in QEMU con `test-boot.sh`, che registra l'audio, e ascoltato da Vabax (2026-09-24); manca il PC fisico.*
- [ ] ★ Super+Alt+S accende e spegne Orca.
- [ ] ★ Dal desktop si passa a una console testuale con voce e si torna indietro. *Provato in QEMU con `test-boot.sh`, che registra l'audio, e ascoltato da Vabax (2026-09-24); manca il PC fisico.*

**Configurazione e desktop**

- [ ] ★ Il tour di GNOME non compare. Al suo posto parte la configurazione iniziale Vabax, tutta da tastiera: lingua, voce e velocità, tastiera, rete Wi-Fi. *Il tour non è più installato e il benvenuto parlato chiede lingua, voce e tastiera (ADR-0016); manca la rete, con la configurazione iniziale (lavoro 8).*
- [ ] Dal desktop si aprono, da tastiera e con Orca: menu applicazioni, terminale, file manager, impostazioni.
- [ ] ★ Il terminale viene letto da Orca, anche con programmi come `nmtui`.
- [ ] ★ Nella sessione live la sospensione automatica è disattivata. Dopo una sospensione manuale Orca riprende a parlare, oppure il difetto è documentato. *Disattivata da `vabaxos-settings`; manca la prova della sospensione manuale.*
- [ ] Spegnimento e riavvio si fanno da tastiera con conferma letta.

**Installazione e hardware**

- [ ] ★ L'installer con sintesi vocale contiene il firmware non libero necessario (Wi-Fi, audio).
- [ ] Il sistema installato in una VM si riavvia con la voce attiva.
- [ ] Il log dell'avvio si esporta in un file di testo.

**Costruzione**

- [x] `./scripts/build.sh` produce la ISO, `SHA256SUMS`, il manifest e un log datato.
- [ ] La CI costruisce la ISO e la avvia in QEMU (test di fumo senza interfaccia).
- [ ] Due costruzioni con la stessa data di snapshot producono lo stesso squashfs. *Vero per due costruzioni sulla postazione; manca una ricostruzione indipendente.*

### Lavori della v0.1

Ogni lavoro diventerà una issue su GitHub, con il modello «Lavoro».

1. Guida alla postazione Windows: WSL2 Debian, QEMU, audio e KVM (ADR-0013). **Fatto:** [guida](docs/sviluppo/postazione-windows.md) collaudata sulla postazione di Vabax.
2. Scheletro di live-build in `image/` e `scripts/build.sh` (ADR-0002). **Fatto:** ISO minima che arriva alla console, con `scripts/test-boot.sh`.
3. `scripts/run-qemu.sh`: UEFI, Secure Boot, audio. **Fatto:** UEFI, Secure Boot e BIOS provati; audio verificato ascoltando il bip del menu.
4. Menu di avvio parlante: segnale acustico, voci del menu, attesa (ADR-0014). **Fatto:** due bip, menu in inglese con scelta della lingua (L), lettere V, N, R, T, attesa di 10 secondi, [guida](docs/utente/menu-di-avvio.md). Il menu GRUB non può parlare: la voce parte con il sistema (lavoro 5).
5. Voce in console: Speakup + espeakup attivi nella live. **Fatto** (`vabaxos-accessibility`), anche in modalità di recupero.
5b. Benvenuto parlato «Benvenuto in VabaxOS»: lingua, poi prova, installa, voce e tastiera, riavvia, spegni (ADR-0016). **Fatto** (`vabaxos-welcome`, [guida](docs/utente/benvenuto.md)); «Installa» arriva con il lavoro 9.
6. Orca automatico in sessione e in GDM, italiano, eSpeak NG. **Fatto** su GNOME 50 e Orca 50 (ADR-0017), con un solo server audio per tutte le voci ([architettura](ARCHITECTURE.md)).
7. Pacchetto `vabaxos-settings`: tour disattivato, sospensione disattivata in live, valori predefiniti. **Fatto.**
8. Configurazione iniziale Vabax (GTK 4): lingua, voce, tastiera, rete.
9. Installer Debian con sintesi vocale e firmware, preseed per i pacchetti Vabax (ADR-0007).
10. CI: costruzione della ISO e test di avvio in QEMU.
11. Prima prova su PC fisico e scheda hardware.

### Come si chiude la v0.1 (deciso con Vabax il 2026-09-26)

La v0.1 comprende anche i blocchi 13 e 14, prima previsti per la v0.2. Ordine del lavoro:

1. **Correzioni della notte** (PR #18): CI verde, poi unione a `main`.
2. **Blocco 13, aggiornamenti VabaxOS** ([ADR-0020](docs/decisions/0020-aggiornamenti-e-sicurezza.md)): archivio APT firmato su GitHub Pages di questo repository; due chiavi (archivio, firmata dalla CI; versioni ufficiali, solo sul computer di Vabax); pacchetto con la chiave e le sorgenti; `vabaxos-update` anche dall'archivio; date di snapshot.debian.org provate ogni settimana dalla CI prima di pubblicarle; nessun aggiornamento automatico; `vabaxctl` (stato, voce, aggiornamenti, rapporto).
3. **Blocco 14, Internet con Orca:** Firefox ESR e Thunderbird provati a fondo con Orca (pagine, moduli, posta, tasti come NVDA nel web), prove automatiche su pagine di esempio. Se il difetto di GNOME 50 (Orca che in Firefox legge solo le etichette) resta, la v0.1 esce lo stesso, con il difetto e il modo di aggirarlo nelle note.
4. **Blocco 15, menu Start e sicurezza:** il menu Start di VabaxOS per tutti, ArcMenu tolto, anche con il mouse, con una casella di ricerca sulla barra quando è chiuso, come in Windows 11 ([ADR-0025](docs/decisions/0025-menu-start-vabaxos.md)); firewall ufw attivo per default ([ADR-0021](docs/decisions/0021-firewall-e-cifratura.md)); segnalazioni dei difetti trovati a GNOME, Orca, ArcMenu e Debian.
5. **Prova di Vabax in VMware sul mini PC** con la ISO da `main` (scelta di Vabax: VMware invece della chiavetta). I criteri qui sopra che dicono «manca il PC fisico» si considerano provati con VMware per la v0.1; la prova da chiavetta resta per una versione successiva.
6. **Uscita:** `v0.1.0-alpha.1` come pre-release su GitHub, con la ISO e `SHA256SUMS` firmato con la chiave delle versioni ufficiali, solo dopo il sì finale di Vabax. Lingue: italiano e inglese.

La cifratura del disco resta per la v0.2, con voce e segnale alla richiesta della password.

## Dopo la v0.1

I dettagli delle versioni successive sono in [DOC-01](docs/specs/01_VabaxOS_Roadmap_v0.1-v1.0.txt) (sezioni 7–16 e 67–86) e nel piano dei primi 12 mesi [DOC-32](docs/specs/32_Execution_Plan_First_12_Months.md). Gaming, supporto ARM e Mac, API di accessibilità Vabax e shell propria restano fuori dal primo traguardo, come già deciso in DOC-32.
