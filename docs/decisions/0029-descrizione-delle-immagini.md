# ADR-0029: Descrizione delle immagini senza Internet

- **Stato:** Accettata (Vabax, 2026-11-02: «un modello leggero, recente, multilingue», scaricato dall'interfaccia per non appesantire la ISO; la scelta del modello e del modo di scaricarlo affidata a Claude)
- **Data:** 2026-11-02
- **Responsabile:** Vabax (Project Lead, responsabile accessibilità), Principal Software Engineer

## Contesto

Vabax ha scelto (2026-11-01) la descrizione delle immagini senza Internet: «cosa c'è in questa foto», anche per una finestra senza testo leggibile.

Ricerca del 2026-11-02:

- NVDA ha provato la descrizione sul computer con ViT-GPT2 (poco utile, secondo i suoi utenti) e propone ora Qwen 3.5 0,8B in ONNX, molto migliore, con tempi fino a un minuto.
- Firefox usa distilvit di Mozilla (Apache-2.0): veloce e piccolo, ma descrive solo in inglese.
- In Debian forky c'è **llama.cpp** (con la libreria multimodale `libmtmd` e `llama-server`), che legge le immagini con modelli GGUF.

## Decisione

1. Motore: **llama.cpp di Debian** (`llama-server`, avviato solo quando serve e chiuso dopo).
2. Modello: **Qwen3.5 0,8B** (Apache-2.0, 2026), lo stesso che propone NVDA per le descrizioni sul computer: multilingue, quindi descrive in italiano, e leggero. Si usa la versione pubblicata dal progetto llama.cpp stesso (`ggml-org/Qwen3.5-0.8B-GGUF`): il modello in Q8_0 e il proiettore delle immagini (mmproj), circa 1 GB in tutto.
3. **Il modello non è nella ISO.** Si scarica una volta, quando l'utente lo chiede, nella sua cartella (`~/.local/share/vabaxos/describe`):
   - la prima volta che si preme Super+Alt+P, VabaxOS spiega che serve il modello, quanto pesa, e chiede se scaricarlo; l'avanzamento si sente ogni 25%; finito lo scaricamento descrive subito l'immagine;
   - dal menu Start, «Descrizione delle immagini»: scarica o elimina il modello.
   Niente avviso sul desktop all'avvio (lo sentirebbe anche chi non usa la funzione); niente voce nel menu di Orca (Orca non accetta componenti aggiuntivi).
4. Ogni file scaricato si controlla con l'impronta SHA-256 data dal repository; quando VabaxOS avrà provato i file veri, le impronte si fissano in `vabaxos_describe/model.py` (`PINNED`).
5. Tasti: **Super+Alt+P** descrive la finestra in uso, **Super+Alt+Maiusc+P** lo schermo intero; per un file, «Apri con», «Descrivi l'immagine». Il risultato si apre in una finestra di testo, come l'OCR, con la descrizione e il testo riconosciuto.

## Alternative considerate

- **Servizi in Internet:** descrizioni migliori, ma le immagini lascerebbero il computer.
- **distilvit con onnxruntime:** il più rapido, ma solo in inglese e con descrizioni brevi.
- **Qwen2-VL 2B o SmolVLM 500M** (la prima proposta): il primo più pesante e del 2024, il secondo solo in inglese.
- **Il modello nella ISO:** pronto subito, ma 1 GB in più per tutti.

## Conseguenze

- La ISO non cresce; serve Internet la prima volta, poi mai più.
- Da verificare nella fase delle prove: che llama.cpp di forky legga Qwen3.5 (supporto arrivato nel 2026), i nomi dei file del repository, il tempo vero sul mini PC e sul portatile di Vabax.

## Riesame

- Quando llama.cpp di Debian legge modelli più recenti e piccoli (per esempio Qwen 3.5 0,8B).
