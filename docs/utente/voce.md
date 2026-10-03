# La voce del desktop

VabaxOS ha due voci per il desktop, cioè per Orca e per ogni programma che parla ([ADR-0019](../decisions/0019-voce-naturale-kokoro.md), [ADR-0024](../decisions/0024-espeak-predefinito.md)):

- **la voce naturale, Kokoro:** sembra una persona che parla. Per l'italiano ci sono Nicola, voce maschile, e Sara, voce femminile;
- **eSpeak NG:** robotica, ma leggerissima e immediata.

La console di testo, quella che parla prima del desktop e nella modalità di recupero, usa sempre eSpeak NG: deve funzionare anche quando tutto il resto non parte.

## Chi sceglie

Il desktop parla con **eSpeak NG**, su ogni computer: risponde subito, anche sui computer lenti (scelta di Vabax, [ADR-0024](../decisions/0024-espeak-predefinito.md)).

Kokoro si sceglie a mano nella [configurazione iniziale](configurazione.md), al passo Voce:

- **Tipo di voce:** eSpeak NG, predefinita, oppure Voce naturale (Kokoro);
- **Voce naturale:** Automatico (Nicola in italiano), Nicola, Sara, o una voce inglese.

La scelta vale dal prossimo avvio del lettore di schermo: Super+Alt+S due volte. Da allora, a ogni accesso VabaxOS prepara Kokoro in anticipo, così la prima frase non aspetta. Kokoro va bene sui computer recenti con almeno 8 GB di memoria.

Il [lettore di documenti](lettore.md) usa sempre Kokoro.

## Cosa aspettarsi

- La **prima volta** che Kokoro dice una frase serve un attimo, da un quinto di secondo a circa mezzo secondo su un portatile recente. Le volte successive la frase parte subito: VabaxOS se la ricorda.
- Le parole più comuni di Orca, come «pulsante», «casella di controllo», «selezionata» e i nomi dei menu, VabaxOS le prepara in anticipo, nei primi minuti dopo l'avvio.
- Quando si preme un tasto, la voce si ferma subito.
- La velocità alta non mangia le parole: Kokoro parla sempre alla sua velocità naturale e VabaxOS accelera il suono, come fa eSpeak NG.
- Le lingue che Kokoro non conosce, e i simboli, li legge eSpeak NG.

## Se la voce si ferma

Premi **Ctrl+Super+Invio**: VabaxOS dice «Ripristino la voce» e la rimette a posto in pochi secondi. Il tasto funziona ovunque: nel desktop, nella schermata di accesso, nella console di testo e anche quando il desktop è bloccato, perché VabaxOS legge la tastiera prima del desktop.

Cosa fa, in ordine:

1. fa ripartire l'audio se non risponde, toglie il muto e alza il volume se è sotto il 40 per cento;
2. dice subito «Ripristino la voce» con eSpeak NG;
3. fa ripartire il servizio della voce (speech-dispatcher);
4. salva una copia delle impostazioni di Orca, poi riaccende la voce di Orca, sceglie eSpeak NG e riporta velocità e volume a valori normali se erano troppo alti o troppo bassi: velocità fuori dall'intervallo 15-90 torna a 50, volume sotto 5 torna a 10. Il resto delle impostazioni non cambia;
5. dice «Voce ripristinata» con la voce del desktop: se la senti, la voce funziona di nuovo;
6. riaccende il lettore di schermo e fa ripartire Orca;
7. fa ripartire la voce della console.

Se al posto di «Voce ripristinata» senti «La voce del desktop non risponde», la voce della console funziona ancora: premi Ctrl+Alt+F3, accedi e usa `vabaxctl report` per salvare un rapporto.

Le copie delle impostazioni di Orca sono in `~/.local/share/vabaxos/voice-rescue`, una cartella per ogni volta, le ultime cinque. Per tornare alle impostazioni di prima, copia `user-settings.conf` di una di queste cartelle in `~/.local/share/orca/` e riavvia Orca con Super+Alt+S due volte.

Kokoro si sceglie di nuovo nelle impostazioni del lettore di schermo (Super+Alt+O).

## Per chi amministra il computer

- `/etc/vabaxos/voice.conf`: `engine=espeak` (predefinito), `kokoro` per tutti gli utenti, oppure `auto`, che misura il computer a ogni avvio e usa Kokoro se è abbastanza veloce; con `auto` contano il ritardo massimo accettato (`max_delay_ms`) e la memoria minima (`min_memory_mb`).
- Opzione di avvio `vabaxos.voice.engine=kokoro`, `=espeak` oppure `=auto`, per imporre la scelta.
- `/var/lib/vabaxos/voice.conf`: la scelta fatta all'avvio e le misure.
- Ctrl+Super+Invio: triggerhappy legge i tasti (`/etc/triggerhappy/triggers.d/vabaxos-voice-rescue.conf`) e tocca `/run/vabaxos-voice-rescue/request`; `vabaxos-voice-rescue.path` avvia `/usr/libexec/vabaxos/voice-rescue`. Cosa ha fatto: `journalctl -u vabaxos-voice-rescue`.
- `sudo vabaxos-voice-select --engine auto`: misura il computer.
