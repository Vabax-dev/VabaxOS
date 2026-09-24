# VabaxOS — Developer Onboarding Guide

| Campo | Valore |
|---|---|
| ID | VABAX-DOC-21 |
| Versione | 0.1.0 |
| Stato | Bozza — istruzioni legate alla workstation attuale |
| Data | 2026-09-23 |
| Dipendenze | DOC-01, DOC-02, DOC-06, DOC-08, DOC-19 |

## 1. A chi serve

Per nuovi contributori che vogliono capire progetto, preparare workstation e produrre un change verificabile. Questa guida non sostituisce la guida tecnica Windows (DOC-02) né un futuro `CONTRIBUTING.md` nel repository software.

## 2. Prima di iniziare

Leggere in ordine DOC-01 roadmap, README/master index, DOC-03 architettura, DOC-04 requisiti, DOC-05 accessibilità, DOC-06 decisioni base/build, DOC-07 QA e DOC-08 standards. Consultare ADR e issue aperte prima di scegliere stack o codificare. Chiedere chiarimento via issue se requisito non è assegnato.

## 3. Ambiente di riferimento

La workstation definita è Windows 11 + NVDA + WSL2 Ubuntu 24.04 LTS + Git + VS Code Remote WSL + QEMU. Seguiri DOC-02 per installazione, collocazione repo nel filesystem Linux WSL, compilazione, ISO e test QEMU. Versioni tool e ambiente vanno registrate. Non installare prototipi VabaxOS sul PC principale.

## 4. Primo contributo

1. Ottenere repository e issue; non lavorare su `main`.
2. Confermare scope e acceptance criteria.
3. Leggere dipendenze documentate e ADR; proporre ADR per decisione mancante.
4. Creare branch legato all'issue; implementare change piccolo.
5. Eseguire test pertinenti e registrare comandi/esiti.
6. Verificare keyboard/AT, licenze, segreti e docs se applicabile.
7. Aprire PR con contesto, test, rischi e note release.

## 5. Sicurezza e accessibilità del contributo

Non pubblicare credenziali, dati utente o dump non redatti. Non assumere che una schermata funzionante visivamente sia utilizzabile; fornire semantica AT, ordine focus, shortcut, localizzazione e comportamento errore. Dipendenze nuove richiedono licenza e provenance. I comandi distruttivi si eseguono solo in VM/hardware esplicitamente dedicato.

## 6. Primi task suggeriti

Documentare toolchain e versione; creare test automatizzati per manifest; aggiungere un caso accessibilità; raccogliere una scheda hardware; replicare build/boot QEMU; rivedere upstream license. Nessuno di questi sceglie base distro senza DOC-06 ADR.

## 7. Checklist onboarding

- [ ] Accessibilità workstation pronta e testata.
- [ ] Repo clonato nel filesystem WSL.
- [ ] Issue/owner e criteri capiti.
- [ ] Branch creato, nessun secret aggiunto.
- [ ] Build/test riproducibili o impedimento segnalato.
- [ ] Evidenza keyboard/AT e licenza aggiornata.
- [ ] PR e documentazione compilate.

## 8. Decisioni aperte

Repository URL, licenza progetto, accesso GitHub, CI, code review, contributi esterni, supporto hardware/test lab, canali di comunicazione e processo di onboarding sono TBD.

## Riferimenti

- [Windows Development Environment](02_VabaxOS_Windows_Development_Environment.txt)
- [Development Standards](08_Development_Standards.md)
- [Git documentation](https://git-scm.com/doc)
- [Linux kernel contribution process](https://docs.kernel.org/process/)

## Cronologia

- 0.1.0 — 2026-09-23: guida iniziale.
