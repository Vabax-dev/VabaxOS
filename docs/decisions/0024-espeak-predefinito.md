# ADR-0024: eSpeak NG voce predefinita, Kokoro a scelta dell'utente

- **Stato:** Accettata (Vabax, 2026-09-25)
- **Data:** 2026-09-25
- **Responsabile:** Vabax (Project Lead, responsabile accessibilità), Principal Software Engineer
- **Modifica:** ADR-0019 (voce naturale Kokoro per il desktop): cambia solo chi sceglie la voce

## Contesto

ADR-0019 fa scegliere la voce al computer: a ogni avvio VabaxOS misura quanto ci mette Kokoro e, se il computer è abbastanza veloce, il desktop parla con Kokoro.

Il 2026-09-25 Vabax ha ascoltato VabaxOS nella macchina virtuale e ha deciso: «metti eSpeak come sintesi di default. Kokoro lascialo come alternativa, ma sarà l'utente a metterselo».

Motivi:

- un lettore di schermo deve rispondere subito, su ogni computer; eSpeak NG lo fa sempre, Kokoro solo sui computer veloci e con un attimo di attesa sulle frasi nuove;
- la misura all'avvio dà risultati diversi da un avvio all'altro (nella macchina virtuale Nicola ha misurato 855 ms, poco sopra il limite di 800): la voce può cambiare senza che l'utente lo chieda;
- chi usa un lettore di schermo vuole decidere lui la propria voce.

## Decisione

1. Il desktop parla con **eSpeak NG** per default, su ogni computer (`engine=espeak` in `/etc/vabaxos/voice.conf`).
2. **Kokoro resta installato**, con tutto quello che ADR-0019 descrive (Sonic, cache, taglio del silenzio, interruzione immediata).
3. L'utente sceglie Kokoro nella configurazione iniziale, al passo Voce, «Tipo di voce: Voce naturale (Kokoro)». Quando Orca usa Kokoro, il modulo carica il modello in anticipo a ogni avvio della sessione, così la prima frase non aspetta.
4. La misura automatica resta disponibile per chi amministra il computer: `engine=auto` in `/etc/vabaxos/voice.conf`, o l'opzione di avvio `vabaxos.voice.engine=auto`.
5. Il lettore di documenti (`vabaxos-reader`) continua a usare Kokoro: lì la voce naturale conta più della prontezza.

## Alternative considerate

- **Tenere la scelta automatica (ADR-0019):** scartata da Vabax per i motivi sopra.
- **Togliere Kokoro dal sistema:** si risparmierebbe circa 1 GB, ma si perde la voce naturale che Vabax vuole come alternativa e per il lettore di documenti.

## Conseguenze

- Il primo avvio non misura più il computer: qualche secondo in meno prima del desktop.
- La guida «La voce» spiega come passare a Kokoro.
- La soglia di ritardo di Kokoro (800 ms) conta solo con `engine=auto`.

## Riesame

- Se Kokoro diventa abbastanza rapido per un lettore di schermo su un computer comune (per esempio con un motore più veloce), si può riproporre la scelta automatica.
