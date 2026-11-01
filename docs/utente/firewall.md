# Il firewall

Il firewall decide chi può entrare nel computer dalla rete. In VabaxOS funziona come quello di Windows ([ADR-0021](../decisions/0021-firewall-e-cifratura.md)):

- **tutto quello che esce è permesso:** navigare, la posta, gli aggiornamenti, la musica funzionano come sempre;
- **da fuori entra solo quello che serve**, e dipende dal tipo di rete.

## Due tipi di rete

- **Rete privata** (casa, lavoro): il computer trova le stampanti, gli altri dispositivi, le cartelle condivise degli altri computer e il telefono. È la scelta per le reti nuove.
- **Rete pubblica** (bar, albergo, treno, aeroporto): non entra niente e il computer non si mostra agli altri. Sceglila nei luoghi che non conosci.

Per cambiarlo: **Configurazione di VabaxOS**, pagina **Rete**, gruppo **Firewall**, «Tipo di rete» e il nome della rete. VabaxOS dice il risultato, per esempio «Bar Centrale ora è una rete pubblica».

## Programmi consentiti

Nello stesso gruppo ci sono tre interruttori, spenti all'inizio come in Windows. Valgono solo nelle reti private:

- **Condivisione dei file:** gli altri computer aprono le cartelle che condividi, anche quelli con Windows e Mac;
- **Desktop remoto:** una persona di fiducia usa questo computer da un altro, per aiutarti;
- **Terminale remoto (SSH):** comandi da un altro computer, per chi li conosce.

Per cambiarli serve la password di amministratore: la chiede la finestra di GNOME, che Orca legge.

## Sapere com'è

- **Super+Alt+I** dice lo stato del computer, anche «Firewall attivo».
- Nel terminale, `vabaxos-firewall` dice se il firewall è attivo e di che tipo è ogni rete in uso.

## Da terminale

- `vabaxos-firewall private` o `vabaxos-firewall public`: il tipo delle reti in uso;
- `vabaxos-firewall allow samba`, `allow rdp`, `allow ssh`: consente un programma nelle reti private; `block` lo blocca di nuovo.
