# Il benvenuto in VabaxOS

Dopo il [menu di avvio](menu-di-avvio.md), prima del desktop, VabaxOS parla: è il «Benvenuto in VabaxOS» ([ADR-0016](../decisions/0016-benvenuto-parlato.md)). Funziona anche se il desktop grafico non parte.

## Primo passo: la lingua

Si sente, in inglese, come nelle altre distribuzioni:

> Welcome to VabaxOS. Use the arrow keys to choose your language, then press Enter.

Con le frecce su e giù si scorrono le lingue. Ognuna viene letta nella sua lingua e con la sua voce: «English», «Italiano». Invio conferma. Da quel momento il benvenuto parla solo nella lingua scelta.

Se la lingua è già stata scelta nel menu di avvio (lettera L), questo passo si salta.

## Secondo passo: la modalità

Nella lingua scelta si sente:

> Benvenuto in VabaxOS. Usa le frecce per scegliere la modalità di configurazione o di utilizzo, poi premi Invio.

Le scelte:

- **Prova VabaxOS**: parte il desktop, con Orca che legge lo schermo. Il disco del computer non viene toccato.
- **Voce e tastiera**: voce più lenta o più veloce, tastiera italiana o inglese. «Indietro» torna all'elenco.
- **Riavvia**.
- **Spegni**.

«Installa VabaxOS» comparirà quando la ISO conterrà l'installer (lavoro 9).

## Tasti

- **Frecce su e giù**: scorrono le scelte, e ogni scelta viene letta.
- **Invio**: conferma.
- **Esc**: torna al passo precedente.
- **F1**: ripete il messaggio.

Il benvenuto non sceglie mai da solo. Se nessuno preme niente, dopo 30 secondi ripete il messaggio una volta, poi aspetta.

## Senza voce

Con «VabaxOS without voice» nel menu di avvio, il benvenuto compare solo come testo sullo schermo, senza parlare.

## Limiti noti

- La velocità scelta vale per il benvenuto e per la voce della console. Per Orca, nel desktop, arriverà con la configurazione iniziale (lavoro 8).
- Le lingue per ora sono inglese e italiano.
- Spegnimento: con Orca attivo, a volte il sistema restava 90 secondi in silenzio prima di spegnersi. La causa non è ancora trovata (probabilmente Orca o la sua voce). Per ora VabaxOS aspetta al massimo 10 secondi i programmi della sessione.
