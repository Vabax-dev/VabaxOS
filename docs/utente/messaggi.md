# Messaggi e videochiamate

Nel menu Start ci sono **WhatsApp**, **Telegram** e **Videochiamata**. Si aprono ognuno nella sua finestra di Firefox: su Linux sono le versioni che funzionano meglio con il lettore di schermo.

## Con Orca, in generale

- Queste pagine sono programmi: per scrivere un messaggio Orca deve essere in **modalità focus**. **Ins+Spazio** passa dalla modalità navigazione (le frecce leggono la pagina) alla modalità focus (le frecce e i tasti vanno alla pagina) e viceversa.
- Per leggere i messaggi arrivati, torna in modalità navigazione con Ins+Spazio e scorri con le frecce; **H** salta da un titolo all'altro.
- Il permesso di usare microfono e fotocamera, o di mandare notifiche, lo chiede Firefox con una finestrella che Orca legge: Tab fino a **Consenti**, poi Invio.

## WhatsApp

La prima volta, la pagina mostra un codice QR da inquadrare con il telefono (WhatsApp sul telefono, Dispositivi collegati). Se la fotocamera del telefono è difficile da puntare, la pagina offre anche il collegamento con il numero di telefono e un codice di 8 caratteri.

Alcuni tasti di WhatsApp Web (l'elenco completo è nelle impostazioni di WhatsApp, Scorciatoie da tastiera):

- **Ctrl+Alt+E:** archivia la chat;
- **Ctrl+Alt+Maiusc+U:** segna come non letto.

## Telegram

Telegram Web: si accede con il numero di telefono e il codice che arriva sul telefono.

### Telegram per Orca (AccessGram)

**Telegram per Orca**, nel menu Start, installa a richiesta **AccessGram**, un programma per Telegram fatto apposta per i lettori di schermo (licenza MIT). È giovane e in inglese, e non è fatto da VabaxOS: per questo non è già installato.

- **Scarica e installa:** circa 1 MB da GitHub. VabaxOS scarica la versione che ha controllato e verifica il suo contenuto: se è diverso, non installa niente. Poi AccessGram è anche nel menu Start.
- **La prima volta** AccessGram chiede un «API ID» e un «API hash»: Telegram li dà a ogni persona. **Apri my.telegram.org**, entra con il tuo numero di telefono e il codice che Telegram ti manda, scegli «API development tools», compila il modulo (un nome qualsiasi per l'applicazione), poi copia i due valori in AccessGram. Poi AccessGram chiede il numero di telefono e il codice, come Telegram Web.
- I tasti di AccessGram: **Ctrl+N** cerca, **Ctrl+F** filtra le chat, **Invio** manda il messaggio, **Maiusc+Invio** va a capo, **Ctrl+Maiusc+R** registra un messaggio vocale, **Pagina su** carica i messaggi più vecchi, **Esc** torna indietro.
- **Rimuovi** toglie il programma; la tua sessione di Telegram resta nella cartella di AccessGram.

## Videochiamata (Jitsi Meet)

Jitsi Meet è libero e non chiede account: scrivi un nome per la stanza, premi Invio, e manda l'indirizzo della pagina alle persone da chiamare. Nella chiamata:

- **M:** microfono acceso o spento;
- **V:** fotocamera accesa o spenta;
- **C:** la chat;
- **?:** l'elenco di tutti i tasti.

Per le chiamate di lavoro con Zoom, Teams o Google Meet, si aprono i loro link in Firefox allo stesso modo.
