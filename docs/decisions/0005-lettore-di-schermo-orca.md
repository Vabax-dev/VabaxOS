# ADR-0005: Lettore di schermo — Orca upstream, più Speakup in console

- **Stato:** Accettata
- **Data:** 2026-09-24
- **Responsabile:** Vabax (Project Lead, responsabile accessibilità)

## Contesto

La roadmap chiede se forkare o personalizzare Orca oppure scrivere un nuovo «Vabax Screen Reader» (DOC-01 §26, punto 5), e indica già Orca per la v0.1. NVDA è il riferimento per l'esperienza, ma è legato alle API di Windows e non si può portare su Linux (DOC-01 §1.7).

## Decisione

- **Desktop:** VabaxOS usa **Orca così com'è upstream**, senza fork. Il «Vabax Screen Reader» per ora è Orca con un **profilo Vabax**: impostazioni predefinite, voce, verbosità, scorciatoie e script per i programmi Vabax. Le modifiche al codice di Orca si propongono a Orca.
- **Console e recupero:** **Speakup** (il lettore di schermo del kernel) con **espeakup**, così la voce c'è anche nelle console testuali, nella modalità di recupero e se il desktop non parte.
- **Braille:** **BRLTTY**, già integrato con Orca e con la console.

## Alternative considerate

- **Fork di Orca:** un fork si allontana dall'originale a ogni versione di GNOME. Senza un team non si regge, e toglierebbe a Orca proprio i miglioramenti che servono a tutti.
- **Nuovo lettore di schermo da zero:** NVDA ha richiesto più di quindici anni e un'organizzazione dedicata. Iniziare da qui significherebbe non avere una v0.1.

## Motivazione

L'utente ha bisogno di un lettore di schermo che funzioni oggi. Orca è maturo, supporta sintesi vocale e Braille, usa AT-SPI e su GNOME 48 funziona su Wayland. Il valore di VabaxOS sta nel **far funzionare tutta la catena** (avvio, voce, configurazione, desktop, recupero), non nel riscrivere un pezzo che esiste già.

## Conseguenze

- Il pacchetto `vabaxos-accessibility` conterrà il profilo Orca predefinito, la configurazione di Speakup/espeakup e BRLTTY.
- Le differenze fra l'esperienza NVDA e Orca vanno raccolte come issue con l'etichetta `orca-upstream`, e quelle risolvibili si propongono a Orca.
- Il nome «Vabax Screen Reader» non si usa pubblicamente finché è Orca: si dice «Orca, configurato per VabaxOS».

## Riesame

Alla v0.8 (Accessibility Beta), sulla base delle barriere raccolte: se ci sono limiti di Orca che upstream non accetta e che bloccano utenti, si valuta un componente Vabax aggiuntivo (con un ADR e un prototipo, vedi DOC-14 e DOC-15).
