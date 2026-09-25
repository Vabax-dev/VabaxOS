# Il menu di avvio

Quando si accende il computer dalla chiavetta o dal DVD di VabaxOS, compare il menu di avvio. Il menu non parla: la voce parte dopo, con il sistema. Per questo il menu si usa con segnali acustici e lettere.

Il menu è in inglese, come nelle altre distribuzioni. Con la lettera **L** si sceglie un'altra lingua: il menu si ricarica in quella lingua, e tutto il sistema parte in quella lingua (voce, benvenuto, desktop, tastiera). Le lettere sono le stesse in ogni lingua.

## Come si usa senza vedere lo schermo

1. Accendi il computer dalla chiavetta di VabaxOS.
2. Aspetta **due bip ravvicinati**: il menu è pronto.
3. Non premere niente: dopo 10 secondi parte **VabaxOS con voce**, e il [benvenuto parlato](benvenuto.md) ti chiede la lingua.

Oppure, dopo i due bip, premi una lettera:

- **V**: VabaxOS con voce («with voice»).
- **N**: VabaxOS senza voce («without voice»), per chi non ha bisogno della sintesi vocale.
- **I**: installa VabaxOS con la voce («install with voice»). Poi la lingua: **I** italiano, **E** inglese, **A** altre lingue. Parte l'installer di Debian con la sintesi vocale, già nella lingua scelta: vedi [l'installazione](installazione.md). Se la lingua è già stata scelta con L, I parte subito.
- **O**: altre modalità di installazione («other install options»): grafica ad alto contrasto con lo zoom (K), grafica (G), testuale (T).
- **R**: modalità di recupero con voce («recovery mode»). Parte solo la console testuale, senza desktop grafico e senza benvenuto. Serve quando il desktop non funziona.
- **L**: lingua («language»). Apre l'elenco delle lingue:
  - **E**: English;
  - **I**: italiano.
  Dopo la scelta il menu si ricarica nella nuova lingua e i **due bip suonano di nuovo**: è la conferma. Poi si prosegue come sopra, per esempio aspettando 10 secondi.
- **T**: strumenti («tools»).

Negli strumenti:

- **C**: verifica che la chiavetta o il DVD non siano danneggiati.
- **G**: avvia con la grafica sicura, per le schede video che danno uno schermo nero.
- **D**: lascia VabaxOS e avvia il dispositivo successivo, di solito il disco del computer.
- **F**: apre le impostazioni del firmware UEFI. Attenzione: il firmware non parla.
- **R**: riavvia.
- **S**: spegne.
- **Esc**: torna al menu principale.

Si possono usare anche le frecce su e giù, poi Invio. Appena premi un tasto, l'attesa di 10 secondi si ferma.

## Come appare

Per chi vede poco: in alto c'è il logo di VabaxOS su fondo blu scuro. Le voci sono bianche; quella scelta è gialla. In basso c'è la barra dei secondi che mancano all'avvio automatico.

## Stato

- Per ora le lingue sono inglese e italiano (DOC-01 §28).
- Su alcuni computer i bip non si sentono, perché manca l'altoparlante interno che li produce. In quel caso basta aspettare: dopo l'attesa parte comunque VabaxOS con voce. Va verificato sui PC fisici di prova.
