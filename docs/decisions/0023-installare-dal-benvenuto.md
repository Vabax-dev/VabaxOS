# ADR-0023: Installare dal benvenuto, con le scelte di accessibilità

- **Stato:** Accettata (Vabax, 2026-09-25)
- **Data:** 2026-09-25
- **Responsabile:** Vabax (Project Lead, responsabile accessibilità), Principal Software Engineer
- **Sostituisce / Sostituita da:** — (completa ADR-0007; cambia la sua conseguenza «si installa dal menu di avvio»)

## Contesto

Vabax ha chiesto di analizzare tutto l'installer (2026-09-25), e ha notato che Ubuntu 26.04 ha le impostazioni di accessibilità già nell'installer. L'analisi completa è in [docs/sviluppo/analisi-installer.md](../sviluppo/analisi-installer.md). I punti che contano qui:

- L'installer di Ubuntu comincia con: lingua, poi **accessibilità** (vista, udito, digitazione, puntamento, zoom), poi «Prova o installa». Le scelte valgono subito.
- Il benvenuto parlato di VabaxOS (ADR-0016) ha già lo stesso ordine: lingua, poi Prova, Installa, Accessibilità. Ma oggi «Installa VabaxOS» dice solo di riavviare e premere I nel menu di avvio. Chi installa deve ritrovare il menu di avvio, premere di nuovo L e I per l'italiano, e perde tutto quello che ha scelto: velocità della voce, testo grande, contrasto, zoom, tasti permanenti. Al primo avvio del sistema installato il benvenuto chiede di nuovo la lingua, in inglese.
- Il menu di avvio della chiavetta è in sola lettura: il sistema live non può scegliere la voce del menu al riavvio successivo.
- Il kernel Linux può caricare un altro kernel e passargli il controllo senza passare dal firmware (kexec). L'installer di Debian è sulla chiavetta (`/install/gtk/vmlinuz`, `/install/gtk/initrd.gz`), firmato come il kernel del sistema live.
- Il modulo della voce dell'installer accetta la velocità dalla riga di avvio (`speakup_soft.rate`).

## Decisione

1. **«Installa VabaxOS» nel benvenuto fa ripartire subito il computer nell'installer con la voce**, con il programma `vabaxos-install` (pacchetto `vabaxos-welcome`). Carica l'installer della chiavetta con la chiamata di sistema `kexec_file_load` e lo avvia con `systemctl kexec`: niente firmware, niente menu di avvio.
2. L'installer riceve le scelte fatte nel benvenuto: **lingua e tastiera** (nessuna domanda di lingua, paese e tastiera), **velocità della voce** (`speakup_soft.rate`), e le **impostazioni di accessibilità** (`vabaxos.a11y`, `vabaxos.rate`). Se nel benvenuto la voce è spenta parte l'installer grafico, ad alto contrasto se il contrasto è stato scelto.
3. **Le scelte arrivano nel sistema installato.** Le risposte automatiche dell'installer (`image/config/includes.installer/preseed.cfg`) salvano in `/var/lib/vabaxos/installer-choices` la lingua dell'installazione, `vabaxos.a11y`, `vabaxos.rate`, e l'alto contrasto della voce K del menu di avvio. Al primo avvio il benvenuto parte da quelle scelte: nella lingua giusta, alla velocità giusta, con testo grande, contrasto, zoom e tasti permanenti già attivi.
4. **Se il kernel rifiuta di caricare l'installer**, il benvenuto spiega il menu di avvio come oggi e offre di riavviare.
5. Il menu di avvio resta com'è: I, K, G, T continuano a funzionare.

## Alternative considerate

- **Solo il menu di avvio (come oggi):** nessun rischio nuovo, ma chi installa perde le scelte e deve usare il menu di avvio due volte.
- **Un installer grafico VabaxOS nella sessione live, come Ubuntu:** è la domanda di ADR-0007 per la v0.5, con prove con persone cieche. Troppo presto, e l'installer di Debian con la voce funziona già.
- **Calamares:** in Qt, accessibilità con Orca da dimostrare (ADR-0007).
- **Scegliere la voce del menu di avvio per il riavvio successivo:** la chiavetta è in sola lettura, e la variabile UEFI BootNext sceglie il dispositivo, non la voce del menu.

## Motivazione

È la parte dell'esperienza di Ubuntu che conta per una persona cieca: scegliere lingua e accessibilità una volta sola, all'inizio, e ritrovarle dopo l'installazione. Si ottiene senza scrivere un installer nuovo e senza toccare il partizionamento: l'installer resta quello di Debian (ADR-0007), cambia solo come ci si arriva e cosa si porta con sé.

## Conseguenze

- `scripts/test-boot.sh --entry welcome-install` prova il percorso: dal benvenuto a «Installa ora», fino all'installer che parla; la CI lo esegue con e senza Secure Boot.
- `scripts/test-install.sh` controlla che le scelte passate all'installer arrivino nel sistema installato; la CI lo esegue.
- Con Secure Boot il kernel accetta solo un installer firmato: va verificato su ogni nuova versione del kernel di Debian (la prova della CI lo fa).
- La guida [Installare VabaxOS](../utente/installazione.md) spiega il nuovo percorso.

## Riesame

- La prova con Secure Boot fallisce su un PC reale;
- alla v0.5, con la scelta dell'installer (ADR-0007);
- Vabax, ascoltando, trova il percorso scomodo.
