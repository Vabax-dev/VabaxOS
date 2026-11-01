# Descrivere le immagini

VabaxOS descrive a parole un'immagine, una foto o una finestra senza testo leggibile, **senza Internet**: l'immagine non esce mai dal computer ([ADR-0029](../decisions/0029-descrizione-delle-immagini.md)).

## I tasti

- **Super+Alt+P:** descrive la finestra in uso.
- **Super+Alt+Maiusc+P:** descrive tutto lo schermo.
- Per un file: in File, sull'immagine, **Apri con**, «Descrivi l'immagine».

VabaxOS dice «Descrivo l'immagine», poi si apre una finestra con la descrizione e, se c'è, il testo scritto nell'immagine. Le frecce la leggono riga per riga, Esc chiude. Ci vuole da qualche secondo a un minuto, secondo il computer.

## La prima volta: il modello

Per descrivere serve un modello di circa 1 GB (Qwen3.5 0,8B), che non è nella chiavetta per non appesantirla. La prima volta che premi Super+Alt+P, VabaxOS lo spiega e chiede se scaricarlo:

- **Scarica:** VabaxOS dice l'avanzamento ogni 25 per cento; alla fine descrive subito l'immagine;
- **Non ora:** non scarica niente.

Serve Internet solo per questo scaricamento, una volta sola. Il modello si può scaricare o eliminare anche dal menu Start, **Descrizione delle immagini**.
