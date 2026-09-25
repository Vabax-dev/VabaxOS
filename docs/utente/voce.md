# La voce del desktop

VabaxOS ha due voci per il desktop, cioè per Orca e per ogni programma che parla ([ADR-0019](../decisions/0019-voce-naturale-kokoro.md)):

- **la voce naturale, Kokoro:** sembra una persona che parla. Per l'italiano ci sono Nicola, voce maschile, e Sara, voce femminile;
- **eSpeak NG:** robotica, ma leggerissima e immediata.

La console di testo, quella che parla prima del desktop e nella modalità di recupero, usa sempre eSpeak NG: deve funzionare anche quando tutto il resto non parte.

## Chi sceglie

A ogni avvio, prima del desktop, VabaxOS misura per qualche secondo il computer:

- se il computer è abbastanza veloce e ha almeno 7 GB di memoria, il desktop parla con Kokoro;
- per ogni lingua si usa la voce che su quel computer risponde prima;
- altrimenti resta eSpeak NG.

Si può scegliere a mano nella [configurazione iniziale](configurazione.md), al passo Voce:

- **Tipo di voce:** Automatico, Voce naturale (Kokoro) oppure eSpeak NG;
- **Voce naturale:** Automatico, Nicola, Sara, o una voce inglese.

La scelta vale dal prossimo avvio del lettore di schermo: Super+Alt+S due volte.

## Cosa aspettarsi

- La **prima volta** che Kokoro dice una frase serve un attimo, da un quinto di secondo a circa mezzo secondo su un portatile recente. Le volte successive la frase parte subito: VabaxOS se la ricorda.
- Le parole più comuni di Orca, come «pulsante», «casella di controllo», «selezionata» e i nomi dei menu, VabaxOS le prepara in anticipo, nei primi minuti dopo l'avvio.
- Quando si preme un tasto, la voce si ferma subito.
- La velocità alta non mangia le parole: Kokoro parla sempre alla sua velocità naturale e VabaxOS accelera il suono, come fa eSpeak NG.
- Le lingue che Kokoro non conosce, e i simboli, li legge eSpeak NG.

## Per chi amministra il computer

- `/etc/vabaxos/voice.conf`: `engine=auto`, `kokoro` oppure `espeak`; il ritardo massimo accettato (`max_delay_ms`) e la memoria minima (`min_memory_mb`).
- Opzione di avvio `vabaxos.voice.engine=kokoro` oppure `=espeak`, per imporre la scelta.
- `/var/lib/vabaxos/voice.conf`: la scelta fatta all'avvio e le misure.
- `sudo vabaxos-voice-select`: ripete la misura.
