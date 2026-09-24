# VabaxOS — Distribution & Adoption Plan

| Campo | Valore |
|---|---|
| ID | VABAX-DOC-25 |
| Versione | 0.1.0 |
| Stato | Piano proposto — canali e responsabilità da approvare |
| Data | 2026-09-24 |
| Ambito | Distribuire ISO, raggiungere utenti, aggiornare e assistere |

## 1. Strategia

Non cominciare dalla distribuzione di una “distro completa”. Distribuire prove crescenti: prototipo privato → alpha pubblica → beta per gruppi di test → release stabile. Ogni download ha requisiti hardware, stato, versione, checksum, firma quando disponibile, istruzioni di verifica, accessibilità nota, recovery e canale feedback.

## 2. Canali e fasi

| Fase | Pubblico | Artefatto | Condizione di pubblicazione |
|---|---|---|---|
| Interna | maintainer | VM image/ISO | build ripetibile entro team, nessun dato reale |
| Alpha | volontari tecnici e accessibilità | ISO UEFI x86-64 | flussi A0 identificati, note rischi, checksum, report issue |
| Beta | gruppi pilota | ISO/install media | test hardware più ampio, upgrade/recovery, supporto definito |
| Stable | pubblico generale | ISO + aggiornamenti | gate DOC-07/12, security/licensing, support policy e release approval |

GitHub Releases è candidato iniziale per sorgenti/artefatti; `vabax.it` deve essere pagina canonica di spiegazione e collegamento, non storage autonomo non versionato. Mirroring va aggiunto solo per disponibilità e con checksum coerenti.

## 3. Pagina download canonica

Per ogni release: nome/versione/data/channel; chi dovrebbe provarla; cosa funziona; hardware e architetture testati; requisiti; SHA-256 e firma/fingerprint; build/source commit; installazione/VM; note accessibilità; known issues; support lifecycle; security advisories; licenze; collegamento issue/report. Il flusso di verifica deve avere istruzioni solo tastiera/screen reader.

## 4. Modello aggiornamento

Distinguere update sicurezza, feature e firmware. Canali stable/beta non si mescolano; pacchetti e metadata autenticati; rollback/recovery testati; notifiche accessibili e rinviabili; finestra di manutenzione e supporto pubblici. L'infrastruttura concreta dipende da DOC-06 e DOC-12.

## 5. Diffusione e adozione

1. Racconto mensile “cosa abbiamo provato/cosa non funziona”.
2. Demo accessibile e registrazione con trascrizione/caption, usando hardware dichiarato.
3. Invito a gruppi mirati (utenti ciechi, educatori, Linux community, hardware tester) con attività piccole.
4. Collaborare upstream prima di mantenere patch divergenti.
5. Lavorare con enti/scuole solo dopo supporto, privacy e responsabilità definiti.
6. Raccogliere task completati e retention, non solo visite/download.

## 6. Modello di supporto

Community issue e FAQ sono canale best-effort per alpha; stable richiede owner, policy vulnerabilità, SLA/obiettivi realistici, EOL e fallback recovery. Non promettere supporto 24/7 o LTS finché non esistono risorse e copertura.

## 7. KPI e gate

Download verificati; installazioni riuscite dichiarate; issue riprodotte e risolte; quota test A0 passati; architetture/hardware Tier A; crash/recovery; utenti che tornano alla release successiva; spesa di hosting e supporto. Pubblicare metodo e limiti delle statistiche.

## 8. Decisioni aperte

Hosting artifact, firma e chiavi, mirrors, telemetry opt-in, update system, support window, target paesi, policy LTS, gestione account e assistenza.

## Riferimenti

- [Reproducible Builds — making plans](https://reproducible-builds.org/docs/plans/)
- [Definition of reproducible builds](https://reproducible-builds.org/docs/definition/)
- DOC-06 Build/Base; DOC-07 QA; DOC-10 Security; DOC-12 Release Engineering.

## Cronologia

- 0.1.0 — 2026-09-24: canali e processo proposti.
