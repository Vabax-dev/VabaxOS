# Internet con Orca

VabaxOS usa **Firefox ESR** per il web e **Thunderbird** per la posta: sono i programmi che funzionano meglio con Orca su Linux. ESR vuol dire che le novità arrivano una volta all'anno: i tasti e i menu non cambiano da un giorno all'altro. Firefox si apre dal menu Start, oppure con Super e poi scrivendo «Firefox».

Per esercitarsi c'è una [pagina di prova](../../packages/vabaxos-help/root/usr/share/doc/vabaxos-help/html/prova-web.html), nell'aiuto di VabaxOS: ha titoli, collegamenti, un elenco, un modulo e una tabella.

## Le due modalità

Nelle pagine web Orca lavora come NVDA:

- **modalità navigazione**: le frecce leggono la pagina riga per riga, e le lettere sono tasti rapidi (qui sotto). È la modalità normale quando si apre una pagina;
- **modalità focus**: i tasti vanno alla pagina, per scrivere in un campo o usare un menu. Orca ci passa da solo quando si entra in un campo con Tab o con Invio.

**Ins+Spazio** passa a mano da una modalità all'altra; **Esc** in un campo torna alla modalità navigazione.

## I tasti rapidi

In modalità navigazione, una lettera va all'elemento successivo; con Maiusc a quello precedente. Sono gli stessi tasti di NVDA:

- **H**: titolo; **da 1 a 6**: titolo di quel livello;
- **K**: collegamento; **U**: collegamento non visitato; **V**: visitato;
- **F**: campo di un modulo; **E**: campo di testo; **B**: pulsante; **C**: casella combinata; **X**: casella di controllo; **R**: pulsante di opzione;
- **T**: tabella; nella tabella, **Ctrl+Alt+frecce** si muovono fra le celle;
- **L**: elenco; **I**: voce di elenco;
- **D**: punto di riferimento (intestazione, navigazione, contenuto principale, piè di pagina);
- **M**: riquadro; **G**: immagine; **P**: paragrafo; **Q**: citazione;
- **J**: zona che si aggiorna da sola, per esempio un messaggio dopo aver inviato un modulo.

Come NVDA, Orca non ripete la lettera del tasto rapido premuto: dice solo il titolo, il collegamento o il campo raggiunto. Quando scrivi in un campo dice ogni carattere scritto. Si cambia con **Ins+2**, o nelle Impostazioni del lettore di schermo, pagina «Scrittura».

Gli elenchi, come in JAWS: **Ins+F7** collegamenti, **Ins+F6** titoli, **Ins+F5** campi dei moduli. **Ins+Freccia giù** legge tutto dal punto in cui sei; **Ins+T** dice il titolo della pagina.

L'elenco completo dei tasti è nella guida [I tasti di Orca](tasti-orca.md).

## Tasti di Firefox

- **Ctrl+L** o **F6**: la barra degli indirizzi; scrivi l'indirizzo o le parole da cercare e premi Invio;
- **Ctrl+T**: nuova scheda; **Ctrl+W**: chiudi la scheda; **Ctrl+Tab**: scheda successiva;
- **Alt+Freccia sinistra**: pagina precedente; **F5**: ricarica;
- **Ctrl+F**: cerca nella pagina;
- **Ctrl+D**: aggiungi ai segnalibri; **Ctrl+Maiusc+O**: i segnalibri.

In VabaxOS Firefox si apre senza pagine di benvenuto, senza la barra sui dati inviati a Mozilla e senza messaggi pubblicitari, che Orca leggerebbe a ogni avvio (e che il tasto Tab raggiungerebbe prima della pagina). L'accessibilità di Firefox è sempre accesa. Quando una pagina si apre, Orca dice quanti titoli, collegamenti, moduli e tabelle contiene.

## La posta con Thunderbird

- **Ctrl+N**: nuovo messaggio; **Ctrl+R**: rispondi; **Ctrl+L**: inoltra;
- **Ctrl+Invio**: invia il messaggio che stai scrivendo;
- **F6**: passa fra l'elenco delle cartelle, l'elenco dei messaggi e il messaggio aperto;
- nell'elenco dei messaggi le frecce scorrono i messaggi e Orca legge mittente, oggetto e data; **Invio** apre il messaggio.

## Problemi noti

- Con GNOME 50, su alcuni computer (segnalato da altri utenti, non riprodotto nelle prove di VabaxOS) Orca in Firefox dice solo il tipo e il nome degli elementi, e non legge il testo della pagina ([discussione su GNOME](https://discourse.gnome.org/t/orca-on-gnome-50-wayland-only-reads-element-labels-not-text-content-plus-automatic-language-switching-not-working/38619)). Se succede: premi **Ins+Spazio** una o due volte per cambiare modalità; se non basta, riavvia Orca con **Super+Alt+S** due volte, poi torna in Firefox. VabaxOS avvia Orca prima di ogni programma, come si consiglia per questo problema.
- I programmi fatti con Electron (per esempio alcuni programmi di chat) possono restare muti: si avviano con l'opzione `--force-renderer-accessibility`.
