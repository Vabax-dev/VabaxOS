# VabaxOS — Package & Application System Specification

| Campo | Valore |
|---|---|
| ID | VABAX-DOC-13 |
| Versione | 0.1.0 |
| Stato | Bozza — formati, repository e policy non approvati |
| Data | 2026-09-23 |
| Dipendenze | DOC-03, DOC-04, DOC-06, DOC-09, DOC-10, DOC-12 |

## 1. Scopo

Definisce come installare, aggiornare, verificare e rimuovere software. La roadmap nomina pacchetti nativi + Flatpak come indirizzo preliminare; AppImage, `.deb`, `.rpm`, Steam/Proton/Wine sono obiettivi di compatibilità da valutare, non un obbligo di includere ogni formato nella base.

## 2. Classi software

- **Sistema/base:** kernel, servizi, driver, firmware, librerie integrate e strumenti di recovery; gestiti dal package system scelto per la base.
- **Applicazioni desktop curate:** repository Vabax con metadati, accessibilità nota, provenienza, dipendenze e ciclo update.
- **Sandbox desktop:** Flatpak è candidato per app desktop; accesso a file/dispositivi tramite permessi espliciti e XDG portals.
- **Portable/compatibility:** AppImage e altri formati sono testati caso per caso; compatibilità e isolamento non sono garantiti dal formato da solo.
- **Gaming/compat layer:** Steam, Proton, Wine e runtimes richiedono policy licenza, GPU, driver e supporto separati.

## 3. Requisiti verificabili

| ID | Requisito |
|---|---|
| PKG-001 | Mostrare origine, versione, architettura, licenza e richieste di permesso prima dell'installazione. |
| PKG-002 | Verificare integrità/provenienza secondo il meccanismo approvato e rifiutare artefatti invalidi con messaggio accessibile. |
| PKG-003 | Installazione, aggiornamento, annullamento e rimozione sono navigabili da tastiera/AT e producono log non sensibili. |
| PKG-004 | Le modifiche privilegiate usano il servizio autorizzativo; un'app non riceve root per default. |
| PKG-005 | Ogni package/app record dichiara requisito CPU, runtime, permessi, dipendenze e stato accessibilità testato. |
| PKG-006 | Update interrotto o spazio insufficiente non lascia il sistema in stato non avviabile senza recovery documentata. |
| PKG-007 | L'utente può ispezionare e revocare permessi concessi ove il formato lo supporta. |
| PKG-008 | I repository configurati e le chiavi sono visibili, con canali stable/beta distinti. |

## 4. Modello repository e metadati

Ogni sorgente repository ha proprietario, URL, key/fingerprint, policy update, architetture, componenti supportati e procedura rimozione. Un catalog record include nome e summary localizzati, screenshot/testo alternativo, versione, publisher, licenza, requisiti AT, permessi, changelog, hash, origine e issue note. Evitare dipendenze silenziose da repo terzi.

## 5. Software non accessibile e compatibilità

Il catalogo distingue “accessibilità testata”, “parziale”, “non testata” e “barriere note”; non usa una generica etichetta “compatibile”. Fornire link a workaround/accessibility issue e metodo per segnalare difetti. Un compatibility center, AppImage o installer Windows non implica che l'app diventi accessibile.

## 6. Criteri di accettazione

Installare, aggiornare, annullare, revocare permessi e rimuovere almeno una app in VM; testare accessibilità del dialogo, verifica artefatto alterato, esaurimento spazio e assenza rete. L'utente capisce il package source e il rollback/recovery applicabile. Formati promossi vengono aggiunti a matrice release.

## 7. Decisioni aperte

Package manager base; repo/signing; Flatpak default o opzionale; politica Flathub o repo Vabax; AppImage; `.deb`/`.rpm` conversione o installazione nativa; aggiornamenti atomici; cache e cleanup; Steam/Proton licensing; supporto app commerciali.

## Riferimenti ufficiali

- [Flatpak basics](https://docs.flatpak.org/en/latest/basic-concepts.html)
- [XDG Desktop Portals](https://docs.flatpak.org/en/latest/portal-api-reference.html)
- [Flatpak application security limits](https://docs.flatpak.org/en/latest/introduction.html)
- [Freedesktop desktop entry specification](https://specifications.freedesktop.org/desktop-entry/latest/)
- [SPDX license list](https://spdx.org/licenses/)

## Cronologia

- 0.1.0 — 2026-09-23: prima bozza.
