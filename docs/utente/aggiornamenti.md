# Gli aggiornamenti

**Aggiorna VabaxOS**, nel menu Start, cerca gli aggiornamenti e li installa annunciando ogni passo: quanti sono, quanti di sicurezza, l'avanzamento ogni 25% e il risultato. Aggiorna anche le applicazioni Flatpak.

Da terminale:

- `vabaxos-update`: controlla e dice cosa c'è, senza installare;
- `vabaxos-update --now`: scarica e installa subito;
- `vabaxos-update --at-restart`: scarica ora e installa al prossimo avvio, con la voce della console. È il modo più sicuro per gli aggiornamenti grossi, perché la sessione in uso non si rompe a metà.

Una volta al giorno VabaxOS controlla in silenzio, e avvisa con una notifica solo se ci sono aggiornamenti di sicurezza. **Non installa mai niente da solo**, in questa serie di prova.

La password di amministratore la chiede la finestra di GNOME, che Orca legge.

## Da sapere, nella versione di prova

VabaxOS 0.x si basa su Debian testing. Per ora il sistema installato prende gli aggiornamenti direttamente da Debian testing, senza un controllo di VabaxOS: raramente, un aggiornamento può rompere qualcosa. Il piano per controllare gli aggiornamenti prima che arrivino è in [ADR-0020](../decisions/0020-aggiornamenti-e-sicurezza.md), in attesa di approvazione.
