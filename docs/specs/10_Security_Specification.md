# VabaxOS — Security Specification

| Campo | Valore |
|---|---|
| ID | VABAX-DOC-10 |
| Versione | 0.1.0 |
| Stato | Bozza — profilo di sicurezza da approvare |
| Data | 2026-09-23 |
| Dipendenze | DOC-03, DOC-04, DOC-06, DOC-08, DOC-09, DOC-12, DOC-13 |

## 1. Scopo e modello di minaccia

Definisce requisiti minimi per ridurre compromissione, perdita dati e update malevoli, senza promettere sicurezza assoluta. Asset: credenziali, dati utente, chiavi release, repository/build, boot chain e dispositivi assistivi. Avversari: software malevolo locale, pacchetto compromesso, supply-chain compromessa, perdita/furto dispositivo e abuso di privilegi. Secure Boot, cifratura e threat model di rete dipendono dall'hardware e restano da precisare.

## 2. Principi e requisiti

| ID | Requisito verificabile |
|---|---|
| SEC-001 | Servizi e applicazioni operano con privilegi minimi; privilegi elevati sono espliciti, limitati e loggati. |
| SEC-002 | Azioni amministrative hanno prompt e feedback accessibili; l'autenticazione non deve dipendere da un unico canale visivo o audio. |
| SEC-003 | Pacchetti e aggiornamenti verificano autenticità/integrità prima dell'applicazione; chiavi private non sono incluse in repo o immagini. |
| SEC-004 | Bootloader/kernel/module signing/Secure Boot hanno un piano di chiavi, rotazione, revoca e recovery prima di release firmate. |
| SEC-005 | Firewall e servizi di rete hanno default documentato, senza porte non necessarie; stato verificabile accessibilmente. |
| SEC-006 | Segreti non sono scritti in log; report di supporto sono minimizzati e condivisi solo con consenso. |
| SEC-007 | Cifratura disco è valutata per installer e recovery; LUKS2 è candidato della lista iniziale ma non approvato. |
| SEC-008 | Ogni vulnerabilità ha canale di segnalazione, triage, severità, remediation e advisory di release. |
| SEC-009 | Dipendenze, firmware e artefatti hanno versioni/provenienza; componenti non supportati sono identificati. |
| SEC-010 | Sandbox e portali non devono essere trattati come protezione assoluta; permessi e limiti sono visibili e documentati. |

## 3. Boot, account e autorizzazione

La roadmap propone UEFI, systemd-boot candidato e GRUB da valutare. Definire trust chain, comportamento con Secure Boot disattivo/non supportato, enrollment chiavi e istruzioni AT. Account standard per attività quotidiane; policy sudo/polkit, recovery admin, blocco schermo, sessioni remote e gestione credenziali sono TBD. Testare agent d'autorizzazione con tastiera e screen reader, timeout e messaggi ambigui.

## 4. Aggiornamenti e supply chain

Canale release separato da staging; artefatti firmati o verificati; manifest/SBOM; build provenance; protezione chiavi e approvazione multipla quando praticabile. Update falliti devono mantenere un percorso di boot/recovery. Firma e rollback non sono realizzati solo da checksum: documentare quale minaccia copre ciascun controllo. Piani di sicurezza CI, mirror e build host sono prerequisiti della release.

## 5. Privilegi, sandbox e privacy

Valutare confinement per applicazioni desktop; Flatpak è candidato, con accesso tramite permessi espliciti e XDG portals. Sviluppare regole polkit ristrette; applicazioni non devono distribuire policy autorizzative globali senza review. Telemetria, diagnostica remota, OCR/cloud e controllo vocale devono dichiarare dati raccolti, destinazione, durata e opt-in.

## 6. Verifica e criteri di accettazione

Testare verifica pacchetto alterato, update interrotto, permessi non autorizzati, leak log, account standard, recovery e accessibilità dei prompt. Release bloccata da vulnerabilità critica non mitigata, chiavi compromesse/non custodite, artefatti senza provenienza, o recovery che distrugge dati senza conferma comprensibile. Threat model, livelli CVSS o tempi di risposta sono TBD e richiedono owner.

## 7. Decisioni aperte

Secure Boot support matrix e signing service; cifratura default; firewall; policy update/rollback; sandbox predefinito; hardening kernel; dati diagnostici; security response team e disclosure policy. Specifiche legali/regolatorie dipendono dal mercato di distribuzione.

## Riferimenti ufficiali

- [Linux kernel module signing](https://docs.kernel.org/admin-guide/module-signing.html)
- [Linux kernel security documentation](https://docs.kernel.org/admin-guide/LSM/index.html)
- [polkit reference manual](https://polkit.pages.freedesktop.org/polkit/polkit.8.html)
- [Flatpak sandbox and portals](https://docs.flatpak.org/en/latest/basic-concepts.html)
- [systemd security concepts](https://systemd.io/)

## Cronologia

- 0.1.0 — 2026-09-23: bozza iniziale.
