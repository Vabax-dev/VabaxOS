# VabaxOS — Project Governance & Management Plan

| Campo | Valore |
|---|---|
| ID | VABAX-DOC-23 |
| Versione | 0.1.0 |
| Stato | Piano operativo proposto — da ratificare dal fondatore |
| Data | 2026-09-24 |
| Ambito | Governance, priorità, decisioni, responsabilità, milestone |

## 1. Mandato

VabaxOS mira a essere un sistema operativo general-purpose basato su Linux, progettato fin dall'inizio per essere utilizzabile da persone con e senza disabilità. L'ambizione è creare un sistema “per tutti” con accessibilità incorporata, non promettere ora il miglior sistema operativo al mondo né compatibilità universale. Il successo si dimostra tramite autonomia, stabilità, sicurezza, prestazioni misurate, compatibilità documentata e fiducia della comunità.

## 2. Modello di governo per fasi

### Fase A — progetto guidato dal fondatore

Il fondatore conserva responsabilità finale su visione, roadmap, budget, partnership e approvazione pubblica. Nomina per ogni area un owner anche se all'inizio la stessa persona copre più ruoli. Nessuna approvazione tecnica o di sicurezza viene delegata a un output AI senza review e prova.

### Fase B — nucleo di maintainer

Quando esistono contributori continuativi, creare un gruppo di 3–5 maintainer con competenze di sistema/build, accessibilità/UX, sicurezza/release e community. Definire mandato, durata, conflitti d'interesse, quorum, successione e processo di ricorso prima di concedere poteri irreversibili.

### Fase C — ente o fiscal host

Valutare struttura legale o fiscal host solo quando fondi, contratti, assunzioni, proprietà intellettuale o responsabilità lo rendono necessario; verificare obblighi con consulenti in Italia/UE. Non costituire un ente solo per apparenza.

## 3. Ruoli e accountability

| Area | Owner iniziale | Responsabilità |
|---|---|---|
| Product/Project Lead | Fondatore | visione, priorità, scope, relazioni e approvazione roadmap |
| Architecture | Architetto nominato | ADR, interfacce, consistenza tecnica |
| Engineering/Build | Maintainer tecnico | repository, pipeline, build e review |
| Accessibility | Lead accessibilità + co-ricercatori | requisiti, test AT e barriera triage |
| Security/Release | Security/release owner | vulnerabilità, firme, gate release |
| Community/Finance | Owner nominato | contributi, codice condotta, fondi e report |

In partenza alcune responsabilità possono ricadere sul fondatore; registrare esplicitamente i conflitti e chiedere revisione esterna per sicurezza, licenze e fondi.

## 4. Cadenza e strumenti

- Un backlog pubblico con issue ID, owner, priorità, milestone, stima/rischio e criteri d'accettazione.
- Riunione interna quindicinale di 30–45 minuti quando c'è un team; aggiornamento pubblico mensile di stato.
- Review mensile di rischi, capacity, dipendenze, accessibilità e spese.
- ADR per decisioni con impatto su architettura, sicurezza, licenza, dati o compatibilità; non ogni dettaglio richiede ADR.
- Limite WIP proposto: non più di 3 milestone attive; completare il verticale v0.1 prima di espandere scope.

## 5. Priorità e controllo delle modifiche

Valutare ogni proposta su: impatto autonomia/accessibilità, numero di utenti, rischio sicurezza/dati, costo manutenzione, dipendenze, licenza, prova riproducibile e coerenza con milestone. Non aggiungere funzionalità solo perché innovative. Requisiti che cambiano devono aggiornare DOC-04/05, test e roadmap. Un cambiamento di obiettivo passa da proposta → analisi → decisione → versione documento → implementazione → evidenza.

## 6. Dashboard mensile

Misurare milestone passate/ritardo; requisiti A0 verificati; blocker aperti per gravità; build riuscite e riproducibilità; macchine/app testate; contributori attivi e tempo di review; spese/entrate e mesi runway; feedback utenti e barriere chiuse. Non usare download o stelle come sostituti dell'autonomia.

## 7. Primo piano concreto

**Settimana 1:** approvare charter sintetico, owners (anche “fondatore”), backlog e scope v0.1. **Settimana 2:** nominare 3 obiettivi prioritari, pubblicare decisioni aperte e canale contatti. **Ogni mese:** aggiornare stato pubblico, rischi, budget e prossime prove. **Gate:** non annunciare una release se non sono disponibili criteri e risultati verificabili.

## 8. Decisioni aperte

Forma futura di governance; repository e strumenti; owner reali; disponibilità oraria; escalation; nomina maintainer; uso pubblico di metriche; approvazione budget; necessità di ente/host. Questi elementi sono deliberazioni del progetto, non assunzioni.

## 9. Riferimenti interni

DOC-01 Roadmap; DOC-07 QA; DOC-08 Development Standards; DOC-19 AI Workflow; DOC-22 Master Specification.

## Cronologia

- 0.1.0 — 2026-09-24: piano di governance iniziale.
