# VabaxOS — Trust, Transparency & Accountability Plan

| Campo | Valore |
|---|---|
| ID | VABAX-DOC-27 |
| Versione | 0.1.0 |
| Stato | Piano proposto — applicazione progressiva |
| Data | 2026-09-24 |
| Ambito | Credibilità tecnica, comunicazione, dati e responsabilità |

## 1. Fondamento della fiducia

La fiducia non si costruisce con una frase di marketing ma con comportamenti verificabili: si dice la verità sullo stato, si correggono errori pubblicamente, si pubblicano fonti/test/limiti, si tratta bene chi segnala problemi e si rende chiaro chi governa codice e fondi. Il fondatore porta esperienza e responsabilità; persone cieche e disabili devono avere influenza reale sul design e non servire solo come testimonianza promozionale.

## 2. Impegni pubblici

- Roadmap e registro decisioni con owner, data, alternative e stato.
- Release note con difetti noti, hardware/AT testati e limiti di supporto.
- Codice sorgente, licenze, SBOM e provenienza degli artefatti secondo la fase.
- Policy sicurezza privata, risposta coordinata e avvisi pubblici per vulnerabilità risolte.
- Privacy by default: no telemetry personale senza scopo, minimizzazione e consenso.
- Pagina “What VabaxOS can/cannot do” aggiornata per versione.
- Registro finanziario aggregato: entrate, spese, fee e allocazione, quando si accettano fondi progetto.
- Postmortem senza colpevolizzare per incidenti di release o dati.

## 3. Evidenza di affidabilità

Per un'affermazione pubblica conservare claim → versione → test/evidenza → data → responsabile. Esempio: “installazione testata con NVDA/Orca su modello X” richiede report riproducibile; non prova tutte le configurazioni. Dichiarare “build riproducibile” solo dopo una ricostruzione indipendente byte-for-byte secondo definizione del progetto Reproducible Builds.

## 4. Processo di feedback e reclamo

Canali distinti per bug pubblico, accessibilità, privacy, sicurezza riservata e fondi. Confermare ricezione, assegnare owner, rendere visibile lo stato e comunicare la risoluzione in un formato accessibile. Nessun utente deve essere obbligato a rendere pubblico il proprio nome o la disabilità per segnalare una barriera.

## 5. Trasparenza sui rischi

Comunicare che v0.1 può perdere dati/rompersi, non va installata su macchina primaria, e che Linux non garantisce driver per ogni dispositivo. Le schermate marketing non sostituiscono evidenze accessibilità. Pubblicare regressioni note e versioni interessate senza creare falsa sicurezza.

## 6. Indicatori

Percentuale release con note/known issues, sicurezza ricevuta e triage, difetti A0 risolti con evidenza, release ritirate/corrette, percentuale spese rendicontate, test user completati e risposte a feedback. Nessun punteggio singolo per “fiducia”.

## 7. Criteri di accettazione

Prima di alpha pubblica: governance e contatti visibili; security policy; privacy note; pagina stato e download verificabili; limiti accessibilità; codice licenziato; registro issue pubblico e regole comunità. Prima di accettare fondi continuativi: destinazione, titolare legale/fiscale e reporting definiti.

## Riferimenti

- [GitHub private vulnerability reporting](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting)
- [Reproducible Builds definition](https://reproducible-builds.org/docs/definition/)
- [SPDX](https://spdx.dev/)
- DOC-09 Licensing; DOC-10 Security; DOC-12 Release Engineering; DOC-29 Funding.

## Cronologia

- 0.1.0 — 2026-09-24: piano iniziale.
