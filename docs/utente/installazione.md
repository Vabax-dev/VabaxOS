# Installare VabaxOS

VabaxOS si installa con l'installer di Debian, lo stesso che molte persone cieche usano da anni ([ADR-0007](../decisions/0007-installer.md)). VabaxOS lo rende raggiungibile e lo avvia già con le opzioni di accessibilità.

## Con la voce

1. Accendi il computer dalla chiavetta di VabaxOS e aspetta i **due bip** del menu di avvio.
2. Se vuoi l'installer in italiano, premi **L**, poi **I**: il menu si ricarica e i due bip suonano di nuovo.
3. Premi **I**: parte l'installer con la sintesi vocale.
4. La voce legge ogni domanda. Si risponde con le frecce e Invio; Tab passa ai pulsanti.
5. Alla fine il sistema installato ha già la voce della console e Orca, come la versione live.

Dal benvenuto parlato, la voce «Installa VabaxOS» spiega gli stessi passi e offre di riavviare.

## Per chi vede poco

Nel menu di avvio premi **O**, poi **K**: parte l'installer grafico con il **tema ad alto contrasto**. Con **Ctrl+Più** e **Ctrl+Meno** si ingrandisce e si rimpicciolisce il testo.

## Altre modalità

Sempre nel sottomenu **O**: **G** per l'installer grafico normale, **T** per quello testuale senza voce.

## Attenzione

- L'installazione può cancellare i dati del disco scelto. L'installer chiede sempre conferma prima di scrivere.
- In questa fase di sviluppo (serie 0.x) VabaxOS è basato su Debian testing ([ADR-0017](../decisions/0017-base-debian-testing-forky.md)): va bene per provare, non per l'uso quotidiano con dati importanti.
- Il firmware non libero per Wi-Fi e audio è incluso.
