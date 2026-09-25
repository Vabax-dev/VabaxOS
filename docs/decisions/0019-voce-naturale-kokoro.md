# ADR-0019: Voce naturale Kokoro per il desktop, eSpeak NG come riserva

- **Stato:** Accettata (Vabax, 2026-09-24); chi sceglie la voce è cambiato con ADR-0022
- **Data:** 2026-09-24
- **Responsabile:** Vabax (Project Lead, responsabile accessibilità), Principal Software Engineer
- **Modifica:** ADR-0006 (sintesi vocale): Piper opzionale dalla v0.3 non è più il piano

## Contesto

Vabax non ama eSpeak NG: «fa schifo», anche se tono, volume e velocità vanno bene e non perde mai una parola. Il 2026-09-24 ha ascoltato, sulla postazione, la stessa frase e le frasi tipiche di Orca con quattro voci:

- **eSpeak NG:** robotico, ma chiaro e completo anche veloce.
- **Piper «riccardo»** (dati M-AILABS, licenza libera): più umano di eSpeak, ma perde la lettera finale delle parole e suona «distante». Il difetto resta anche con il punto finale e il volume fisso. Scartato come voce predefinita.
- **Piper «paola»:** buona, ma addestrata partendo da una voce con licenza solo per la ricerca. Esclusa per la licenza.
- **Kokoro** (voci italiane Sara e Nicola): «un altro mondo». Ad alta velocità (parametro `speed` del modello) si mangia le parole; parlando a velocità naturale e accelerato con Sonic (la libreria di eSpeak NG per le alte velocità) «ha retto bene».

Il limite di Kokoro è il tempo di calcolo. Misure sulla postazione (Intel Core 7 150U, 8 thread, onnxruntime di Debian), per una frase nuova mai detta:

- «Sì»: circa 0,2-0,3 s;
- «Impostazioni»: 0,5 s;
- «Impostazioni, pulsante»: 0,75 s;
- Piper, per confronto: 0,06 s.

I lettori di schermo puntano a meno di 0,2 s (hexgrad/kokoro#291). Kokoro aggiunge da 0,2 a 0,27 s di silenzio all'inizio di ogni frase, come le voci che NVDA ha corretto nel 2024.

## Decisione

1. **Kokoro è la voce del desktop** (Orca e ogni programma che parla con Speech Dispatcher) **quando il computer ce la fa.** Altrimenti resta eSpeak NG. Piper non si usa per ora.
2. **La console resta sempre eSpeak NG** (Speakup, ADR-0005), anche con Kokoro nel desktop: deve funzionare quando tutto il resto non parte.
3. **A ogni avvio `vabaxos-voice-select` misura il computer**, prima del desktop:
   - servono almeno 7 GB di memoria e il modello installato;
   - Kokoro sintetizza tre frasi brevi di Orca con ogni voce;
   - se la voce più veloce di ogni lingua resta sotto il limite (`max_delay_ms`, oggi 800 ms, **provvisorio**: si fissa con l'ascolto di Vabax con Orca), Kokoro diventa il modulo predefinito;
   - per ogni lingua si usa **la voce più veloce** (decisione di Vabax); sulla postazione, per l'italiano, Nicola.
   Si può imporre la scelta con l'opzione di avvio `vabaxos.voice.engine=kokoro|espeak`, o in `/etc/vabaxos/voice.conf`.
4. **La velocità viene sempre da Sonic**: Kokoro parla sempre a velocità naturale.
5. **Per ridurre il ritardo**, il modulo `sd_kokoro`:
   - tiene il modello sempre in memoria;
   - taglia il silenzio prima e dopo ogni frase;
   - spezza i messaggi alle fine di frase e alle virgole, e fa suonare la prima parte mentre calcola la seconda;
   - tiene una cache delle frasi già dette, in memoria e sul disco, e prepara in anticipo le frasi più comuni di Orca e GNOME;
   - suona con un buffer di 30 ms e si ferma in pochi millisecondi a ogni STOP, interrompendo anche il calcolo in corso.
6. **Le lingue che Kokoro non ha**, e i simboli che non sa leggere, li legge eSpeak NG dentro lo stesso modulo.
7. **Solo pacchetti Debian** a parte il modello: onnxruntime, numpy, espeak-ng (per i fonemi), libsonic, libpulse. Il modello (325 MB) e le voci (28 MB) si scaricano durante la costruzione e si verificano con SHA-256.

## Licenza

- Modello e voci: Apache-2.0 (hexgrad/Kokoro-82M); esportazione ONNX del progetto kokoro-onnx (MIT). Compatibili con ADR-0011.
- Da sapere: secondo la scheda del modello, Kokoro è stato addestrato anche con **audio prodotto da servizi vocali commerciali**, oltre che con audio di pubblico dominio e con licenze libere. Vabax ne è stato informato e ha accettato (2026-09-24).

## Alternative considerate

- **Solo eSpeak NG:** veloce e sicuro, ma è proprio la voce che Vabax non vuole.
- **Piper:** veloce, ma la voce italiana con licenza pulita (riccardo) perde le lettere finali.
- **Kokoro sempre, anche sui computer lenti:** un lettore di schermo che risponde dopo un secondo non si può usare.
- **Modelli ridotti di Kokoro (int8, fp16):** Vabax non vuole perdere qualità, e l'int8 è anche più lento (hexgrad/kokoro#291).

## Conseguenze

- Il pacchetto `vabaxos-voice` pesa circa 330 MB e la ISO cresce di conseguenza.
- Su un computer lento o con poca memoria resta eSpeak NG, come prima.
- La prima volta che una frase viene detta c'è un ritardo; le volte successive parte subito.
- Kokoro servirà anche al lettore di documenti con voce naturale (blocco 6).

## Riesame

- Vabax, ascoltando Orca con Kokoro, trova il ritardo scomodo: si abbassa il limite o si torna a eSpeak NG come predefinito.
- Esce una voce italiana veloce e con licenza pulita (Piper o altro).
- Kokoro 2 o un modello simile con uscita a flusso (streaming).
