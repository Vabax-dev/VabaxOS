# Il ripristino del sistema

Se un aggiornamento rompe qualcosa (la voce non parte, il desktop non si apre, un programma non funziona più), VabaxOS può **tornare a com'era il sistema prima** ([ADR-0027](../decisions/0027-ripristino-del-sistema.md)).

## Le copie del sistema

VabaxOS fa da solo una copia del sistema:

- **prima di ogni installazione di pacchetti**, quindi prima di ogni aggiornamento (al massimo una all'ora);
- **una volta alla settimana.**

Tiene le 3 copie più recenti fatte prima delle installazioni e le 2 settimanali più recenti; le più vecchie si cancellano da sole. Non fa copie nella versione live e quando il disco è quasi pieno.

**I documenti e le cartelle personali non sono nelle copie e non cambiano mai con un ripristino.** Per loro c'è il backup (Déjà Dup).

## Dalla finestra

**Ripristino del sistema**, nel menu Start:

- l'elenco delle copie, la più recente per prima, con la data e il motivo, per esempio «30/10/2026 alle 10:00: Prima di installare 12 pacchetti: gnome-shell, orca, mutter»;
- su ogni copia, **Ripristina** ed **Elimina**;
- **Crea una copia ora** (Ctrl+N).

Ripristina chiede conferma e ricorda di salvare il lavoro. Poi il computer copia indietro il sistema (qualche minuto) e si riavvia. La password di amministratore la chiede la finestra di GNOME, che Orca legge.

## Quando il desktop non parte

**Dalla console di testo:** premi **Ctrl+Alt+F3**, accedi con il tuo nome e la tua password (la voce della console legge tutto), poi scrivi `ripristino` e premi Invio.

**Dalla chiavetta di VabaxOS**, se il computer non si avvia proprio:

1. avvia dalla chiavetta e nel menu di avvio premi **R** (modalità di recupero con voce);
2. la console dice «Modalità di recupero»: scrivi `ripristino` e premi Invio;
3. se il disco è cifrato, scrivi la sua password;
4. VabaxOS legge le copie con il loro numero: scrivi il numero e premi Invio;
5. scrivi `sì` e premi Invio per confermare.

Il computer ripristina il sistema e si riavvia.
