# VabaxOS — Master Specification & Document Control

| Campo | Valore |
|---|---|
| ID | VABAX-DOC-22 |
| Versione | 0.2.0 |
| Stato | Indice normativo di raccolta — bozza, non approvato come baseline |
| Data | 2026-09-24 |
| Proprietario | Project Architect / Project Lead da confermare |

## 1. Scopo

Questo documento è il punto di ingresso e tracciabilità del corpus VabaxOS. Non duplica le singole specifiche né trasforma candidature in decisioni. Le priorità e le release restano quelle della roadmap, salvo change approvato e registrato in ADR.

## 2. Indice canonico

| N. | Documento | Funzione | Stato |
|---:|---|---|---|
| 01 | Roadmap v0.1–v1.0 | Visione, release e requisiti ampi | Bozza sorgente |
| 02 | Windows Development Environment | Workstation di sviluppo accessibile | v1.0 |
| 03 | Architecture Specification | Modello e confini architetturali | Bozza 0.1.0 |
| 04 | Requirements Specification | Requisiti verificabili | Bozza 0.1.0 |
| 05 | Accessibility Specification | Esperienza e verifica accessibile | Bozza 0.1.0 |
| 06 | Build System & Base Distribution Decision | Matrice e ADR base/build | Decisione aperta |
| 07 | Testing & QA Plan | Strategia di verifica | Bozza 0.1.0 |
| 08 | Development Standards | Contributi, codice, Git e review | Bozza 0.1.0 |
| 09 | Open Source & Licensing Policy | Componenti, licenze e SBOM | Bozza 0.1.0 |
| 10 | Security Specification | Modello minacce e requisiti | Bozza 0.1.0 |
| 11 | Hardware Compatibility Specification | Tier e matrice hardware | Bozza 0.1.0 |
| 12 | Release Engineering & Versioning | Canali, gate e artefatti | Bozza 0.1.0 |
| 13 | Package & Application System | Pacchetti, app e compatibilità | Bozza 0.1.0 |
| 14 | Vabax Accessibility API | Estensioni accessibilità Vabax | Esplorativa |
| 15 | Vabax Screen Reader | Requisiti del lettore vocale | Specifica in bozza |
| 16 | Installer Specification | Flusso installazione accessibile | Bozza 0.1.0 |
| 17 | Desktop Specification | Shell e superfici desktop | Bozza 0.1.0 |
| 18 | Gaming Specification | Giochi, runtime e accessibilità gaming | Bozza di visione |
| 19 | AI Development Workflow | Ruoli e ciclo assistito | Bozza operativa |
| 20 | Troubleshooting & Recovery Manual | Diagnosi e ripristino | Bozza operativa |
| 21 | Developer Onboarding Guide | Avvio nuovi contributori | Bozza 0.1.0 |
| 22 | Master Specification | Indice e controllo documentale | Questo documento |
| 23 | Project Governance & Management Plan | Ruoli, decisioni e gestione milestone | Piano proposto |
| 24 | Product Vision & Excellence Framework | Posizionamento, qualità e promesse misurabili | Proposta |
| 25 | Distribution & Adoption Plan | Canali, gate, download, update e supporto | Proposta |
| 26 | vabax.it Integration Plan | Presenza web e distinzione progetto/persona | Proposta; nessuna modifica live |
| 27 | Trust & Transparency Plan | Evidenze, privacy, incidenti e accountability | Proposta |
| 28 | Community & Contributor Plan | Onboarding, governance comunità e inclusione | Proposta |
| 29 | Sustainability & Funding Plan | Costi, fonti fondi, rendicontazione e gate | Preliminare; nessuna piattaforma scelta |
| 30 | Accessible Co-Design & User Research Plan | Ricerca, consenso e test con utenti | Protocollo proposto |
| 31 | Partnerships & Ecosystem Plan | Upstream, enti, hardware e collaborazioni | Proposta; nessun partner impegnato |
| 32 | First 12 Months Execution Plan | Sequenza e gate del primo anno | Piano proposto, nessuna data garantita |

La conversazione elencava Development Standards come 07 e QA come 11; in seguito l'utente ha ordinato il primo pacchetto 03–07 con Testing & QA al 07. Il corpus mantiene tale ordine esplicito e colloca Development Standards al numero 08, preservando i nomi e contenuti richiesti senza sovrascrivere il documento già creato.

## 3. Precedenza e gestione conflitti

La roadmap DOC-01 governa obiettivi e milestone approvati; DOC-03 governa architettura dopo ratifica; DOC-04 requisiti; DOC-05 comportamento accessibile; DOC-06 registra decisione base/build; DOC-07 governa test/release evidence. Se due documenti confliggono, aprire issue di document control e ADR/change request: non risolvere per inferenza durante l'implementazione. DOC-02 è fonte dell'ambiente di sviluppo, non runtime dell'OS.

## 4. Stati documentali

- **Draft:** contenuto in revisione, non vincolante.
- **Proposed:** proposta con alternative e prove mancanti.
- **Approved:** approvato da owner e data, applicabile a release indicate.
- **Superseded:** sostituito da versione/documento successivo con collegamento.

Ogni decisione architetturale o di policy ha ID, owner, alternative, evidenza, conseguenze e data di riesame. Un requisito approvato ha ID stabile e metodo di verifica.

## 5. Principi comuni

Accessibility First; voce offline al bootstrap; x86-64 v0.1/v1.0 e ARM64/Chromebook/Mac in serie 2.x secondo roadmap; software open source e licensing reviewed; test VM prima e PC reale per milestone richieste; non dichiarare universalità hardware o accessibilità senza matrice; privilegiare componenti upstream; nessuna scelta TBD viene presentata come definitiva.

## 6. Decisioni bloccanti per v0.1

Secondo DOC-01: base userspace; build system; desktop; installer per fasi in cui richiesto; strategia Orca/Vabax SR; TTS e voci; packaging; filesystem; boot manager. Definire owner e ADR prima del gate di implementazione. Gate dimostrativo: ISO Live x86-64 UEFI → voce/TTS offline → configurazione accessibile → desktop, test in VM e almeno un PC fisico compatibile.

## 7. Change control e release del corpus

Aggiornare la cronologia, revisione e matrice tracciabilità a ogni change; incrementare patch per correzioni editoriali, minor per requisiti/addizioni compatibili, major per cambi incompatibili (schema proposto, non policy approvata). Pubblicare ZIP e manifest file/hash solo dopo review dei contenuti e controllo link. Ogni release del sistema archivia la revisione corpus usata.

## 8. Piani di realizzazione e sostenibilità

DOC-23–32 traducono la visione in gestione, posizionamento, distribuzione, comunicazione, fiducia, comunità, finanziamento, co-design, partnership e piano operativo. Sono proposte da ratificare: non creano impegni legali, finanziari o promesse di release. DOC-26 descrive una proposta per vabax.it; nessuna modifica live è stata eseguita.

## 9. Deliverable operativi successivi

ADR effettivi, repository software e README/CONTRIBUTING/SECURITY operativi; threat model dettagliato; matrice requisiti-test; SBOM per build; hardware compatibility database; traduzioni; tutorial utente; runbook release e verifiche fiscali/legali. Si creano quando esistono owner, dati e decisioni verificabili.

## Riferimenti interni

- Tutti i DOC-01–DOC-32 elencati sopra.
- [Architecture Decision Records (ADR)](06_Build_System_and_Base_Distribution_Decision.md) — DOC-06 contiene il registro decisioni iniziale; repository ADR dedicato da creare.

## Cronologia

- 0.1.0 — 2026-09-23: primo indice master e regole document control.
- 0.2.0 — 2026-09-24: estensione al corpus 32 documenti e piani di realizzazione.
