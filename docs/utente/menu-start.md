# Il menu Start

**Super** (il tasto con il logo di Windows) apre il **menu Start** di VabaxOS ([ADR-0025](../decisions/0025-menu-start-vabaxos.md), scelta di Vabax). Super di nuovo, oppure **Esc**, lo chiude, e il focus torna alla finestra in cui eri. Anche **Super+S** lo apre.

## Cercare

Il menu si apre con il **focus nel campo di ricerca**: scrivi, e i risultati arrivano mentre scrivi. Orca dice quanti sono.

- Si cercano programmi, impostazioni (Wi-Fi, Bluetooth, Audio, Accessibilità...), cartelle, file recenti e comandi (Blocca, Esci, Sospendi, Riavvia, Spegni).
- Non serve scrivere il nome intero né gli accenti: «posta» trova il programma di posta, «citta» trova «Città».
- **Invio** apre il primo risultato; **Freccia giù** va ai risultati, poi le frecce li scorrono.
- **Esc** cancella la ricerca; di nuovo, chiude il menu.

## Le categorie

Con il campo di ricerca vuoto, **Tab** va alle categorie:

- **Preferiti:** i programmi fissati nella barra delle applicazioni;
- **Programmi**, divisi come in Windows: Ufficio, Internet, Musica e video, Grafica, Accessibilità, Giochi, Istruzione, Sviluppo, Accessori, Sistema, Altri programmi;
- **Strumenti di VabaxOS:** Programmi di VabaxOS, impostazioni del lettore di schermo, aiuto, lettore di documenti e gli altri;
- **Impostazioni:** le pagine delle Impostazioni;
- **Cartelle:** Cartella personale, Scrivania, Documenti, Scaricati, Musica, Immagini, Video, Cestino;
- **File recenti;**
- **Spegni o esci:** Blocca, Esci, Sospendi, Riavvia, Spegni.

Le categorie sono un albero, come le cartelle in Windows:

- **Freccia destra** apre una categoria; premuta ancora, entra nel suo contenuto;
- **Freccia sinistra** chiude la categoria, oppure torna a quella che la contiene;
- **Frecce su e giù** scorrono;
- **una lettera** salta alla voce che comincia con quella lettera;
- **Invio** apre il programma, l'impostazione o la cartella.

Orca dice di ogni categoria quanti elementi ha e se è aperta o chiusa.

## Dalla barra delle applicazioni, anche con il mouse

A sinistra nella barra delle applicazioni, come in Windows 11:

- il pulsante **Start**, con il simbolo di VabaxOS: un clic apre il menu, un altro lo chiude;
- la casella **Cerca**: un clic apre il menu nel campo di ricerca; quello che scrivi nella casella passa alla ricerca del menu, che si apre già con i risultati.

Nel menu, un clic su un risultato lo apre; un clic sul nome di una categoria la apre o la chiude, un clic su un programma, un'impostazione o una cartella la apre.

Con la tastiera basta Super; sulla barra, raggiunta con **Ctrl+Alt+Tab**, Orca legge i due comandi come «Start» e «Cerca programmi, impostazioni e file».

La panoramica di GNOME, con tutte le finestre, è su **Super+Tab**.
