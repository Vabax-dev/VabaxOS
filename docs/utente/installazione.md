# Installare VabaxOS

VabaxOS si installa con l'installer di Debian, lo stesso che molte persone cieche usano da anni ([ADR-0007](../decisions/0007-installer.md)). VabaxOS lo rende raggiungibile e lo avvia già con le opzioni di accessibilità.

## Dal benvenuto (il modo più semplice)

1. Accendi il computer dalla chiavetta di VabaxOS e aspetta il benvenuto parlato.
2. Scegli la lingua. Se vuoi, apri **Accessibilità** e scegli velocità della voce, testo grande, alto contrasto, zoom, tasti permanenti.
3. Scegli **Installa VabaxOS**, poi **Installa ora**. Il computer riparte subito nell'installer con la voce, nella tua lingua e alla stessa velocità.
4. L'installer non chiede di nuovo lingua e tastiera.
5. Al primo avvio del sistema installato il benvenuto parla nella lingua dell'installazione, alla velocità che avevi scelto, e le impostazioni di accessibilità sono già attive.

Questo percorso è deciso in [ADR-0023](../decisions/0023-installare-dal-benvenuto.md). Se il computer non riesce a ripartire così, il benvenuto spiega come usare il menu di avvio.

## Con la voce, dal menu di avvio

1. Accendi il computer dalla chiavetta di VabaxOS e aspetta i **due bip** del menu di avvio.
2. Premi **I**, poi la lettera della lingua: **I** per italiano, **E** per inglese. Parte l'installer con la sintesi vocale, già nella lingua scelta, con il paese e la tastiera di quella lingua: niente domande su lingua, paese e tastiera. Quindi **I, I** installa in italiano.
3. Per un'altra lingua premi **I**, poi **A** («altre lingue»): l'installer chiede la lingua dall'elenco completo di Debian, poi il paese e la tastiera.
4. La voce legge ogni domanda. Si risponde con le frecce e Invio; Tab passa ai pulsanti.
5. Alla fine il sistema installato ha già la voce della console e Orca, come la versione live.

Se prima hai scelto la lingua con **L** nel menu di avvio, **I** fa partire subito l'installer in quella lingua.

## Per chi vede poco

Nel menu di avvio premi **O**, poi **K**: parte l'installer grafico con il **tema ad alto contrasto**. Con **Ctrl+Più** e **Ctrl+Meno** si ingrandisce e si rimpicciolisce il testo.

## Altre modalità

Sempre nel sottomenu **O**: **G** per l'installer grafico normale, **T** per quello testuale senza voce.

## Quali domande fa l'installer

VabaxOS risponde da solo alle domande che non servono a chi installa: il nome del computer in rete e il dominio, la password di root (non c'è: la persona che installa è l'amministratore, come nella versione live e in Ubuntu), altri dischi di installazione da cercare, il paese, il server e il proxy per scaricare i pacchetti (si usa il server principale di Debian). Restano sempre le domande che riguardano te e il disco: lingua, paese e tastiera (se non li hai già scelti), nome e password, fuso orario, quale disco usare e la conferma prima di scrivere.

Con la voce K del menu di avvio (alto contrasto) anche il sistema installato parte con l'alto contrasto.

## Attenzione

- L'installazione può cancellare i dati del disco scelto. L'installer chiede sempre conferma prima di scrivere.
- In questa fase di sviluppo (serie 0.x) VabaxOS è basato su Debian testing ([ADR-0017](../decisions/0017-base-debian-testing-forky.md)): va bene per provare, non per l'uso quotidiano con dati importanti.
- Il firmware non libero per Wi-Fi e audio è incluso.
