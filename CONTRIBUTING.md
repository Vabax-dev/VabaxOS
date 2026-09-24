# Contribuire a VabaxOS

Grazie per l'interesse. VabaxOS è all'inizio: ogni contributo, anche piccolo, conta.

## Si può contribuire senza scrivere codice

- **Provare** le ISO e raccontare cosa succede.
- **Segnalare una barriera di accessibilità** con il modello «Barriera di accessibilità»: è il tipo di segnalazione più prezioso.
- **Descrivere il proprio hardware** con il modello «Rapporto hardware».
- **Tradurre** e **scrivere documentazione**.

Non serve dichiarare la propria disabilità né usare il proprio nome vero per segnalare qualcosa.

## Prima di scrivere codice

1. Leggi [ARCHITECTURE.md](ARCHITECTURE.md) e gli [ADR](docs/decisions/README.md) dell'area su cui vuoi lavorare.
2. Cerca una issue esistente, oppure aprine una e aspetta una risposta prima di lavorare su qualcosa di grande.
3. Se il tuo lavoro richiede una scelta architetturale non ancora presa, proponi prima un ADR copiando [il modello](docs/decisions/0000-modello.md).

## Flusso di lavoro

Il flusso è descritto in [ADR-0012](docs/decisions/0012-repository-e-flusso-di-lavoro.md). In breve:

1. Crea un ramo da `main`: `tipo/NUMERO-descrizione`, per esempio `feat/12-menu-avvio-parlante`.
2. Fai commit piccoli, in inglese, con [Conventional Commits](https://www.conventionalcommits.org/) e la firma DCO:

   ```bash
   git commit -s -m "feat(boot): beep when the boot menu is ready (VABAX-12)"
   ```

3. Apri una pull request compilando il modello: cosa cambia, perché, come l'hai provato, impatto sull'accessibilità.
4. La CI deve essere verde prima del merge.

## Firma DCO

Con `-s` certifichi il [Developer Certificate of Origin](https://developercertificate.org/): hai il diritto di inviare il contributo sotto la licenza del progetto. Non serve firmare altri accordi.

## Quando un contributo è finito

Una modifica è completa quando (DOC-01 §82, DOC-07 §9):

- è implementata, costruisce e ha i test pertinenti;
- se tocca l'interfaccia, si usa da tastiera e con Orca, e l'hai provata;
- le stringhe per l'utente sono traducibili (gettext);
- la documentazione è aggiornata;
- le licenze delle dipendenze nuove sono verificate e annotate;
- non contiene segreti, token o dati personali.

## Contributi assistiti da AI

Sono benvenuti alle condizioni di [DOC-19](docs/specs/19_AI_Development_Workflow.md): una persona ne è responsabile, li ha rivisti e provati, e ha verificato che non contengano codice di provenienza o licenza sconosciuta.

## Licenze

Contribuendo accetti che il codice sia distribuito sotto GPL-3.0-or-later e la documentazione sotto CC BY-SA 4.0 ([ADR-0011](docs/decisions/0011-licenze.md)).

## Comportamento

Vale il [Codice di condotta](CODE_OF_CONDUCT.md).
