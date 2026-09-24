# VabaxOS — Release Engineering & Versioning

| Campo | Valore |
|---|---|
| ID | VABAX-DOC-12 |
| Versione | 0.1.0 |
| Stato | Bozza — cadenza, supporto e signing TBD |
| Data | 2026-09-23 |
| Dipendenze | DOC-01, DOC-04, DOC-06, DOC-07, DOC-09, DOC-10 |

## 1. Scopo e schema versioni

La roadmap definisce v0.1–v0.9, v1.0 stabile e v2.x per ARM/Chromebook/Mac. Proposta semver per componenti software; per la distribuzione mantenere `major.minor.patch`, con canali alpha, beta, RC e stable espliciti. Non confondere versione documento, versione OS, kernel, repository e formato immagine.

## 2. Canali e gate

| Canale | Uso | Gate minimo |
|---|---|---|
| Nightly | integrazione interna | build attribuita, test smoke automatici |
| Alpha | prototipo instabile | note limiti, suite essenziale, niente uso dati primari |
| Beta | prova ampia | regressione/accessibilità, hardware/app matrix aggiornata |
| RC | candidato release | zero blocker aperti, update/recovery e artefatti firmabili |
| Stable | distribuzione supportata | approvazione release, SBOM/notices, advisory e support window |

La frequenza, support duration/LTS e criteri numerici sono TBD. La v0.1 è proof-of-concept, non una stable support promise.

## 3. Pipeline release

Freeze manifest e dipendenze → build isolata/versionata → test QA/accessibilità e compatibilità → generare ISO/pacchetti/SBOM/checksum → review licenze/sicurezza → firma con chiave custodita → publish note e known issues → monitorare difetti/advisory. Conservare commit, tool versions, build log, environment, hash, SBOM e provenance.

## 4. Naming e artefatti

Proposta: `VabaxOS-<version>-<channel>-x86_64-<date>.iso`; verificare che nome/architettura/canale coincidano con manifest. Pubblicare hash tramite canale autenticato; una firma digitale va distribuita con fingerprint e procedura di verifica accessibile. Contenuti di release: note, requisiti hardware, limiti accessibilità, known issues, upgrade/recovery e licenze.

## 5. Supporto update e rollback

Documentare componenti aggiornati e sicurezza; testare upgrade da versioni supportate e interruzione; stabilire compatibilità dati/configurazioni e rollback. Snapshot Btrfs e update atomici sono idee da valutare, non presupposti. Definire durata supporto, policy EOL e gestione mirror prima di v1.0.

## 6. Hotfix e incidenti

Ogni hotfix ha issue, severità, commit/release note e regressione mirata. Vulnerabilità pubblica segue disclosure coordinata e avviso accessibile. Ritiro artefatto compromesso, rotazione chiavi e comunicazione utenti richiedono runbook e owner nominati.

## 7. Criteri di accettazione release

La release ha gate QA DOC-07; matrice hardware e accessibilità aggiornata; licenze/SBOM complete; ISO attribuita e checksum/firma verificabili; recovery e known issues; note accessibili; approvazione e archivio immodificabile. Cadenza, chiavi e infrastruttura sono prerequisiti da deliberare.

## 8. Decisioni aperte

Semver OS o schema distro-specifico; canali e cadenza; LTS; repository; chiavi e custodia; firma ISO/pacchetti; criteri di promozione; rollback; support window; firma trasparente delle build e retention.

## Riferimenti

- [systemd: steps to a successful release](https://systemd.io/RELEASE/)
- [Linux kernel development process](https://docs.kernel.org/process/)
- [SPDX specifications](https://spdx.dev/use/specifications/)
- [Sigstore documentation](https://docs.sigstore.dev/)

## Cronologia

- 0.1.0 — 2026-09-23: schema iniziale; nessuna policy release definitiva.
