# Qualcosa non va

Quando qualcosa non funziona, apri **Qualcosa non va** dal menu Start (lo trovi anche scrivendo «problema» nella ricerca).

## I primi controlli

Appena si apre, VabaxOS controlla da solo le cause più comuni e ti dice cosa ha trovato:

- servizi del sistema o della tua sessione che non sono partiti;
- nessuna uscita audio, audio muto o volume molto basso;
- Orca spento (**Super+Alt+S** lo avvia);
- nessuna rete, o rete senza Internet;
- poco spazio libero;
- programmi installati solo in parte.

Se non trova niente lo dice. Spesso basta questo per capire cosa fare.

## Il rapporto

Se il problema resta, prepara un rapporto da mandare a chi ti aiuta:

1. in **Cosa non va** scegli l'argomento (la voce, l'audio, la tastiera, la rete, un programma…);
2. in **Cosa è successo** scrivi con parole tue cosa facevi e cosa è successo;
3. premi **Crea il rapporto**.

VabaxOS salva un file di testo nella cartella Documenti, con i primi controlli, i dati del computer e i registri dell'avvio. Poi puoi:

- **Apri il rapporto:** lo leggi nell'editor di testo;
- **Apri la cartella:** per allegarlo a un messaggio;
- **Copia il rapporto:** per incollarlo con **Ctrl+V** in un messaggio o in una segnalazione.

## I tuoi dati

**Nascondi i miei dati personali** è acceso: nel rapporto il tuo nome, il nome del computer, i nomi delle reti Wi-Fi, gli indirizzi di rete e gli indirizzi e-mail sono sostituiti da parole come `[personal]` e `[address]`. Prima di mandarlo puoi comunque leggerlo tutto.

**Aggiungi tutto il registro del sistema** rende il rapporto più utile, ma chiede la password, perché il registro del sistema contiene anche i messaggi degli altri utenti e dei servizi. Se non dai la password, il rapporto si fa lo stesso, senza quella parte.

VabaxOS **non invia niente da solo** e non permette a nessuno di controllare il computer da lontano: sei tu a decidere a chi mandare il rapporto. Per segnalare un difetto di VabaxOS puoi allegarlo a una segnalazione su GitHub, nella pagina del progetto Vabax-dev/VabaxOS.

## Dal terminale

Il comando `vabaxos-report` scrive lo stesso rapporto, senza i primi controlli e senza nascondere i dati personali. Con `sudo vabaxos-report` aggiunge tutto il registro del sistema.
