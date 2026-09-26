# ADR-0020: Aggiornamenti e sicurezza

- **Stato:** Accettata (Vabax, 2026-09-26)
- **Data:** 2026-09-25
- **Responsabile:** Vabax (Project Lead), Principal Software Engineer
- **Sostituisce / Sostituita da:** —

## Contesto

Vabax ha chiesto (2026-09-24) come gestire gli aggiornamenti: renderli rapidi, farli fare anche all'utente da solo, e occuparsi della sicurezza.

La situazione oggi:

- La serie 0.x si costruisce su Debian testing «forky» (ADR-0017). La ISO usa un'istantanea a data fissa di snapshot.debian.org, quindi due costruzioni danno lo stesso sistema.
- **Il sistema installato invece punta a `deb.debian.org` forky**, che cambia ogni giorno. Un aggiornamento può portare una versione nuova di GNOME prima che ArcMenu, Orca o i pacchetti VabaxOS siano pronti. Il tracker di Debian segnala già la transizione a GNOME 51.
- **Testing non ha un archivio di sicurezza separato.** Le correzioni arrivano da unstable, di solito in pochi giorni, a volte di più.
- ADR-0008 prevede un repository APT VabaxOS firmato dalla v0.2 e Flatpak per le applicazioni esterne.
- ADR-0009: ext4, niente snapshot del disco prima della v1.5, quindi niente ritorno automatico a prima di un aggiornamento.
- GNOME Software e PackageKit sono già nella ISO; Flatpak ancora no.

## Decisione

Accettata da Vabax il 2026-09-26: date controllate di snapshot.debian.org provate ogni settimana dalla CI, nessun aggiornamento che parta senza l'utente nella serie 0.x, archivio VabaxOS su GitHub Pages di questo repository, due chiavi di firma (una per l'archivio, usata dalla CI; una per le versioni ufficiali, solo sul computer di Vabax). L'archivio e `vabaxctl` entrano nella 0.1 (blocco 13), non più nella 0.2.

### 1. Da dove arrivano gli aggiornamenti

- **Serie 0.x: Debian «a istantanee controllate».** Il sistema installato non segue forky giorno per giorno, ma una data di snapshot.debian.org scelta da VabaxOS. Ogni settimana la CI prova una data nuova: costruisce la ISO, la avvia, installa il sistema in una VM (`test-boot.sh`, `test-install.sh`, registrazioni audio). Se tutto passa, la data nuova si pubblica nel repository VabaxOS (pacchetto `vabaxos-apt`, che scrive le sorgenti APT). Così un aggiornamento che rompe la voce o il desktop si ferma prima di arrivare agli utenti.
- **Correzioni di sicurezza urgenti:** se un problema grave è corretto in unstable o testing, la data si sposta subito, con le stesse prove automatiche e senza aspettare la settimana.
- **Dalla 1.0: Debian stable** con `debian-security` e aggiornamenti di sicurezza automatici (`unattended-upgrades`), come previsto da ADR-0001.
- **Pacchetti VabaxOS** (voce, benvenuto, impostazioni, modello Kokoro): dal repository APT VabaxOS firmato (ADR-0008), dalla v0.2.
- **Applicazioni esterne:** Flatpak, con Flathub attivabile (ADR-0008). Flatpak si aggiunge alla ISO ora.
- **Firmware:** fwupd e LVFS, già presenti, attraverso lo stesso programma di aggiornamento.

### 2. Come si aggiorna, da utente

- **`vabaxos-update`**, programma VabaxOS accessibile, anche da tastiera e da terminale:
  - «Controlla»: dice quanti aggiornamenti ci sono, quanti di sicurezza e quanto scaricano;
  - «Aggiorna ora»: scarica e installa, e annuncia l'avanzamento a voce (notifiche lette da Orca) ogni 25%, poi dice se serve riavviare;
  - «Aggiorna al riavvio» (aggiornamento offline di PackageKit): installa al prossimo avvio, con la voce della console, così la sessione in uso non si rompe a metà. È la scelta predefinita per gli aggiornamenti grossi, come GNOME;
  - Flatpak e firmware nello stesso elenco.
- **Una volta al giorno**, in silenzio, il sistema controlla. Se ci sono aggiornamenti di sicurezza, una notifica lo dice; per gli altri, al massimo una volta alla settimana.
- **Nessun aggiornamento parte senza che l'utente lo chieda**, nella serie 0.x. Dalla 1.0, solo quelli di sicurezza di Debian stable partono da soli.
- La richiesta della password di amministratore è quella di GNOME (polkit), che Orca legge.

### 3. Aggiornamenti rapidi

- Scaricamento in parallelo di APT e mirror CDN (`deb.debian.org`, per stable dalla 1.0); PackageKit scarica in anticipo in background, così «Aggiorna ora» parte subito.
- Pacchetti VabaxOS piccoli e separati: il modello Kokoro (330 MB) cambia raramente, quindi non si riscarica a ogni aggiornamento della voce.

### 4. Sicurezza di base del sistema

- Secure Boot con la catena firmata di Debian (ADR-0003, già provato).
- AppArmor attivo (Debian), sandbox Flatpak per le applicazioni esterne.
- Firme: sorgenti APT solo con chiavi dichiarate (`Signed-By`); la chiave VabaxOS segue ADR-0015.
- Nessun servizio di rete in ascolto per default; firewall: da valutare con un ADR a parte (GNOME non ne ha uno integrato e accessibile).
- `vabaxos-report` e i log non contengono password e non escono dal computer se l'utente non li invia.

## Alternative considerate

- **Seguire forky direttamente (come oggi):** correzioni più veloci, ma ogni giorno può rompersi qualcosa, e un utente non vedente può restare senza voce senza poter chiedere aiuto.
- **Data fissa per sempre (come la ISO):** nessuna rottura, ma nessuna correzione di sicurezza.
- **Solo GNOME Software:** esiste già, ma con Orca è accessibile solo in parte, e non dà informazioni a voce sull'avanzamento.
- **Aggiornamenti automatici anche nella 0.x:** meno fatica, ma su testing il rischio di rotture è troppo alto.

## Conseguenze

- Serve il repository APT VabaxOS (v0.2) e una CI settimanale che prova la data nuova di snapshot.debian.org.
- snapshot.debian.org è lento e ha limiti: con molti utenti servirà un mirror nostro delle date approvate.
- Fino alla v0.2, il sistema installato resta su `deb.debian.org` forky, e `vabaxos-update` lo dice chiaramente all'utente.

## Riesame

- Quando esce il repository VabaxOS (v0.2).
- Al passaggio a Debian stable (1.0).
- Con Btrfs e gli snapshot (v1.5): aggiornamenti con ritorno indietro.
