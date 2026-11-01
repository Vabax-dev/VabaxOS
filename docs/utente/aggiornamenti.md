# Gli aggiornamenti

**Aggiorna VabaxOS**, nel menu Start, è il programma che tiene aggiornato tutto il computer: il sistema, le applicazioni Flatpak e il firmware (il programma interno di alcuni componenti, per esempio il disco o la lista di sicurezza dell'avvio).

All'apertura controlla subito cosa c'è e lo dice: per esempio «12 aggiornamenti, 3 di sicurezza».

## Le tre schede

In alto ci sono tre schede: **Aggiornamenti**, **Cronologia** e **Impostazioni**. Si passa dall'una all'altra con **Ctrl+Pagina giù** e **Ctrl+Pagina su**, oppure con **Alt+1**, **Alt+2** e **Alt+3**.

### Aggiornamenti

- **Stato:** una riga che dice cosa c'è da aggiornare e quando è stato l'ultimo controllo.
- **Controlla** (anche **F5**): cerca di nuovo.
- **Aggiorna ora:** scarica e installa subito. L'avanzamento si sente ogni 25 per cento.
- **Aggiorna al riavvio:** scarica ora e installa al prossimo avvio, con la voce della console. È il modo più sicuro, perché la sessione in uso non si rompe a metà.
- **Annulla:** ferma il controllo o lo scaricamento.
- Quattro gruppi: **Sicurezza**, **Sistema**, **Applicazioni** e **Firmware**, ognuno con quanti aggiornamenti ha. **Invio** o **Freccia destra** apre il gruppo e mostra ogni aggiornamento con la sua versione.

Se fra gli aggiornamenti ci sono parti che fanno funzionare il desktop o la voce (GNOME Shell, Orca, l'audio, il kernel), «Aggiorna ora» chiede prima: installarli adesso potrebbe fermare la voce fino al riavvio. La risposta già scelta è **Al prossimo avvio**; si può anche scegliere **Adesso comunque**.

La password di amministratore la chiede la finestra di GNOME, che Orca legge.

### Cronologia

Cosa è stato installato, aggiornato e rimosso, dal più recente: per esempio «2026-10-30 10:01:02: 35 aggiornati, 1 installati». Ogni voce si apre con Invio e dice i nomi dei pacchetti.

### Impostazioni

- **Cerca gli aggiornamenti:** ogni giorno (predefinito), ogni settimana, mai.
- **Avvisa per:** solo gli aggiornamenti di sicurezza (predefinito), oppure tutti.

VabaxOS controlla in silenzio e avvisa con una notifica. **Non installa mai niente da solo**, in questa serie di prova.

## Da terminale

- `vabaxos-update`: controlla e dice cosa c'è, senza installare;
- `vabaxos-update --now`: scarica e installa subito;
- `vabaxos-update --at-restart`: scarica ora e installa al prossimo avvio;
- `vabaxos-update --window`: apre la finestra.

## Da sapere, nella versione di prova

VabaxOS 0.x si basa su Debian testing. Per ora il sistema installato prende gli aggiornamenti direttamente da Debian testing, senza un controllo di VabaxOS: raramente, un aggiornamento può rompere qualcosa. Il programma lo ricorda nella scheda Aggiornamenti. Il piano per controllare gli aggiornamenti prima che arrivino è in [ADR-0020](../decisions/0020-aggiornamenti-e-sicurezza.md), in attesa di approvazione.
