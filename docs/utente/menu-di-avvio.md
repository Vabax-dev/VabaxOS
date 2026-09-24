# Il menu di avvio

Quando si accende il computer dalla chiavetta o dal DVD di VabaxOS, compare il menu di avvio. Il menu non parla: la voce parte dopo, con il sistema. Per questo il menu si usa con segnali acustici e lettere.

Le scritte del menu sono in due lingue, prima in inglese e poi in italiano, come «VabaxOS with voice / con voce». Le lettere valgono per tutte e due le lingue.

## Come si usa senza vedere lo schermo

1. Accendi il computer dalla chiavetta di VabaxOS.
2. Aspetta **due bip ravvicinati**: il menu è pronto.
3. Non premere niente: dopo 10 secondi parte **VabaxOS con voce**.

Oppure, dopo i due bip, premi una lettera per scegliere subito:

- **V**: VabaxOS con voce (in inglese «with voice»).
- **N**: VabaxOS senza voce («without voice»), per chi non ha bisogno della sintesi vocale.
- **R**: modalità di recupero con voce («recovery»). Parte solo la console testuale, senza desktop grafico. Serve quando il desktop non funziona.
- **T**: apre il sottomenu Strumenti («Tools»).

Nel sottomenu Strumenti:

- **C**: verifica che la chiavetta o il DVD non siano danneggiati («check»).
- **G**: avvia con la grafica sicura («safe graphics»), per le schede video che danno uno schermo nero.
- **D**: lascia VabaxOS e avvia il dispositivo successivo, di solito il disco del computer.
- **F**: apre le impostazioni del firmware UEFI. Attenzione: il firmware non parla.
- **R**: riavvia («reboot»).
- **S**: spegne («shut down»).
- **Esc**: torna al menu principale.

Si possono usare anche le frecce su e giù, poi Invio. Appena premi un tasto, l'attesa di 10 secondi si ferma.

## Stato

- La voce «Installa con sintesi vocale» arriverà con l'installer (ROADMAP, lavoro 9).
- «Con voce» e «senza voce» sono già nel menu, ma la voce vera e propria arriva con i lavori 5 (console) e 6 (desktop).
- Dopo il menu, un benvenuto parlato («Benvenuto in VabaxOS») permetterà di scegliere lingua e modalità: vedi [ADR-0016](../decisions/0016-benvenuto-parlato.md).
- Su alcuni computer i bip non si sentono, perché manca l'altoparlante interno che li produce. In quel caso basta aspettare: dopo l'attesa parte comunque VabaxOS con voce. Va verificato sui PC fisici di prova.
