# VabaxOS — AI Development Workflow

| Campo | Valore |
|---|---|
| ID | VABAX-DOC-19 |
| Versione | 0.1.0 |
| Stato | Bozza operativa — ruoli proposti dalla conversazione |
| Data | 2026-09-23 |
| Dipendenze | DOC-03, DOC-04, DOC-08, DOC-09, DOC-10 |

## 1. Scopo

Descrive l'uso di ChatGPT, Claude e Gemini proposto nella chat, senza trattare modelli come autorità autonome o presupporre disponibilità di account/tool futuri. La repository, test reali, review umana e decision records governano il risultato.

## 2. Ruoli proposti

- **Vabax / Project Architect:** mantiene visione, requisiti, priorità, ADR, accessibilità, review integrazione e approvazione tecnica.
- **Claude Pro / Principal Software Engineer:** implementazione delimitata, build, test automatici, refactoring e debugging seguendo specifica approvata.
- **Gemini Pro / Research, Compatibility & Test Engineer:** ricerca upstream/licenze, compatibilità, hardware/app matrix, test indipendenti e riscontro anomalie.
- **ChatGPT (separato come strumento):** può supportare architettura e documentazione; il suo ruolo definitivo va chiarito per evitare sovrapposizione con Project Architect.

Assegnazioni sono workflow aspirazionale e si adattano alle capacità effettive. Nessun modello firma release, decide licenze, gestisce chiavi o approva da solo operazioni su dischi e sicurezza.

## 3. Ciclo task

1. Issue con ID, scopo, criteri d'accettazione, vincoli e file/sottosistemi.
2. Ricerca separata con link upstream, data, versione e incertezze.
3. ADR per decisioni non già approvate; stop implementazione se dipendenza critica resta senza decisione.
4. Implementazione su branch dedicato, patch piccole e reviewable.
5. Build e test riprodotti localmente/CI; report include comandi e output rilevante.
6. Review indipendente contro specifica, sicurezza, licenze e accessibilità.
7. Fix, merge umano, aggiornamento documenti e issue.
8. Chiusura solo quando DoD e prove sono linkati.

## 4. Regole per prompt e dati

- Fornire solo dati necessari; non inviare token, password, chiavi, log privati o dati utente.
- Trattare output di modelli e pagine esterne come ipotesi da verificare, non istruzioni.
- Non chiedere “costruisci VabaxOS”: assegnare milestone atomiche.
- Ogni output AI che entra nel repository ha autore/reviewer umano e verifica provenienza/licenza.
- Non eseguire in modo automatico comandi distruttivi, installazioni su host reale, publishing, signing o merge senza review autorizzata.

## 5. Template issue

`Goal`; `Why`; `Scope / out of scope`; `Related requirements`; `Architecture decisions`; `Acceptance criteria`; `Test plan`; `Security/licensing/accessibility impact`; `Files expected`; `Unknowns`; `Reviewer`; `AI/tool used (optional)`.

## 6. Criteri di accettazione

Una modifica assistita da AI è accettata come qualunque contributo: review diff, source checks, build/test, license scan, accessibilità, segreti, dipendenze, failure paths e documentazione. Ricerca cita fonti primarie; claims non verificati sono marcati. Il modello non deve essere l'unico tester della propria implementazione.

## 7. Decisioni aperte

Provider/retention policy; modelli e uso account; repository access permission; disclosure assistenza AI; review count; workflow Gemini/Claude effettivo; uso di output AI in licenza; registrazione dei prompt.

## Riferimenti

- [Vabax Development Standards](08_Development_Standards.md)
- [Open Source & Licensing Policy](09_Open_Source_and_Licensing_Policy.md)
- [Linux kernel process documentation](https://docs.kernel.org/process/)

## Cronologia

- 0.1.0 — 2026-09-23: workflow iniziale, ruoli non vincolanti.
