# ADR-0025: Il menu Start di VabaxOS, con ricerca e categorie ad albero

- **Stato:** Proposta
- **Data:** 2026-09-25
- **Responsabile:** Vabax (Project Lead, responsabile accessibilità), Principal Software Engineer
- **Sostituisce / Sostituita da:** — (cambia ADR-0018 per il tasto Super; ArcMenu resta sulla barra)

## Contesto

Con ADR-0018 il menu Start di VabaxOS è ArcMenu, un'estensione di GNOME Shell, con la disposizione «Redmond» e il logo di VabaxOS. Funziona con Orca (0 comandi senza nome, blocco 3).

Il 2026-09-25 Vabax ha descritto il menu Start che vuole: «quando si apre, un campo di ricerca con i suggerimenti che arrivano mentre scrivi; se non si scrive niente si preme Tab e si passa a dei macro menu, app, strumenti, cartelle; se premuta la freccia destra su uno di questi espande il contenuto e si può poi scorrere con le frecce tranquillamente il contenuto».

ArcMenu ha una disposizione vicina a questa («Whisker»: categorie a sinistra, programmi a destra; la freccia destra passa ai programmi), ma non un albero: Orca non dice «espanso» e «compresso» né il livello, e gli elementi di GNOME Shell non espongono queste informazioni come fanno le finestre GTK. Cambiare ArcMenu significherebbe mantenere modifiche a un'estensione di altri.

## Decisione proposta

1. **Super apre il menu Start di VabaxOS** (`vabaxos-start`, programma GTK 4, blocco 12), non più ArcMenu. Super+S fa lo stesso. Super di nuovo, o Esc, lo chiude e il focus torna alla finestra di prima.
2. Il menu si apre con il **focus nel campo di ricerca**. I risultati arrivano mentre si scrive: programmi (anche per parole chiave e descrizione, senza badare agli accenti), impostazioni, cartelle, file recenti, comandi (Blocca, Esci, Sospendi, Riavvia, Spegni). Orca dice quanti sono; Freccia giù va ai risultati, Invio apre il primo.
3. Con il campo vuoto, **Tab va alle categorie**: Preferiti, Programmi (divisi come in Windows: Ufficio, Internet, Musica e video, Grafica, Accessibilità, Giochi, Istruzione, Sviluppo, Accessori, Sistema, Altri programmi), Strumenti di VabaxOS, Impostazioni, Cartelle, File recenti, Spegni o esci. Sono un **albero**: Freccia destra espande o entra, Freccia sinistra chiude o torna alla categoria che la contiene, le frecce scorrono, una lettera salta alla voce che comincia con quella lettera, Invio apre. Orca dice il nome, quanti elementi ha una categoria, se è espansa o compressa.
4. Il menu resta aperto in memoria, nascosto (avviato all'accesso): si apre subito.
5. **ArcMenu resta** installato, con il suo pulsante sulla barra delle applicazioni, per chi usa il mouse. Se Vabax preferisce ArcMenu anche per Super, basta rimettere le sue due impostazioni (`arcmenu-hotkey` e `arcmenu-hotkey-overlay-key-enabled` in `10-start-menu`).

## Alternative considerate

- **ArcMenu «Whisker» o «Brisk»:** due riquadri invece di un albero; nessuna informazione di espansione per Orca; comportamento dei tasti deciso da altri.
- **La panoramica di GNOME (Super):** ricerca buona, ma nessuna categoria e una griglia di icone.
- **Scrivere l'albero dentro GNOME Shell (estensione):** stessi limiti di accessibilità di ArcMenu.

## Conseguenze

- Un programma in più, `vabaxos-start`, con i suoi test (`tests/start/test_start.py`) e le prove in `test-boot.sh` (Super apre il menu con il focus nella ricerca, Tab va alle categorie, Freccia destra espande).
- `vabaxos-keys` prende il tasto Super, come fa ArcMenu.
- La guida «Il menu Start» cambia.

## Riesame

- Dopo l'ascolto di Vabax: se l'albero, i nomi o la velocità di apertura non convincono, si torna ad ArcMenu per Super cambiando due impostazioni.
