# ADR-0006: Sintesi vocale — speech-dispatcher + eSpeak NG, Piper opzionale

- **Stato:** Accettata
- **Data:** 2026-09-24
- **Responsabile:** Vabax (Project Lead)

## Contesto

La roadmap vuole una sintesi vocale che funzioni senza Internet dal primo avvio, con eSpeak NG come ripiego e un motore neurale locale opzionale (DOC-01 §26, punto 6). Segnala anche che il repository storico di Piper è archiviato.

## Decisione

- **Strato vocale:** **speech-dispatcher**, lo strato standard che Orca e le altre applicazioni Linux usano per parlare.
- **Voce predefinita:** **eSpeak NG**, inclusa nella ISO e attiva di default, italiano e inglese. È piccola, veloce, reattiva e parla più di cento lingue.
- **Voce neurale opzionale (dalla v0.3):** **Piper**, il cui sviluppo continua in [OHF-Voice/piper1-gpl](https://github.com/OHF-Voice/piper1-gpl) (GPL-3.0, Open Home Foundation) dopo l'archiviazione del repository rhasspy/piper nell'ottobre 2025. Ogni voce ha una propria licenza: una voce entra nella ISO solo dopo la verifica della sua licenza (DOC-09). Le altre voci si installano a richiesta.
- **Nessuna sintesi online** nel percorso essenziale: la voce del sistema non dipende mai dalla rete.

## Alternative considerate

- **Solo Piper, di default:** voce più naturale ma più lenta a rispondere e più pesante. Molti utenti esperti di lettori di schermo preferiscono comunque eSpeak ad alta velocità. Resta un'opzione, non il default.
- **Sintesi vocali commerciali:** licenze incompatibili con una ISO distribuita liberamente.
- **RHVoice e altri motori:** da valutare come voci aggiuntive, senza bloccare la v0.1.

## Motivazione

Per chi non vede, la voce è il sistema. Deve partire sempre, subito e su qualunque hardware: eSpeak NG lo garantisce e occupa pochi megabyte. La qualità si migliora dopo, senza mettere a rischio l'avvio.

## Conseguenze

- La latenza della voce (tempo fra l'evento e la parola) si misura dalla v0.1 (DOC-01 §17).
- Il Centro Accessibilità Vabax (v0.4) permetterà di scegliere motore, voce, velocità, tono e volume, separati dalla lingua dell'interfaccia.
- Serve un modulo speech-dispatcher per Piper, verificato con Orca, prima di offrirlo.

## Riesame

Quando una voce neurale libera in italiano risponde con una latenza paragonabile a eSpeak NG sull'hardware di riferimento: allora si valuta se renderla predefinita.
