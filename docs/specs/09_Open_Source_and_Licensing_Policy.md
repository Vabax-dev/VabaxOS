# VabaxOS — Open Source & Licensing Policy

| Campo | Valore |
|---|---|
| ID | VABAX-DOC-09 |
| Versione | 0.1.0 |
| Stato | Bozza di processo — licenza di VabaxOS non decisa |
| Data | 2026-09-23 |
| Dipendenze | DOC-01, DOC-03, DOC-06, DOC-08, DOC-12 |

## 1. Scopo

Assicurare che codice, pacchetti, firmware, font, temi, voci TTS, modelli, giochi e materiali redistribuiti abbiano provenienza e diritti documentati. Questa policy non costituisce parere legale e non sceglie la licenza principale di VabaxOS.

## 2. Regole d'ingresso

Prima di includere o distribuire un componente registrare: nome e versione; URL e commit sorgente; copyright/autori; licenza SPDX dichiarata e licenza effettiva; dipendenze e licenze transitive; modifiche locali; obblighi di sorgente/NOTICE/attribution; condizioni di redistribuzione; firmware o asset non liberi; reviewer e data. Non accettare componente senza licenza identificabile o con conflitto irrisolto.

## 3. Repository e artefatti richiesti

- `LICENSE`: da approvare per il progetto e distinta dalle licenze di terze parti.
- `LICENSES/` o equivalente: testi delle licenze richiesti.
- `NOTICE`/copyright notices: quando richiesti da licenze e componenti.
- `THIRD_PARTY_NOTICES.md`: inventario leggibile per release.
- SBOM in formato standard, SPDX è candidato; versione e profilo da scegliere.
- Provenance per sorgenti, patch, build tool, firmware, voci TTS e modelli.

Il manifest va generato da dati verificabili e revisionato: uno scanner automatico è un indizio, non approvazione legale. Aggiornare inventario per ogni release e modifica delle dipendenze.

## 4. Criteri per selezionare componenti

Preferire open source mantenuto, licenza compatibile con distribuzione e modifiche, upstream accessibile, security process, API stabili, integrazione accessibile e costo di manutenzione sostenibile. Valutare separatamente copyleft, linking, firmware, codecs, artwork, marchi, voci e modelli AI. La licenza di un programma non concede automaticamente diritti su marchi, servizi online o contenuti.

## 5. Processo di review

1. Contributor propone componente e inventario.
2. Maintainer tecnico verifica origine, versione, modifiche e dipendenze.
3. Responsabile licenze verifica obblighi/redistribuzione; casi ambigui vanno a consulenza competente.
4. ADR/decisione registra accettazione, condizioni, eccezioni e data di riesame.
5. Release engineering controlla che avvisi, sorgenti e corrispondenze siano inclusi.

Bloccare l'inclusione in ISO pubblica se i diritti di redistribuzione, firmware, TTS o asset non sono chiariti. Prototipi locali devono comunque indicare chiaramente componenti non redistribuibili.

## 6. Materiali AI e contributi

Contributi generati o assistiti da AI devono avere autore umano responsabile, revisione, provenienza delle fonti e controllo che non siano stati inseriti segreti o materiale non autorizzato. La policy di contributo e DCO/CLA, se necessario, resta TBD. I dataset, modelli e voci hanno record licenza separati dal software che li esegue.

## 7. Criteri di accettazione release

Ogni componente nel prodotto ha identificativo di licenza e versione; notice obbligatori presenti; sorgenti corrispondenti reperibili quando richiesto; SBOM/inventario validato; eccezioni chiuse o approvate; canale per segnalare violazioni pubblicato. Nessuna ISO di release prima della review.

## 8. Decisioni aperte

Licenza del codice Vabax; licenza della documentazione e artwork; policy firmware/codecs; formato SBOM; processo CLA/DCO; titolarità e approvazione release richiedono decisione.

## Riferimenti ufficiali

- [SPDX specifications](https://spdx.dev/use/specifications/) e [SPDX License List](https://spdx.org/licenses/)
- [REUSE Specification](https://reuse.software/spec/)
- [GNU GPL FAQ](https://www.gnu.org/licenses/gpl-faq.html)
- [Debian Free Software Guidelines](https://www.debian.org/social_contract#guidelines)

## Cronologia

- 0.1.0 — 2026-09-23: bozza di processo, nessuna licenza scelta.
