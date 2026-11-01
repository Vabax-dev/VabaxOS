# ADR-0029: Descrizione delle immagini senza Internet

- **Stato:** Proposta
- **Data:** 2026-11-02
- **Responsabile:** Vabax (Project Lead, responsabile accessibilità), Principal Software Engineer

## Contesto

Vabax ha scelto (2026-11-01) la descrizione delle immagini senza Internet: «cosa c'è in questa foto», anche per una finestra senza testo leggibile.

Ricerca del 2026-11-02:

- NVDA ha provato la descrizione sul computer con ViT-GPT2 (poco utile, secondo i suoi utenti) e propone ora Qwen 3.5 0,8B in ONNX, molto migliore, con tempi fino a un minuto.
- Firefox usa distilvit di Mozilla (Apache-2.0): veloce e piccolo, ma descrive solo in inglese.
- In Debian forky c'è **llama.cpp** (con la libreria multimodale `libmtmd` e `llama-server`), che legge le immagini con modelli GGUF.

## Decisione proposta

1. Motore: **llama.cpp di Debian** (`llama-server`, avviato solo quando serve e chiuso dopo).
2. Modello, da scegliere fra:
   - **A. Qwen2-VL 2B Instruct** (Apache-2.0), quantizzato Q4: descrive in italiano; circa 1,6 GB sul disco con il proiettore delle immagini; da 30 a 90 secondi per immagine su un portatile comune;
   - **B. SmolVLM 500M** (Apache-2.0): circa 0,6 GB, pochi secondi, ma descrizioni buone solo in inglese (poi si tradurrebbero).
   Proposta: **A**, perché una descrizione in italiano vale l'attesa; mentre aspetta, VabaxOS dice «Descrivo l'immagine».
3. Tasti: **Super+Alt+P** descrive la finestra in uso, **Super+Alt+Maiusc+P** lo schermo intero; per un file, «Apri con», «Descrivi l'immagine». Il risultato si apre in una finestra di testo, come l'OCR, con la descrizione e il testo riconosciuto.
4. Il pacchetto `vabaxos-describe` resta fuori dalla ISO (`not-in-iso`) finché il modello non è scelto e provato.

## Alternative considerate

- **Servizi in Internet:** descrizioni migliori, ma le immagini lascerebbero il computer.
- **distilvit con onnxruntime:** il più rapido, ma solo in inglese e con descrizioni brevi.

## Conseguenze

- La ISO cresce di circa 1,6 GB con A, o di 0,6 GB con B.
- Va misurato il tempo vero sul mini PC e sul portatile di Vabax.

## Riesame

- Quando llama.cpp di Debian legge modelli più recenti e piccoli (per esempio Qwen 3.5 0,8B).
