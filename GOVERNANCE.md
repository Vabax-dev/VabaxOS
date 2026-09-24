# Governance

Il modello completo è in [DOC-23](docs/specs/23_Project_Governance_and_Management_Plan.md). Qui c'è quello che vale adesso.

## Fase attuale: progetto guidato dal fondatore

VabaxOS è guidato da **Vabax** (fondatore e Project Lead), che ha la responsabilità finale su visione, roadmap, decisioni architetturali e comunicazione pubblica.

Nessuna approvazione tecnica o di sicurezza è delegata a un assistente AI senza revisione umana e prove (DOC-19).

## Ruoli

| Area | Chi |
|---|---|
| Visione, priorità, roadmap | Fondatore |
| Architettura (ADR) | Fondatore |
| Accessibilità | Fondatore, con i tester e le persone coinvolte nella co-progettazione (DOC-30) |
| Costruzione, codice, revisione | Fondatore, con assistenza AI |
| Sicurezza e rilasci | Fondatore, finché non c'è un responsabile dedicato |

Quando ci saranno contributori continuativi, si formerà un gruppo di 3–5 manutentori (fase B di DOC-23).

## Come si decide

- Le scelte che toccano architettura, sicurezza, licenze, dati o compatibilità passano da un **ADR** ([docs/decisions/](docs/decisions/README.md)).
- Le altre si discutono nelle issue e nelle pull request.
- Le decisioni prese in chat o a voce valgono solo quando sono scritte nel repository.

## Decisioni già prese sui piani di progetto (DOC-23–32)

- **Canali pubblici:** GitHub Issues per il lavoro e le domande, vabax.it per il racconto in italiano. GitHub Discussions si attiverà quando arriveranno contributori.
- **Sicurezza:** segnalazioni riservate via email (vedi [SECURITY.md](SECURITY.md)). La segnalazione privata di GitHub si attiverà prima della prima alpha pubblica.
- **Raccolta fondi:** nessuna prima della v0.1 alpha pubblica. Quando arriverà, i fondi per VabaxOS resteranno separati dal sostegno personale a Vabax, con un rendiconto pubblico (DOC-29).
- **Pagina su vabax.it:** si pubblica quando esiste una prima ISO che parla, non prima (DOC-26).
- **Programmi Vabax per Windows e macOS:** sono progetti separati, con repository e roadmap propri. Non sono sul percorso critico di VabaxOS (DOC-32).
- **Cadenza:** un aggiornamento pubblico di stato al mese, a partire dalla v0.1.
