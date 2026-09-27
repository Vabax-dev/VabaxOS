# ADR-0026: Pacchetti Debian corretti da VabaxOS

- **Stato:** Accettata (Vabax, 2026-09-27)
- **Data:** 2026-09-27
- **Responsabile:** Vabax (Project Lead), Principal Software Engineer
- **Sostituisce / Sostituita da:** — (completa ADR-0027 e ADR-0020)

## Contesto

Le prove del gruppo di blocchi 13-15 hanno trovato due difetti che non sono di VabaxOS, ma di programmi di Debian che VabaxOS usa così come sono:

- **speech-dispatcher 0.12.1** a volte smette di parlare per sempre (circa una prova su due con la voce). Quando Orca chiede l'elenco delle voci mentre un modulo sta parlando, il filo che legge le risposte, finito il suo lavoro, sveglia la variabile sbagliata; il filo che legge l'audio del modulo resta addormentato, il modulo si ferma mentre scrive l'audio e nessuno lo sblocca più. Il difetto è anche nella versione di sviluppo di speech-dispatcher. La correzione è una riga (`docs/sviluppo/segnalazioni.md`, segnalazione 6). Provata in un sistema Debian forky minimo: senza la correzione si blocca al primo o al secondo giro di `tests/upstream/speechd-reply-race.py`; con la correzione, 200 giri e 2000 messaggi senza nessun blocco.
- **GJS 1.88.1** (il motore JavaScript di GNOME Shell) a volte si blocca all'avvio con le impostazioni dconf (circa 2 avvii su 10). Riprodotto in 20 secondi con `tests/upstream/gjs-gsettings-deadlock.js`; la correzione spetta a GJS (segnalazione 7) ed è più delicata.

Per una persona cieca il primo difetto è il più grave: il lettore di schermo tace finché non si riavvia la sessione, e non c'è modo di capire cosa succede.

Oggi VabaxOS prende tutti i pacchetti di Debian dalla data fissa di snapshot.debian.org (ADR-0017) e costruisce solo i propri (`packages/`). Aspettare la correzione da speech-dispatcher e poi da Debian può richiedere mesi.

## Decisione proposta

1. VabaxOS può **ricostruire un pacchetto di Debian con una correzione**, solo quando:
   - il difetto tocca l'accessibilità o blocca il sistema;
   - il difetto è riprodotto da una prova nel repository (`tests/upstream/`) e la correzione la fa passare;
   - la correzione è piccola, ed è segnalata al progetto originale con il testo in `docs/sviluppo/segnalazioni.md`.
2. Le correzioni stanno in `patches/debian/<pacchetto>/`, nel formato delle patch di Debian (quilt), con l'intestazione che dice il difetto, la prova e la segnalazione; il file `packages` dice quali pacchetti binari sostituiscono quelli di Debian.
3. Durante la costruzione della ISO, il hook `0400-vabaxos-debian-patched` scarica il sorgente di Debian della versione installata, **dalla stessa data** di `image/build.conf`, aggiunge le correzioni, costruisce i pacchetti con la versione `<quella di Debian>+vabaxos1` (per esempio `0.12.0-5+vabaxos1`) e li installa al posto di quelli di Debian; poi toglie quello che serviva solo per costruire. `+vabaxos1` viene dopo gli aggiornamenti di Debian stable della stessa versione (`+deb13u1`): APT tiene i pacchetti corretti finché VabaxOS non ricostruisce anche la versione nuova.
4. I pacchetti ricostruiti entrano nella ISO come i pacchetti VabaxOS e nell'archivio APT di VabaxOS (ADR-0020), così anche il sistema installato li riceve.
5. Una correzione si toglie appena Debian la include (la prova lo dice: passa anche senza).
6. I primi pacchetti (provati su trixie, ADR-0027, dove i due difetti ci sono ancora):
   - **speech-dispatcher** 0.12.0 con la correzione della segnalazione 6, e l'**uscita audio PipeWire** (`AudioOutputMethod "pipewire"`, già in Debian nel pacchetto `speech-dispatcher-audio-plugins`): con l'uscita PulseAudio la prova minima trova un secondo arresto, nell'attesa della fine dell'audio;
   - **GJS** 1.82.3 con la correzione della segnalazione 7: gli oggetti liberati dalla pulizia della memoria si finiscono di liberare dopo aver lasciato il lucchetto. Con `tests/upstream/gjs-gsettings-deadlock.js`, GJS di trixie si blocca dopo 150 giri; con la correzione, 10 minuti e 193.000 giri senza blocchi.

## Conseguenze

- Più lavoro: ogni ricostruzione va seguita, e tolta quando non serve più. Per questo solo pochi casi, con le regole sopra.
- La costruzione della ISO dura qualche minuto in più (speech-dispatcher e GJS si compilano in circa 15 minuti in tutto).
- Le correzioni sono pubbliche e tornano ai progetti originali: aiutano anche chi usa Debian, Ubuntu e le altre distribuzioni.

## Alternative considerate

- **Aspettare speech-dispatcher e Debian:** la 0.1 uscirebbe con un lettore di schermo che a volte tace per sempre.
- **Evitare la causa in Orca** (niente elenco delle voci mentre parla): non dipende da noi; Orca chiede le voci quando cambia la lingua, e togliere il cambio automatico della lingua peggiora la lettura in più lingue, importante per Vabax.
- **Riavviare speech-dispatcher quando tace:** nasconde il difetto; la persona perde comunque le frasi dette nel frattempo.
- **Prendere speech-dispatcher dalla versione di sviluppo:** il difetto c'è anche lì.
