# ADR-0030: La voce naturale su richiesta, più rapida

- **Stato:** Accettata (Vabax, 2026-11-02: «approvo il programma che fa provare e testa la voce naturale»)
- **Data:** 2026-11-02
- **Responsabile:** Vabax (Project Lead, responsabile accessibilità), Principal Software Engineer
- **Modifica:** ADR-0026 (Kokoro fuori dalla ISO), punto 2

## Contesto

Con ADR-0026 VabaxOS parla solo con eSpeak NG e il pacchetto `vabaxos-voice` (Kokoro) non entra nella ISO, perché Kokoro risponde tardi e pesa circa 1 GB. Il 2026-11-02 Vabax ha chiesto di rendere Kokoro più veloce e ha scelto: eSpeak NG resta la voce predefinita; Kokoro si sceglie a mano, e VabaxOS dice se il computer è abbastanza veloce.

Misure del 2026-11-02 (CPU Xeon a 4 core, 2,1 GHz, più lenta di un portatile recente):

- Kokoro impiega circa un terzo della durata dell'audio che produce: il tempo dipende dalla lunghezza della frase, non da un costo fisso. Una frase di 4,8 secondi aspettava 1,4-1,8 secondi prima di parlare.
- Il modello ridotto int8 (88 MB) non è più veloce su questa CPU; il modello completo resta (Vabax: qualità prima di tutto).
- Le frasi brevi di Orca («Nuova cartella pulsante») partono in circa 0,5-0,6 secondi qui; su un PC recente si stima un terzo.

## Decisione

1. **Prima le prime parole.** Kokoro dice da sole le prime 3 parole di ogni frase (mai finendo su un articolo o una preposizione), poi il resto a pezzi di al massimo 12 parole, preparati mentre suonano i precedenti. Misurato: il tempo prima della voce scende da 1,85 a 0,64 secondi e da 1,32 a 0,49 secondi sulle frasi lunghe. Si regola con `first_words=` in `/etc/vabaxos/voice.conf` (0 spegne il taglio, se all'ascolto il suono ne risente). La cache delle frasi più comuni si prepara a pezzi uguali.
2. **Il modello si scarica su richiesta**, come la descrizione delle immagini (ADR-0029): il programma **Voce naturale** (menu Start) scarica i due file (circa 350 MB, gli stessi della costruzione, da GitHub, controllati con SHA-256) in `~/.local/share/vabaxos/kokoro`, fa sentire un esempio, misura il computer e lo dice a parole:
   - fino a 0,3 secondi: «va bene anche per il lettore di schermo»;
   - fino a 0,6: «un po' in ritardo per il lettore di schermo, va bene per leggere i documenti»;
   - oltre: «troppo lento per il lettore di schermo; Orca resta con eSpeak NG».
   Un interruttore la usa per Orca; il lettore di documenti la offre da solo. Eliminarla riporta Orca a eSpeak NG.
3. `vabaxos-voice` torna nella ISO **senza il modello** (tolti i file `fetch` e `not-in-iso`): nella ISO entrano solo il programma, `python3-onnxruntime` e `python3-numpy` (alcune decine di MB invece di circa 1 GB). La CI scarica il modello per le sue prove, con le stesse impronte SHA-256 del programma.

## Alternative considerate

- **Modello nella ISO (ADR-0024):** circa 350 MB in più per tutti, anche per chi non lo usa.
- **Modello int8 o fp16:** più piccolo, ma non più rapido sulle CPU misurate, e con qualità da verificare all'ascolto.
- **Kokoro scelto in automatico a ogni avvio (`engine=auto`):** resta possibile per gli amministratori, ma Vabax ha scelto la scelta a mano.
- **Un motore Kokoro in C++ o Rust:** non è in Debian; da riconsiderare se ci entra.

## Conseguenze

- Chi vuole la voce naturale la scarica una volta con Internet; poi funziona senza.
- Le frasi lunghe partono molto prima; le brevi dipendono dal computer, e VabaxOS lo dice invece di lasciarlo scoprire all'utente.
- Da ascoltare con Vabax nella fase delle prove: le prime tre parole dette da sole suonano naturali? Se no, `first_words=0` oppure un numero più alto.
