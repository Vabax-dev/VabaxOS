# ADR-0027: Ripristino del sistema

- **Stato:** Proposta
- **Data:** 2026-11-01
- **Responsabile:** Vabax (Project Lead), Principal Software Engineer
- **Sostituisce / Sostituita da:** — (anticipa il ripristino previsto per la v1.5 in ADR-0009 e ADR-0020)

## Contesto

Il 2026-11-01 Vabax ha chiesto il ripristino del sistema «adesso»: tornare a com'era prima di un aggiornamento che rompe qualcosa. Per una persona cieca è essenziale: un aggiornamento che rompe la voce o il desktop la lascia senza modo di capire cosa succede.

ADR-0009 sceglie ext4, senza istantanee del disco, e rimanda Btrfs alla v1.5. Ci sono due strade (ricerca del 2026-11-01).

### A. Timeshift in modalità rsync, su ext4

- Timeshift è in Debian. In modalità rsync copia il sistema in una cartella del disco; dalla seconda copia in poi salva solo i file cambiati, perché quelli uguali diventano collegamenti alla copia precedente.
- **Non cambia il disco né l'installer**: vale anche per chi ha già installato VabaxOS, anche con il disco cifrato.
- La cartella personale resta fuori: il ripristino non tocca i documenti.
- Più lento: una copia dura minuti, il ripristino anche, e serve un riavvio. Lo spazio occupato è quello dei file cambiati.
- Si comanda da terminale (`timeshift --create`, `--restore --snapshot ... --yes`), quindi VabaxOS può dargli una finestra sua, accessibile.

### B. Btrfs con snapper

- Le istantanee sono immediate e non occupano spazio finché i file non cambiano. snapper le crea da solo prima e dopo ogni installazione con apt.
- **Cambia il disco**: l'installer deve creare Btrfs con i sottovolumi giusti. Lo schema di Debian (`@rootfs`, con il sottovolume scritto in `/etc/fstab`) va corretto perché `snapper rollback` funzioni.
- Avviare il computer direttamente da un'istantanea (grub-btrfs) secondo diverse guide non è affidabile su Debian senza modifiche all'initramfs; inoltre il menu di GRUB non parla.
- Vale solo per le installazioni nuove.

## Decisione proposta

**A adesso, B nella v1.5**, come previsto da ADR-0009:

1. **Timeshift (rsync)** nel sistema installato, configurato da VabaxOS: copia del sistema **prima di ogni aggiornamento** fatto con «Aggiorna VabaxOS», e una alla settimana. Ne tiene 5, cioè le 3 più recenti più 2 settimanali.
2. **«Ripristino del sistema»**, una finestra VabaxOS (GTK 4, come le altre), con l'elenco delle copie e la loro causa, per esempio «Prima dell'aggiornamento del 1 novembre, 12 pacchetti». Ci sono tre comandi: Crea ora, Ripristina, Elimina. Per ripristinare chiede conferma, avvisa che il computer si riavvierà, dice il risultato a voce al riavvio.
3. **Ripristino anche quando il desktop non parte**: nella modalità di recupero con voce (R nel menu di avvio), un menu parlato nella console dice le copie e ne ripristina una con i tasti. Nessun avvio da istantanea dal menu di GRUB.
4. Spazio: se il disco ha meno del 10% libero, la copia non si fa e VabaxOS lo dice.

## Alternative considerate

- **B subito:** più veloce nell'uso, ma cambia l'installer, vale solo per le installazioni nuove, e l'avvio dalle istantanee su Debian è fragile.
- **Nessun ripristino (oggi):** un aggiornamento rotto può lasciare una persona cieca senza voce.

## Conseguenze

- Pacchetti in più: `timeshift`, e `vabaxos-restore` (finestra e menu della modalità di recupero).
- Un aggiornamento con «Aggiorna VabaxOS» impiega qualche minuto in più (la copia), la prima volta di più.
- Le prove: creare una copia, rompere apposta un pacchetto in una macchina virtuale, ripristinare, controllare che la voce torni (`test-install.sh`).

## Riesame

- Nella v1.5, o prima se A si rivela troppo lento: passaggio a Btrfs (B), con un nuovo ADR.
