# Installare VabaxOS

VabaxOS si installa con l'installer di Debian, lo stesso che molte persone cieche usano da anni ([ADR-0007](../decisions/0007-installer.md)). VabaxOS lo rende raggiungibile e lo avvia già con le opzioni di accessibilità.

## Con la voce

1. Accendi il computer dalla chiavetta di VabaxOS e aspetta i **due bip** del menu di avvio.
2. Premi **I**, poi la lettera della lingua: **I** per italiano, **E** per inglese. Parte l'installer con la sintesi vocale, già nella lingua scelta, con il paese e la tastiera di quella lingua: niente domande su lingua, paese e tastiera. Quindi **I, I** installa in italiano.
3. Per un'altra lingua premi **I**, poi **A** («altre lingue»): l'installer chiede la lingua dall'elenco completo di Debian, poi il paese e la tastiera.
4. La voce legge ogni domanda. Si risponde con le frecce e Invio; Tab passa ai pulsanti.
5. Alla fine il sistema installato ha già la voce della console e Orca, come la versione live.

Se prima hai scelto la lingua con **L** nel menu di avvio, **I** fa partire subito l'installer in quella lingua.

Dal benvenuto parlato, la voce «Installa VabaxOS» spiega gli stessi passi e offre di riavviare.

## Per chi vede poco

Nel menu di avvio premi **O**, poi **K**: parte l'installer grafico con il **tema ad alto contrasto**. Con **Ctrl+Più** e **Ctrl+Meno** si ingrandisce e si rimpicciolisce il testo.

## Altre modalità

Sempre nel sottomenu **O**: **G** per l'installer grafico normale, **T** per quello testuale senza voce.

## Attenzione

- L'installazione può cancellare i dati del disco scelto. L'installer chiede sempre conferma prima di scrivere.
- In questa fase di sviluppo (serie 0.x) VabaxOS è basato su Debian testing ([ADR-0017](../decisions/0017-base-debian-testing-forky.md)): va bene per provare, non per l'uso quotidiano con dati importanti.
- Il firmware non libero per Wi-Fi e audio è incluso.
