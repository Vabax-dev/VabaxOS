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

- [ ] La ISO si avvia in UEFI, anche con Secure Boot attivo (ADR-0003).
- [ ] La ISO si avvia in modalità BIOS legacy.
- [ ] ★ Il menu di avvio emette un segnale acustico quando è pronto.
- [ ] Senza premere nulla, dopo il tempo di attesa si avvia «VabaxOS (con voce)».
- [ ] Il menu offre «senza voce», «Installa con sintesi vocale» e «Modalità di recupero con voce».

**Voce**

- [ ] ★ I messaggi della console vengono letti (Speakup + espeakup).
- [ ] La voce funziona senza connessione a Internet.
- [ ] ★ Orca parte da solo nella sessione live, in italiano con eSpeak NG.
- [ ] ★ Super+Alt+S accende e spegne Orca.
- [ ] ★ Dal desktop si passa a una console testuale con voce e si torna indietro.

**Configurazione e desktop**

- [ ] ★ Il tour di GNOME non compare. Al suo posto parte la configurazione iniziale Vabax, tutta da tastiera: lingua, voce e velocità, tastiera, rete Wi-Fi.
- [ ] Dal desktop si aprono, da tastiera e con Orca: menu applicazioni, terminale, file manager, impostazioni.
- [ ] ★ Il terminale viene letto da Orca, anche con programmi come `nmtui`.
- [ ] ★ Nella sessione live la sospensione automatica è disattivata. Dopo una sospensione manuale Orca riprende a parlare, oppure il difetto è documentato.
- [ ] Spegnimento e riavvio si fanno da tastiera con conferma letta.

**Installazione e hardware**

- [ ] ★ L'installer con sintesi vocale contiene il firmware non libero necessario (Wi-Fi, audio).
- [ ] Il sistema installato in una VM si riavvia con la voce attiva.
- [ ] Il log dell'avvio si esporta in un file di testo.

**Costruzione**

- [ ] `./scripts/build.sh` produce la ISO, `SHA256SUMS`, il manifest e un log datato.
- [ ] La CI costruisce la ISO e la avvia in QEMU (test di fumo senza interfaccia).
- [ ] Due costruzioni con la stessa data di snapshot producono lo stesso squashfs.

### Lavori della v0.1

Ogni lavoro diventerà una issue su GitHub, con il modello «Lavoro».

1. Guida alla postazione Windows: WSL2 Debian, QEMU, audio e KVM (ADR-0013).
2. Scheletro di live-build in `image/` e `scripts/build.sh` (ADR-0002).
3. `scripts/run-qemu.sh`: UEFI, Secure Boot, audio.
4. Menu di avvio parlante: segnale acustico, voci del menu, attesa (ADR-0014).
5. Voce in console: Speakup + espeakup attivi nella live.
6. Orca automatico in sessione e in GDM, italiano, eSpeak NG.
7. Pacchetto `vabaxos-settings`: tour disattivato, sospensione disattivata in live, valori predefiniti.
8. Configurazione iniziale Vabax (GTK 4): lingua, voce, tastiera, rete.
9. Installer Debian con sintesi vocale e firmware, preseed per i pacchetti Vabax (ADR-0007).
10. CI: costruzione della ISO e test di avvio in QEMU.
11. Prima prova su PC fisico e scheda hardware.

## Dopo la v0.1

I dettagli delle versioni successive sono in [DOC-01](docs/specs/01_VabaxOS_Roadmap_v0.1-v1.0.txt) (sezioni 7–16 e 67–86) e nel piano dei primi 12 mesi [DOC-32](docs/specs/32_Execution_Plan_First_12_Months.md). Gaming, supporto ARM e Mac, API di accessibilità Vabax e shell propria restano fuori dal primo traguardo, come già deciso in DOC-32.
