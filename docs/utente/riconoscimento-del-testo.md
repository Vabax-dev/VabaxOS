# Leggere il testo dello schermo (OCR)

A volte Orca non trova niente da leggere: un programma senza accessibilità, un'immagine, un video, un desktop remoto, il menu di un gioco. In quei casi VabaxOS **riconosce il testo** che si vede sullo schermo, come fa NVDA con NVDA+R.

## I tasti

- **Super+Alt+R**: il testo della **finestra in uso**.
- **Super+Alt+Maiusc+R**: il testo di **tutto lo schermo**.

VabaxOS dice «Riconosco il testo», poi in qualche secondo si apre una finestra con il testo trovato. Il titolo dice quante righe ci sono e da quale finestra vengono, per esempio «Testo riconosciuto, 6 righe: Impostazioni di rete».

## Nella finestra del testo

- Il focus è sulla prima riga: **Freccia giù** e **Freccia su** leggono riga per riga, **Ctrl+Frecce** parola per parola, come in un documento.
- **Ins+Freccia giù** legge tutto.
- **Ctrl+C** copia il testo selezionato, **Ctrl+Maiusc+C** copia tutto.
- **Esc** chiude e torna alla finestra di prima.

Le righe sono nell'ordine dello schermo, dall'alto in basso; una riga vuota separa le zone diverse della finestra.

## Le immagini

Un'immagine salvata (PNG, JPEG, TIFF) si legge allo stesso modo: in File, sull'immagine, **Apri con**, «Riconosci il testo». Per un documento intero, anche scansionato, è meglio il [lettore di documenti](lettore.md).

## Cosa aspettarsi

- Riconosce l'italiano e l'inglese.
- Il testo stampato sullo schermo viene bene, anche piccolo e su sfondo scuro; il testo scritto a mano, i caratteri decorativi e le scritte sopra le fotografie possono uscire sbagliati.
- Le icone senza scritta non diventano testo.
- Tutto resta sul computer: la fotografia dello schermo non va su Internet e si cancella appena il testo è pronto.
