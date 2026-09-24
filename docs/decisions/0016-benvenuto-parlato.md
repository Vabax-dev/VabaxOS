# ADR-0016: Benvenuto parlato all'avvio, prima del desktop

- **Stato:** Proposta
- **Data:** 2026-09-24
- **Responsabile:** Vabax (Project Lead, responsabile accessibilità)
- **Modifica:** ADR-0014, punto 4 (configurazione iniziale)

## Contesto

Idea di Vabax (2026-09-24): la prima volta che VabaxOS si avvia, una voce dice «Benvenuto in VabaxOS, usa le frecce per scegliere la modalità di configurazione o di utilizzo».

Oggi, secondo ADR-0014, la prima cosa che l'utente sente è il segnale del menu GRUB (due bip). Poi la voce arriva solo nel desktop, con la configurazione iniziale Vabax in GTK 4.

C'è un limite tecnico: **GRUB non può parlare.** Nel menu di avvio non c'è sintesi vocale e nemmeno il driver della scheda audio. GRUB sa solo suonare toni con l'altoparlante interno del PC (comando `play`). Una voce vera è possibile solo dopo l'avvio di Linux, cioè qualche secondo dopo il menu (in QEMU la console è pronta dopo circa 20 secondi).

## Decisione proposta

1. **Il menu GRUB resta com'è** (ADR-0014): due bip, lettere V, N, R, T, avvio automatico «con voce» dopo 10 secondi. È l'unica cosa che funziona prima di Linux.
2. **Nuovo: «Benvenuto VabaxOS», un menu parlato in modalità testo.** Parte appena Linux ha l'audio, prima del desktop grafico, sulla prima console. Parla con eSpeak NG, senza bisogno del desktop, quindi funziona anche se la grafica non parte.
   - Dice: «Benvenuto in VabaxOS. Usa le frecce per scegliere la modalità di configurazione o di utilizzo, poi premi Invio.»
   - Con le frecce si scorrono le scelte e ogni scelta viene letta. Invio conferma, Esc ripete il messaggio.
   - Scelte proposte, da confermare con Vabax:
     1. «Usa VabaxOS» (sistema live, desktop con voce);
     2. «Configura lingua, voce, tastiera e rete», che porta alla configurazione iniziale (lavoro 8);
     3. «Installa VabaxOS», quando ci sarà l'installer (lavoro 9);
     4. «Spegni».
3. **Quando parte:**
   - nella ISO live: a ogni avvio, perché senza installazione ogni avvio è il primo;
   - nel sistema installato: solo al primo avvio, poi si può riaprire dalle impostazioni.
4. **Senza voce:** con «VabaxOS senza voce» (`vabaxos.voice=off`) lo stesso menu compare solo come testo sullo schermo.
5. **Lingue:** il messaggio e le scelte sono traducibili con gettext (ADR-0010). La lingua del benvenuto si può cambiare con un tasto indicato nel messaggio stesso; il dettaglio va provato con utenti.
6. **Test automatici:** un parametro del kernel (per esempio `vabaxos.welcome=off`) salta il benvenuto, così `scripts/test-boot.sh` e la CI possono arrivare alla console.

## Alternative considerate

- **Voce registrata nel menu GRUB:** GRUB non riproduce file audio, solo toni.
- **Benvenuto solo nel desktop (ADR-0014 com'è):** arriva più tardi e non c'è se la grafica non parte, proprio quando serve di più.
- **Una normale finestra di testo (`dialog`) letta da Speakup:** si può fare, ma controlliamo meno cosa viene letto e quando. Resta un ripiego se il programma Vabax non funziona.

## Motivazione

Chi non vede deve sentire subito che il sistema è vivo e cosa può fare. Un benvenuto parlato prima del desktop colma il silenzio fra i bip del menu e la sessione grafica. Inoltre offre una strada con voce anche quando il desktop non parte.

## Conseguenze

- Nuovo lavoro della v0.1, fra la voce in console (lavoro 5) e Orca nel desktop (lavoro 6): il programma di benvenuto, in Python senza interfaccia grafica, con un servizio systemd.
- La configurazione iniziale (lavoro 8) diventa la seconda scelta del benvenuto, invece di partire da sola nel desktop.
- Chi vede sente la voce al primo avvio. Il messaggio deve dire subito come proseguire, e con «senza voce» la voce non parte.

## Domande aperte per Vabax

- Le quattro scelte vanno bene? Ne manca qualcuna?
- Se nessuno preme niente, il benvenuto deve ripetere il messaggio e aspettare, oppure dopo un minuto partire da solo con «Usa VabaxOS»?
- Il nome «Benvenuto VabaxOS» va bene?

## Riesame

Dopo i primi test con utenti ciechi e vedenti (DOC-30), oppure se il benvenuto rallenta troppo l'avvio.
