# ADR-0011: Licenze — GPL-3.0-or-later, CC BY-SA 4.0, REUSE, DCO

- **Stato:** Accettata
- **Data:** 2026-09-24
- **Responsabile:** Vabax (Project Lead)

## Contesto

DOC-09 stabilisce il processo per le licenze ma lascia aperte la licenza del codice, quella della documentazione e dei materiali grafici, il formato dell'inventario e la scelta fra CLA e DCO. Questa non è una consulenza legale: sono scelte standard nel mondo del software libero.

## Decisione

| Cosa | Licenza |
|---|---|
| Codice di VabaxOS (script, programmi, servizi) | **GPL-3.0-or-later** |
| Documentazione (`docs/`, file `.md`) | **CC-BY-SA-4.0** |
| File di configurazione brevi e file di servizio del repository | **CC0-1.0** |
| Nome «VabaxOS», «Vabax» e logo | **Marchio riservato**, non coperto dalle licenze sopra |

- Il repository segue la specifica **[REUSE](https://reuse.software/spec/)**: la licenza di ogni file è dichiarata (in `REUSE.toml` o nell'intestazione del file), e i testi completi delle licenze stanno in `LICENSES/`. La CI lo controlla con `reuse lint`.
- I contributi usano il **DCO** (Developer Certificate of Origin): ogni commit porta `Signed-off-by:` (`git commit -s`). Nessun CLA.
- I componenti di terze parti (pacchetti Debian, voci, firmware) mantengono le loro licenze. Ogni ISO avrà un inventario (SBOM in formato SPDX, dalla v0.2).

## Alternative considerate

- **MIT / Apache-2.0:** permetterebbero di chiudere il codice in prodotti proprietari. Per un sistema operativo pensato per un bene comune la reciprocità della GPL è più adatta. Orca (LGPL) e NVDA (GPL-2.0-or-later) sono già nel mondo copyleft.
- **GPL-2.0-only:** incompatibile con molto codice GPL-3 moderno.
- **CLA:** frena i contributori e serve solo se si vuole cambiare licenza in futuro.

## Motivazione

La GPL-3.0-or-later è compatibile con quasi tutto l'ecosistema GNOME e Debian, e protegge il lavoro dei contributori. REUSE rende le licenze leggibili anche dalle macchine e prepara l'SBOM. Il DCO è leggero e trasparente.

## Conseguenze

- Il codice di altri progetti si copia solo se la licenza è compatibile con GPL-3.0-or-later, e l'origine va registrata.
- Chi usa il nome o il logo per una distribuzione derivata deve chiedere il permesso: le regole d'uso del marchio arrivano prima della prima alpha pubblica.

## Riesame

Se il progetto passa a un ente o a un fiscal host (DOC-23, fase C), che potrebbe dover detenere il marchio.
