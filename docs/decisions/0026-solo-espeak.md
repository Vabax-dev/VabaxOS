# ADR-0026: Per ora solo eSpeak NG, Kokoro fuori dalla ISO

- **Stato:** Accettata (Vabax, 2026-11-01); il punto 2 è cambiato da [ADR-0030](0030-voce-naturale-su-richiesta.md): `vabaxos-voice` è nella ISO senza il modello
- **Data:** 2026-11-01
- **Responsabile:** Vabax (Project Lead, responsabile accessibilità), Principal Software Engineer
- **Modifica:** ADR-0024 (Kokoro a scelta dell'utente) e ADR-0019 (voce naturale Kokoro): sospese finché Kokoro non è più rapido

## Contesto

Con ADR-0024 il desktop parla con eSpeak NG e Kokoro resta installato, da scegliere a mano. Kokoro però:

- risponde in 0,3-0,8 secondi su una frase nuova; un lettore di schermo dovrebbe stare sotto 0,2 (nella macchina virtuale Nicola ha misurato 855 ms);
- occupa circa 1 GB nella ISO (modello, onnxruntime, numpy) e circa 570 MB di memoria quando parla.

Il 2026-11-01 Vabax ha deciso: «per ora solo espeak, finché Kokoro non sarà più rapido», e ha chiesto ottimizzazioni per tutto il sistema.

## Decisione

1. Il sistema parla **solo con eSpeak NG**: console, benvenuto, Orca e lettore di documenti.
2. Il pacchetto `vabaxos-voice` (Kokoro per speech-dispatcher) **resta nel repository** e si costruisce per i test, ma **non entra nella ISO**: il file `packages/vabaxos-voice/not-in-iso` lo esclude (`VABAXOS_ISO=1` in `scripts/build-packages.sh`, impostato da `scripts/build.sh`).
3. La configurazione iniziale e le impostazioni del lettore di schermo mostrano la scelta «Tipo di voce» solo quando Kokoro è installato.
4. Il lettore di documenti legge con eSpeak NG; se `vabaxos-voice` è installato, offre anche le voci di Kokoro.
5. `test-boot.sh` controlla che il desktop usi eSpeak NG; le prove di Kokoro partono solo con una ISO che lo contiene.

## Alternative considerate

- **Tenere Kokoro installato e spento (ADR-0024):** 1 GB in più nella ISO e nel sistema per una voce che oggi non si usa.
- **Piper:** più rapido di Kokoro, ma le voci italiane suonano peggio (ascolto di Vabax, 2026-09-24) e non è in Debian.

## Conseguenze

- La ISO è più piccola di circa 1 GB; costruzione e installazione più rapide.
- Vabax non ama il timbro di eSpeak NG: la scelta va rivista appena c'è un motore naturale abbastanza rapido.

## Riesame

- Quando Kokoro (o un altro motore naturale con licenza libera) risponde entro circa 0,2 secondi su un computer comune: si rimette `vabaxos-voice` nella ISO togliendo `not-in-iso`, e vale di nuovo ADR-0024.
