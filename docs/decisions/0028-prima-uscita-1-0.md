# ADR-0028: La prima versione pubblica è la 1.0

- **Stato:** Accettata (Vabax, 2026-11-01)
- **Data:** 2026-11-01
- **Responsabile:** Vabax (Project Lead), Principal Software Engineer
- **Modifica:** ADR-0015 (versioni e canali) e la roadmap: niente versioni 0.x pubbliche

## Contesto

La roadmap prevede nove versioni pubbliche, dalla 0.1 alla 0.9, prima della 1.0. Lo sviluppo però è andato avanti per funzioni, non per traguardi: oggi il sistema ha già molto di quello che la roadmap metteva nelle 0.x (installer con voce, aggiornamenti, firewall, cifratura, ripristino, dettatura).

Il 2026-11-01 Vabax ha deciso: la versione in sviluppo diventa direttamente la 1.0. Alla domanda su come intenderlo ha scelto «Prima uscita = 1.0».

## Decisione

1. **Nessuna versione 0.x pubblicata.** Si continua a sviluppare; la prima versione pubblicata si chiama **1.0**.
2. La 1.0 esce solo quando supera **tutti** i criteri della v0.1 e della 1.0 della roadmap, fra cui:
   - avvio, voce, installazione e ripristino provati su **PC fisici**, non solo in QEMU;
   - installazione autonoma provata da **persone cieche**;
   - base **Debian 14 stabile** («forky» stabile, ADR-0001), con gli aggiornamenti di sicurezza di Debian;
   - repository APT di VabaxOS firmato e `SHA256SUMS` firmato (ADR-0015, ADR-0020).
3. Fino ad allora le ISO di prova si chiamano come le nightly di ADR-0015, `VabaxOS-nightly-<AAAAMMGG>-<commit>-amd64.iso`, oppure `1.0.0-alpha.N`, `beta.N`, `rc.N` se Vabax vuole farle provare ad altri. Nessuna 0.x.
4. Le versioni della roadmap (0.1 … 0.9) restano come **elenco di traguardi interni**, non come rilasci.

## Alternative considerate

- **1.0 appena finite funzioni e prove, anche su Debian testing:** prima, ma un sistema su testing può rompersi a ogni aggiornamento; per una persona cieca che lo usa ogni giorno è troppo rischioso chiamarlo stabile.
- **Le 0.x come previste:** più passaggi pubblici, ma Vabax non li vuole.

## Conseguenze

- La 1.0 non esce prima che Debian 14 diventi stabile (previsto intorno al 2027). Il lavoro fino ad allora: funzioni, prove, PC fisici, persone cieche che provano.
- `ROADMAP.md` va letta come traguardi interni.
- Il passaggio da forky a Debian 14 stabile, quando arriva, è un cambio di base: ADR nuovo.

## Riesame

- Quando Debian 14 diventa stabile.
- Se Vabax vuole far provare VabaxOS ad altre persone prima: versioni `1.0.0-alpha.N`.
