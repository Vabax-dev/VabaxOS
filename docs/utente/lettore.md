# Il lettore di documenti

Il **Lettore di VabaxOS** legge i documenti ad alta voce con la voce naturale Kokoro. È pensato per lo studio e per i testi lunghi: libri, dispense, articoli.

Si apre dal menu Start (Lettore di VabaxOS), oppure aprendo un documento con il tasto destro, «Apri con».

## Cosa legge

File di testo e Markdown, PDF, Word (.docx), EPUB e pagine HTML.

Un PDF fatto solo di immagini, per esempio una scansione, non ha testo: il lettore lo dice. Il riconoscimento del testo nelle immagini (OCR) arriverà più avanti.

## Tasti

- **Ctrl+O**: apri un documento.
- **Ctrl+Spazio**: leggi dal punto in cui è il cursore, oppure metti in pausa.
- **Alt+Freccia destra / sinistra**: frase successiva o precedente.
- **Alt+Freccia giù / su**: paragrafo successivo o precedente.
- **Ctrl+Più / Ctrl+Meno**: più veloce o più lento. Le parole restano chiare anche veloci.
- **Ctrl+B**: segnalibro qui. **Ctrl+J**: vai al segnalibro successivo.
- **Ctrl+E**: salva tutta la lettura come file audio (WAV) accanto al documento, per ascoltarla dopo, anche fuori dal computer.

Il testo resta in una normale area di testo: con Orca ci si muove parola per parola o riga per riga come in qualsiasi documento, poi Ctrl+Spazio legge da lì con la voce naturale. Mentre legge, il lettore evidenzia la frase in giallo, per chi vede, senza spostare il cursore: così Orca non si sovrappone alla voce.

Il lettore ricorda dove si era arrivati in ogni documento: alla prossima apertura riparte da lì.

## Voce

La voce si sceglie in basso: Nicola o Sara per l'italiano, Heart o Michael per l'inglese. All'inizio è la voce scelta per il computer (vedi [La voce del desktop](voce.md)).
