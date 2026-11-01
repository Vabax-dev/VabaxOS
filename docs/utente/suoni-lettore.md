# I suoni del lettore di schermo

**Suoni del lettore di schermo**, nel menu Start, fa suonare a Orca un suono breve invece di dire il tipo di comando: «Salva» e un suono, invece di «Salva pulsante». Le letture diventano più brevi, come con i suoni di NVDA.

## Imparare i suoni

Sotto **Impara i suoni** c'è un elenco: Pulsante, Collegamento, Casella di controllo, Pulsante di scelta, Casella combinata, Campo di testo, Menu, Scheda, Pulsante a due stati, Cursore, Pulsante di selezione numerica. **Invio** su una riga suona il suono e dice il suo nome. Conviene ascoltarli tutti prima di accenderli.

## Accenderli e spegnerli

**Suoni al posto dei tipi di comando** li accende o li spegne. Orca riparte da solo, in pochi secondi.

- Lo stato dei comandi resta detto a voce: «selezionata», «non selezionata», «premuto».
- Se Orca dice il tipo di comando con parole diverse da quelle che VabaxOS conosce, lo dice a voce come sempre: non si perde mai un'informazione.
- Il volume dei suoni è quello dei suoni di Orca, nelle impostazioni del lettore di schermo.

Dal terminale: `vabaxos-orca-sounds on`, `off`, `status`.

## Serve Orca 51

I suoni passano da un'estensione di Orca, e le estensioni ci sono da Orca 51 in poi. Se questo VabaxOS ha un Orca più vecchio, l'interruttore è spento e lo dice; i suoni si possono già ascoltare e imparare. Il passaggio a Orca 51 è proposto in [ADR-0031](../decisions/0031-orca-51.md).
