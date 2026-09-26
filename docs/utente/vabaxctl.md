# vabaxctl: VabaxOS dal terminale

`vabaxctl` dice com'è messo VabaxOS e cambia le cose principali, con risposte brevi che Orca legge bene. I comandi hanno un nome italiano e uno inglese.

## I comandi

- `vabaxctl stato` (o solo `vabaxctl`): la versione di VabaxOS e dei suoi pacchetti, se il lettore di schermo è acceso, quale voce usa, se l'archivio VabaxOS è attivo e quanti aggiornamenti sono pronti.
- `vabaxctl voce`: dice la voce del lettore di schermo. `vabaxctl voce kokoro` passa alla voce naturale, `vabaxctl voce espeak` torna a eSpeak NG ([ADR-0024](../decisions/0024-espeak-predefinito.md)).
- `vabaxctl lettore`: dice se il lettore di schermo è acceso. `vabaxctl lettore spento` lo spegne, `vabaxctl lettore acceso` lo riaccende. Anche Super+Alt+S lo accende e lo spegne.
- `vabaxctl aggiorna`: cerca gli aggiornamenti e dice quanti sono. `vabaxctl aggiorna --now` li installa subito, `vabaxctl aggiorna --at-restart` al prossimo avvio. È lo stesso programma degli aggiornamenti del desktop, con l'avanzamento detto a voce.
- `vabaxctl rapporto`: scrive un rapporto del computer (avvio, hardware, voce), da mandare a chi ti aiuta. Non contiene password.
- `vabaxctl archivio`: dice se l'archivio APT di VabaxOS è attivo e l'impronta della chiave del progetto ([ADR-0026](../decisions/0026-archivio-apt-e-chiave.md)).
- `vabaxctl aiuto`: l'elenco dei comandi.

Voce e lettore di schermo si cambiano dal terminale del desktop: da una console di testo (Ctrl+Alt+F3) `vabaxctl` lo dice e non cambia niente.

## Un esempio

```bash
vabaxctl stato
```

Risponde, per esempio:

```text
VabaxOS 0.1 (Debian forky), pacchetti 0.1.0~alpha.1
Lettore di schermo: acceso.
Voce: eSpeak NG.
Archivio VabaxOS: attivo.
Aggiornamenti: 2 pronti. Per installarli: vabaxctl aggiorna --now.
```
