# ADR-0014: Voce dal primo secondo — accessibilità attiva di default

- **Stato:** Accettata
- **Data:** 2026-09-24
- **Responsabile:** Vabax (Project Lead, responsabile accessibilità)

## Contesto

Il principio di VabaxOS è «Accessibility First» (DOC-01 §3). Nelle distribuzioni Linux la voce di solito si accende con una scorciatoia che chi non vede deve già conoscere. A maggio 2026 una persona cieca che studia ha segnalato sulla lista debian-accessibility che, con la ISO live GNOME di Debian trixie, non c'è nessun segnale all'avvio su come attivare la voce, Orca non parte con la scorciatoia, il tour di GNOME non si chiude, e dopo la sospensione Orca resta muto.

## Decisione

Nella ISO live di VabaxOS **l'accessibilità è accesa di default**:

1. **Menu di avvio:** segnale acustico quando è pronto. Voce predefinita «VabaxOS (con voce)» dopo un tempo di attesa, più «VabaxOS senza voce», «Installa con sintesi vocale» e «Modalità di recupero con voce».
2. **Console:** Speakup ed espeakup attivi, così i messaggi testuali di avvio ed eventuali errori vengono letti.
3. **Desktop:** Orca si avvia da solo, con eSpeak NG, nella sessione live e nella schermata di accesso (GDM).
4. **Configurazione iniziale Vabax** al primo avvio del desktop, al posto del tour di GNOME: lingua, voce, velocità, tastiera e rete, tutto da tastiera, con la possibilità di spegnere la voce per chi non ne ha bisogno.
5. **Sospensione automatica disattivata nella sessione live**, finché non è provato che Orca riprende a parlare dopo il risveglio.
6. **Scorciatoia sempre disponibile** per accendere e spegnere Orca (quella standard di GNOME, Super+Alt+S), più un modo per riavviare la voce se si blocca.

Nel sistema installato vale la scelta fatta nella configurazione iniziale.

## Alternative considerate

- **Voce spenta di default, accensione con scorciatoia:** è il comportamento attuale delle distribuzioni, ed è esattamente il problema segnalato.
- **Chiedere a voce all'avvio se attivare la voce:** aggiunge un passaggio a tempo che può fallire. Meglio parlare subito e lasciare a chi vede la scelta di spegnere.

## Motivazione

Chi vede può spegnere la voce con un tasto. Chi non vede non può accenderla se non sa che esiste. Il costo del default sbagliato è molto diverso nei due casi.

## Conseguenze

- Ogni punto è un criterio di accettazione della v0.1 (vedi [ROADMAP.md](../../ROADMAP.md)) e diventa un test.
- Chi vede sente la voce al primo avvio della live: il menu e la configurazione iniziale devono spiegare subito come spegnerla.

## Riesame

Dopo i primi test con utenti (DOC-30), in particolare con utenti vedenti e ipovedenti.
