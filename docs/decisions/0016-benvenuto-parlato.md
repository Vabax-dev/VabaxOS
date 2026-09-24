# ADR-0016: Benvenuto parlato all'avvio, prima del desktop

- **Stato:** Accettata
- **Data:** 2026-09-24
- **Responsabile:** Vabax (Project Lead, responsabile accessibilità), Principal Software Engineer
- **Modifica:** ADR-0014, punto 4 (configurazione iniziale)

Vabax ha proposto l'idea e il messaggio di benvenuto, e il 2026-09-24 ha approvato il messaggio. Ha lasciato le scelte di dettaglio al Principal Software Engineer, sul modello delle altre distribuzioni Linux.

## Contesto

Idea di Vabax: la prima volta che VabaxOS si avvia, una voce dice «Benvenuto in VabaxOS, usa le frecce per scegliere la modalità di configurazione o di utilizzo».

Secondo ADR-0014, oggi la prima cosa che l'utente sente è il segnale del menu GRUB (due bip). Poi la voce arriva solo nel desktop, con la configurazione iniziale Vabax in GTK 4.

C'è un limite tecnico: **GRUB non può parlare.** Nel menu di avvio non ci sono sintesi vocale né driver della scheda audio. GRUB sa solo suonare toni con l'altoparlante interno del PC (comando `play`). Una voce vera è possibile solo dopo l'avvio di Linux (in QEMU la console è pronta circa 20 secondi dopo il menu).

Come fanno le altre distribuzioni:

- **Ubuntu** (installer dalla 23.10): lingua, accessibilità, tastiera, rete, poi «Prova Ubuntu» oppure «Installa Ubuntu».
- **Fedora** (live): il sistema live parte e offre «Prova Fedora» oppure «Installa sul disco».
- **Debian** (installer con sintesi vocale): la prima domanda è la lingua.

In tutti e tre i casi prima si sceglie la lingua, poi fra «prova» e «installa». Nessuno sceglie da solo per l'utente: il programma aspetta.

## Decisione

1. **Il menu GRUB resta** (ADR-0014): due bip, lettere, avvio automatico «con voce» dopo 10 secondi. È l'unica cosa che funziona prima di Linux. Il menu è in inglese, come nelle altre distribuzioni; la voce «Language» (L) ricarica il menu nella lingua scelta, i due bip suonano di nuovo come conferma, e la lingua passa al sistema (`vabaxos.lang`, più `locales` e `keyboard-layouts` di live-config). Da quel momento si usa solo la lingua scelta.
2. **Dopo il menu parte il «Benvenuto in VabaxOS»,** un programma in modalità testo sulla prima console. Parte appena Linux ha l'audio, prima del desktop grafico. Parla con eSpeak NG e non ha bisogno del desktop, quindi funziona anche se la grafica non parte.
3. **Primo passo, la lingua.** Il messaggio è solo in inglese, come nelle altre distribuzioni: «Welcome to VabaxOS. Use the arrow keys to choose your language, then press Enter.» Ogni lingua dell'elenco viene letta nella sua lingua, con la voce di quella lingua: «English», «Italiano». Così una lingua nuova richiede solo il suo nome, non una frase in più all'inizio. All'inizio le lingue sono inglese e italiano (DOC-01 §28); se ne aggiungono altre con le traduzioni.
4. **Secondo passo, la modalità.** Nella lingua scelta: «Usa le frecce per scegliere la modalità di configurazione o di utilizzo, poi premi Invio.» Le scelte sono:
   1. **Prova VabaxOS**: il sistema live con il desktop e la voce, senza toccare il disco;
   2. **Installa VabaxOS**: compare solo quando la ISO contiene l'installer (lavoro 9);
   3. **Voce e tastiera**: velocità e volume della voce, tastiera. Poi si torna a questo elenco;
   4. **Riavvia**;
   5. **Spegni**.
   La rete si configura dopo, nel desktop o nell'installer, come in Ubuntu e Fedora.
5. **Tasti:** frecce su e giù per scorrere, e ogni scelta viene letta. Invio conferma, Esc torna al passo precedente, F1 ripete il messaggio.
6. **Nessuna scelta automatica.** Se nessuno preme niente, dopo 30 secondi il messaggio viene ripetuto una volta, poi il programma aspetta. Chi non vede non deve mai trovarsi in un punto del sistema che non ha scelto.
7. **Quando parte:**
   - nella ISO live: a ogni avvio, perché senza installazione ogni avvio è il primo;
   - nel sistema installato: solo al primo avvio, poi si riapre dalle impostazioni.
8. **Senza voce e test:**
   - con «VabaxOS senza voce» (`vabaxos.voice=off`) lo stesso menu compare solo come testo sullo schermo;
   - con «Recovery mode» il benvenuto non parte: si va dritti alla console;
   - il parametro del kernel `vabaxos.welcome=off` lo salta, per i test automatici (`scripts/test-boot.sh`) e la CI.

## Aggiornamenti

- 2026-09-24: Vabax ha scelto un menu di avvio tutto in inglese, con la possibilità di cambiare lingua prima dell'avvio, invece delle scritte in due lingue. Punto 1 aggiornato.
- 2026-09-24: dopo il primo test di ascolto, Vabax ha chiesto che il messaggio iniziale del benvenuto sia solo in inglese, altrimenti ogni lingua nuova dovrebbe aggiungere la sua frase. Punto 3 aggiornato.

## Alternative considerate

- **Voce registrata nel menu GRUB:** GRUB non riproduce file audio, solo toni.
- **Benvenuto solo nel desktop (ADR-0014 prima di questa modifica):** arriva più tardi e manca se la grafica non parte, proprio quando serve di più.
- **Una normale finestra di testo (`dialog`) letta da Speakup:** si può fare, ma controlliamo meno cosa viene letto e quando. Resta un ripiego se il programma Vabax non funziona.
- **Scelta automatica dopo un tempo di attesa:** comoda per chi vede, ma chi non vede si ritroverebbe in un punto che non ha scelto. Ubuntu e Fedora aspettano.

## Motivazione

Chi non vede deve sentire subito che il sistema è vivo e cosa può fare. Il benvenuto parlato colma il silenzio fra i bip del menu e la sessione grafica. Offre anche una strada con voce quando il desktop non parte. Lo schema lingua, poi «prova o installa» è quello che gli utenti conoscono già dalle altre distribuzioni.

## Conseguenze

- Nuovo lavoro della v0.1, il 5b in `ROADMAP.md`, fra la voce in console (lavoro 5) e Orca nel desktop (lavoro 6). È un programma Python senza interfaccia grafica (ADR-0010), con testi gettext e un servizio systemd che parte prima del display manager.
- Il benvenuto deve accordarsi con Speakup (lavoro 5), perché la console non venga letta due volte. Il modo preciso si decide nel lavoro 5b.
- La configurazione iniziale del desktop (lavoro 8) riceve la lingua già scelta e non la chiede di nuovo.
- Chi vede sente la voce a ogni avvio della live. Il menu GRUB offre «without voice / senza voce» per chi non la vuole.

## Riesame

Dopo i primi test con utenti ciechi e vedenti (DOC-30), oppure se il benvenuto rallenta troppo l'avvio.
