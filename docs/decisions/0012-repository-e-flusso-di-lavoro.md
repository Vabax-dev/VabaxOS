# ADR-0012: Repository e flusso di lavoro — monorepo, trunk-based

- **Stato:** Accettata
- **Data:** 2026-09-24
- **Responsabile:** Vabax (Project Lead)

## Contesto

La roadmap chiede di scegliere fra un repository unico e più repository (DOC-01 §6, fase 0.1.1). DOC-02 propone i rami `main` e `develop` con identificativi VABAX-NNN; DOC-08 propone Conventional Commits e rami `feature/VABAX-123-nome`.

## Decisione

- **Un repository unico:** `Vabax-dev/VabaxOS` su GitHub contiene configurazione della ISO, pacchetti, script, test e documentazione. Si divide solo quando un componente ha una vita propria (per esempio un programma Vabax usato anche fuori da VabaxOS).
- **Flusso trunk-based:** un solo ramo permanente, `main`, sempre costruibile. Il lavoro si fa su rami brevi che rientrano con una pull request. **Niente ramo `develop`**: con un team piccolo duplica il lavoro senza proteggere niente.
- **Nomi dei rami:** `tipo/NUMERO-descrizione`, per esempio `feat/12-menu-avvio-parlante`, `fix/31-orca-dopo-sospensione`, `docs/5-guida-windows`.
- **Identificativi dei task:** **VABAX-n**, dove *n* è il numero della issue su GitHub. Così l'identificativo è unico e cliccabile.
- **Messaggi di commit:** **Conventional Commits** in inglese (`feat:`, `fix:`, `docs:`, `build:`, `test:`, `chore:`), con riferimento alla issue e `Signed-off-by` (ADR-0011).
- **Protezione di `main`:** niente force push e niente cancellazione. Le pull request passano la CI prima del merge.
- **Lingua:** codice, commit e identificativi in inglese. Documentazione di progetto in italiano, README anche in inglese. Issue e discussioni in italiano o in inglese.
- **Organizzazione dei task:** milestone GitHub per versione (v0.1 … v1.0), etichette per area (`area/…`), tipo (`type/…`) e priorità; le barriere di accessibilità hanno un modello di issue dedicato.

## Alternative considerate

- **Più repository fin dall'inizio:** più rumore (versioni incrociate, issue sparse) senza benefici finché il progetto è piccolo.
- **Git flow con `develop`:** pensato per rilasci pianificati con molti sviluppatori in parallelo.

## Motivazione

Per un fondatore che lavora con assistenti AI, la cosa più importante è che `main` funzioni sempre e che ogni modifica sia piccola, revisionata e tracciabile fino alla issue che la motiva.

## Conseguenze

- DOC-02 §11 (rami `main` e `develop`) è superato da questo ADR.
- Le release si fanno con un tag su `main` (ADR-0015).

## Riesame

Quando ci sono almeno tre manutentori attivi, oppure quando un componente merita un repository proprio.
