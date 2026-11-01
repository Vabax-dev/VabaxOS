# La voce del desktop

**VabaxOS parla con eSpeak NG** ([ADR-0026](../decisions/0026-solo-espeak.md)). La voce naturale Kokoro si scarica a richiesta con il programma **Voce naturale** ([ADR-0030](../decisions/0030-voce-naturale-su-richiesta.md), proposta: finché Vabax non la approva, il programma c'è solo dove il pacchetto `vabaxos-voice` è installato a mano).

VabaxOS ha due voci per il desktop, cioè per Orca e per ogni programma che parla ([ADR-0019](../decisions/0019-voce-naturale-kokoro.md), [ADR-0024](../decisions/0024-espeak-predefinito.md)):

- **la voce naturale, Kokoro:** sembra una persona che parla. Per l'italiano ci sono Nicola, voce maschile, e Sara, voce femminile;
- **eSpeak NG:** robotica, ma leggerissima e immediata.

La console di testo, quella che parla prima del desktop e nella modalità di recupero, usa sempre eSpeak NG: deve funzionare anche quando tutto il resto non parte.

## Chi sceglie

Il desktop parla con **eSpeak NG**, su ogni computer: risponde subito, anche sui computer lenti (scelta di Vabax, [ADR-0024](../decisions/0024-espeak-predefinito.md)).

## Voce naturale

**Voce naturale**, nel menu Start:

- **Scarica**: circa 350 MB, una volta sola, con Internet; VabaxOS dice a che punto è ogni 25 per cento. Poi funziona senza Internet. **Elimina** la toglie.
- **Ascolta un esempio**: una frase detta con la voce naturale.
- **Misura la velocità**: VabaxOS prova alcune frasi tipiche di Orca e dice quanto risponde in fretta questo computer: «va bene anche per il lettore di schermo» (fino a 0,3 secondi), «un po' in ritardo, va bene per leggere i documenti» (fino a 0,6), oppure «troppo lento per il lettore di schermo». La misura parte da sola dopo lo scaricamento.
- **Usala per il lettore di schermo**: Orca parla con la voce naturale. Per tornare a eSpeak NG spegni l'interruttore, oppure apri le impostazioni del lettore di schermo con Super+Alt+O.

Il [lettore di documenti](lettore.md) la offre da solo appena è scaricata. Se la voce naturale viene eliminata mentre Orca la usa, Orca parla con eSpeak NG: mai silenzio.

Dopo lo scaricamento, Kokoro si sceglie anche nella [configurazione iniziale](configurazione.md), al passo Voce:

- **Tipo di voce:** eSpeak NG, predefinita, oppure Voce naturale (Kokoro);
- **Voce naturale:** Automatico (Nicola in italiano), Nicola, Sara, o una voce inglese.

La scelta vale dal prossimo avvio del lettore di schermo: Super+Alt+S due volte. Da allora, a ogni accesso VabaxOS prepara Kokoro in anticipo, così la prima frase non aspetta. Kokoro va bene sui computer recenti con almeno 8 GB di memoria.

Il [lettore di documenti](lettore.md) offre anche le voci di Kokoro.

## Cosa aspettarsi

- La **prima volta** che Kokoro dice una frase serve un attimo, da un quinto di secondo a circa mezzo secondo su un portatile recente. Le volte successive la frase parte subito: VabaxOS se la ricorda.
- Nelle frasi lunghe Kokoro dice subito le prime parole e prepara il resto mentre parla: la voce parte prima.
- Le parole più comuni di Orca, come «pulsante», «casella di controllo», «selezionata» e i nomi dei menu, VabaxOS le prepara in anticipo, nei primi minuti dopo l'avvio.
- Quando si preme un tasto, la voce si ferma subito.
- La velocità alta non mangia le parole: Kokoro parla sempre alla sua velocità naturale e VabaxOS accelera il suono, come fa eSpeak NG.
- Le lingue che Kokoro non conosce, e i simboli, li legge eSpeak NG.

## Per chi amministra il computer

- `/etc/vabaxos/voice.conf`: `first_words=3`, le parole dette da sole all'inizio delle frasi lunghe (0 per non tagliare); `engine=espeak` (predefinito), `kokoro` per tutti gli utenti, oppure `auto`, che misura il computer a ogni avvio e usa Kokoro se è abbastanza veloce; con `auto` contano il ritardo massimo accettato (`max_delay_ms`) e la memoria minima (`min_memory_mb`).
- Opzione di avvio `vabaxos.voice.engine=kokoro`, `=espeak` oppure `=auto`, per imporre la scelta.
- `/var/lib/vabaxos/voice.conf`: la scelta fatta all'avvio e le misure.
- `sudo vabaxos-voice-select --engine auto`: misura il computer.
