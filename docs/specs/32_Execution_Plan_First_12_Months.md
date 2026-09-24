# VabaxOS — Piano di esecuzione: primi 12 mesi

| Campo | Valore |
|---|---|
| ID | VABAX-DOC-32 |
| Versione | 0.1.0 |
| Stato | Piano proposto a gate — nessuna promessa di data release |
| Data | 2026-09-24 |
| Ambito | Sequenza iniziale tra governo, ricerca, prototipo e apertura pubblica |

## 1. Premessa

Questo è un piano da seguire e ricalibrare ogni mese, non una previsione garantita. Disponibilità oraria del fondatore, team, budget, hardware e repository non sono ancora noti; le date sono finestre indicative. Non si dichiara v1.0 entro l'anno. Il gate tecnico v0.1 proviene dalla roadmap: ISO Live x86-64/UEFI, boot → TTS offline → configurazione → desktop, VM e almeno un PC fisico.

Gli strumenti Vabax per Windows e macOS sono già in sviluppo secondo il fondatore. Questo piano li tratta come filoni paralleli, con roadmap e gate propri; il piano dei 12 mesi qui sotto è per VabaxOS e non ne presume scadenze o condivisione del team.

## 2. Priorità assolute

1. Chiarire governance minima e proprietà progetto.
2. Chiudere ricerca/ADR della base, build, desktop, boot, screen reader e TTS.
3. Creare repository e pipeline riproducibile in WSL2/QEMU.
4. Dimostrare un verticale accessibile prima di allargare scope.
5. Reclutare tester e costruire fiducia pubblicando prove e limiti.

Gaming, API proprietarie, supporto Mac/ARM, app store e desktop completamente custom restano fuori dal primo verticale.

## 3. Fasi e gate

### Mese 1 — Fondazione pubblica e operativa

Approvare DOC-22/23/24, scope v0.1, owner, issue board, policy community/sicurezza/licenze. Preparare pagina VabaxOS su vabax.it come pagina “in sviluppo”, repository origin e canale contatti. **Gate G1:** ogni deliverable ha owner, stato e criterio; nessuna campagna finanziaria senza piano DOC-29.

### Mesi 2–3 — Decisioni e validazione architetturale

Chiudere ADR base userspace/build system e prove preliminari per boot, sessione grafica, AT-SPI2/Orca, PipeWire/TTS offline. Costruire matrice toolchain in WSL e una VM QEMU accessibile. Consultare primo gruppo utenti. **Gate G2:** PoC documentato che parla prima del desktop oppure decisione tecnica motivata su un'altra catena; rischi e costi identificati.

### Mesi 4–6 — Vertical slice v0.1

Implementare boot UEFI x86-64, audio/TTS offline, screen reader iniziale, first-run keyboard/AT e desktop minimo. Test unit/component/integration, almeno QEMU; definire PC fisico di prova e non usare macchina primaria. **Gate G3:** ISO avviabile e task end-to-end superati in VM; blocchi A0 aperti hanno owner.

### Mesi 7–9 — Alpha controllata

Provare su PC fisico campione; rete, account, terminale, file manager, settings, shutdown; raccogliere bug e performance. Pubblicare alpha solo con checksum/notes/known issues/security contact, e invitare gruppo pilota esplicito. **Gate G4:** v0.1 alpha ripetibile, nessun blocker critico irrisolto o comunicazione chiara che il test è solo laboratorio.

### Mesi 10–12 — Stabilizzazione e piano v0.2

Correggere accessibilità/boot; consolidare release pipeline, source provenance, licenze e hardware database iniziale; produrre report trasparenza/finanza; decidere milestone v0.2 e capacità team. **Gate G5:** revisione indipendente su rischi, supporto e sostenibilità; se i prerequisiti non sono passati si prolunga alpha, non si accelera il marketing.

## 4. Cadenza operativa

Ogni settimana: una priorità tecnica principale e un aggiornamento backlog; ogni mese: release/status note, dashboard e review dei rischi; ogni milestone: design review, accessibilità review e retrospettiva. Limitare lavoro parallelo e tenere un buffer per regressioni.

## 5. Budget e capacità

Prima di definire date, stimare: ore founder/week; ore engineering; devices/test hardware; tester paid; hosting/build; legal/accounting; support/maintenance. Ogni milestone ha stima optimistic/likely/pessimistic e dipendenze. Se capacità scende, ridurre scope o allungare calendario, mai rimuovere gate accessibilità/sicurezza senza decisione e disclosure.

## 6. Scorecard mese 12

- Demo end-to-end v0.1 su QEMU e almeno un PC compatibile.
- Quota task A0 passati per requisiti effettivamente implementati.
- Numero e severità barriere A0 aperte/risolte.
- Build/test ripetibili con versioni/manifest e hash.
- Hardware, lingue, AT e app realmente testati.
- Contributori/tester che hanno completato attività e sono tornati.
- Ore e fondi spesi rispetto a budget; runway/support obligations.
- ADR e limiti pubblici aggiornati.

## 7. Stop/continue criteria

Sospendere la pubblicazione se boot/test distrugge dati; la voce offline non funziona; la provenienza o licenza è ignota; vulnerabilità critica non mitigata; tester senza consenso; supporto promesso non finanziabile. Proseguire al gate successivo solo con evidenze, owner e budget realistici.

## 8. Decisioni da prendere ora

Owner effettivi; tempo settimanale; repository; primo hardware PC; budget massimo autorizzato dal fondatore; criteri v0.1; calendario di co-design; data di pubblicazione pagina; responsabile security contact.

## Riferimenti interni

DOC-01, DOC-06, DOC-07, DOC-12, DOC-23, DOC-25, DOC-26, DOC-29, DOC-30.

## Cronologia

- 0.1.0 — 2026-09-24: piano 12 mesi a gate, date e risorse da validare.
- Nota 2026-09-24: separati i filoni Windows/macOS già in sviluppo dal critical path VabaxOS.
