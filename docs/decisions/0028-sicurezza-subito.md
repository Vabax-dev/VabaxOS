# ADR-0028: Aggiornamenti di sicurezza subito, separati da quelli di VabaxOS

- **Stato:** Accettata (Vabax, 2026-09-27)
- **Data:** 2026-09-27
- **Responsabile:** Vabax (Project Lead), Principal Software Engineer
- **Modifica:** [ADR-0020](0020-aggiornamenti-e-sicurezza.md) (punto 1 e 2: la sicurezza non aspetta più una data nuova e non aspetta l'utente); si appoggia su [ADR-0026](0026-pacchetti-debian-corretti.md) e [ADR-0027](0027-base-debian-stable.md)

Decisione di Vabax (2026-09-27): «l'importante è che è stabile e che funziona, gli aggiornamenti di sicurezza li facciamo arrivare subito, che saranno diversi dagli aggiornamenti di VabaxOS, assicurati che aggiornare dalla 0.1 alla successiva non rompa niente e che funzioni». Confermata da Vabax dopo l'attuazione (installazione automatica della sicurezza, senza riavvii automatici): «va bene tutto così come hai fatto».

## Contesto

- Con ADR-0020 il sistema installato segue una data di snapshot.debian.org scelta da VabaxOS, anche per l'archivio di sicurezza. Una correzione di sicurezza arrivava solo con una data nuova, dopo le prove della ISO (circa 75 minuti) e una pull request.
- Con ADR-0027 la base è Debian 13 stable: `trixie-security` riceve solo correzioni piccole e provate da Debian, per tutta la vita della versione. Il rischio di rotture è molto più basso che su testing.
- ADR-0026: VabaxOS ricostruisce alcuni pacchetti di Debian con correzioni sue (speech-dispatcher, GJS), con la versione `<Debian>+0vabaxos1`. Se Debian pubblica un aggiornamento di sicurezza di uno di questi, serve la stessa correzione sulla versione nuova.
- VabaxOS devia (`dpkg-divert`) il file di avvio automatico di Orca. Un aggiornamento di sicurezza di Orca non deve fermarsi su una domanda né togliere l'avvio di VabaxOS.

## Decisione

### 1. Due tipi di aggiornamento

- **Sicurezza** (di Debian e dei pacchetti Debian corretti da VabaxOS): arrivano **subito** e **si installano da soli**, ogni giorno, anche se l'utente non fa niente. Il computer **non si riavvia mai da solo**: se serve (per esempio un kernel nuovo), il controllo giornaliero di `vabaxos-update` lo dice con una notifica letta da Orca.
- **VabaxOS** (versioni nuove dei programmi VabaxOS, una data nuova di Debian con i suoi aggiornamenti normali): come in ADR-0020, **solo quando l'utente lo chiede** con Aggiorna VabaxOS, dopo le prove automatiche.

### 2. Da dove arrivano

- `vabaxos-apt` scrive tre sorgenti:
  - Debian `trixie` e `trixie-updates` alla data di `image/build.conf` (snapshot.debian.org), come prima;
  - **`trixie-security` da `security.debian.org`, com'è oggi**, non più a una data;
  - l'archivio VabaxOS con due componenti: `main` (programmi VabaxOS) e **`debian-fixes`** (pacchetti Debian corretti da VabaxOS).
- La ISO resta a data fissa anche per la sicurezza (`--mirror-chroot-security` a snapshot.debian.org): due costruzioni danno lo stesso sistema. Il sistema installato riceve poi la sicurezza di oggi.

### 3. Installazione automatica, solo della sicurezza

- `unattended-upgrades` (di Debian), con `apt.conf.d/52vabaxos-security` in `vabaxos-apt`: l'elenco di Debian viene tolto e restano **solo due origini**:
  - `origin=Debian,codename=trixie-security,label=Debian-Security`;
  - `origin=VabaxOS,codename=vabaxos,component=debian-fixes`.
- Mai sulla batteria, mai rimozioni automatiche di pacchetti, mai riavvii automatici.
- Nella live non parte (`ConditionKernelCommandLine=!boot=live` su `apt-daily.service` e `apt-daily-upgrade.service`): la live gira in memoria e dimentica tutto allo spegnimento.

### 4. Pacchetti Debian corretti da VabaxOS

- Il suffisso di versione è **`+0vabaxos1`**: viene dopo la versione di Debian e **prima** di ogni suo aggiornamento (`+deb13u1` di trixie-security, `+b1`). Quindi un aggiornamento di sicurezza di Debian vince sempre sulla ricostruzione della versione vecchia: la sicurezza non aspetta mai VabaxOS.
- Ogni giorno la CI (`archive.yml`) ricostruisce i pacchetti corretti alla versione più recente che vedono i sistemi VabaxOS (la data di `image/build.conf` più la sicurezza di oggi), con lo stesso script della ISO (`scripts/build-debian-patched.sh`), e li pubblica in `debian-fixes`. Esempio: Debian pubblica `0.12.0-5+deb13u1`; il sistema lo installa subito (senza la correzione di VabaxOS); lo stesso giorno arriva `0.12.0-5+deb13u1+0vabaxos1`, di nuovo con la correzione, anche questo da solo.
- Si pubblicano tutti i pacchetti del sorgente ricostruito, così nessun pacchetto dello stesso sorgente resta indietro e blocca gli altri.

### 5. Aggiornare da una versione di VabaxOS alla successiva senza rompere niente

Prove automatiche, oltre a quelle che c'erano:

- **`tests/packages/test-upgrade-packages.sh`** (CI breve, `checks.yml`, pochi minuti): installa i pacchetti dell'ultima versione (l'ultimo tag `v*`; prima della 0.1 i pacchetti di `HEAD`), poi quelli nuovi con una versione più alta. Controlla gli script dei pacchetti in aggiornamento, i file spostati fra pacchetti senza `Replaces`, le diversioni, i file di configurazione, e un aggiornamento di sicurezza di Orca (nessuna domanda, avvio di VabaxOS conservato). Ogni `dpkg` legge da `/dev/null`: una domanda fa fallire la prova.
- **`scripts/test-upgrade.sh`** (CI della ISO, `iso.yml`, dopo `test-install.sh`): parte dal sistema installato in QEMU, scrive un'impostazione di Orca come fa l'utente, aggiunge un archivio con la versione successiva firmato con una chiave usa e getta e aggiorna con `vabaxos-update --now` (PackageKit, come Aggiorna VabaxOS). Controlla: tutti i pacchetti alla versione nuova, niente installato a metà, niente file di configurazione messo da parte, impostazioni dell'utente conservate, benvenuto che non torna, sicurezza automatica con solo due origini. Poi riavvia: schermata di accesso e voce della console udibili, servizi attivi. Dopo l'uscita della 0.1 la prova parte dal disco installato con la ISO della 0.1.
- Le impostazioni di Orca date da VabaxOS si aggiornano **tasto per tasto**: una versione nuova aggiunge i suoi tasti anche a chi ne ha cambiato qualcuno, e non tocca mai un tasto o un valore scelto dall'utente.
- Dopo un aggiornamento di VabaxOS, `vabaxos-update` dice di riavviare: voce, avvio di Orca e servizi VabaxOS prendono la versione nuova all'avvio.
- Regola per chi sviluppa: un file che passa da un pacchetto VabaxOS a un altro richiede `Replaces` e `Breaks`; un file di un altro pacchetto si sostituisce solo con la diversione e un collegamento (mai lo stesso percorso come file di configurazione nostro: dpkg tiene i file di configurazione per percorso).

## Alternative considerate

- **Sicurezza a data fissa, spostata da VabaxOS (ADR-0020):** tutto provato prima, ma una correzione urgente arriva dopo ore o giorni, e solo se l'utente aggiorna.
- **Sicurezza subito ma installata solo quando l'utente la chiede:** l'utente decide, ma chi non apre mai Aggiorna VabaxOS resta scoperto; una persona che non vede lo schermo non deve dover ricordarsene.
- **Pacchetti corretti con versione più alta di ogni aggiornamento Debian (per esempio epoch o `+vabaxos1`):** la correzione resterebbe, ma un aggiornamento di sicurezza di Debian non verrebbe mai installato finché VabaxOS non lo ricostruisce. Scartato: la sicurezza viene prima.
- **Riavvio automatico dopo un kernel nuovo:** il sistema sarebbe protetto prima, ma un riavvio inatteso interrompe il lavoro e la voce. Scartato.

## Conseguenze

- `vabaxos-apt` dipende da `unattended-upgrades`.
- La CI `archive.yml` gira ogni giorno; i pacchetti ricostruiti restano in cache finché le versioni di Debian e le correzioni non cambiano.
- Fra un aggiornamento di sicurezza di speech-dispatcher o GJS e la ricostruzione (al massimo un giorno) il sistema gira senza la correzione di VabaxOS: il difetto raro di ADR-0026 può tornare per quelle ore. È il prezzo di non far aspettare la sicurezza.
- Un aggiornamento di sicurezza di Debian non passa dalle prove della ISO di VabaxOS: ci si fida delle prove di Debian stable.
- Il meccanismo di ADR-0020 per testing (`VABAXOS_SECURITY_SNAPSHOT`, campo `Vabaxos-Security-Snapshot`) non serve più ed è tolto.
- L'archivio VabaxOS deve esistere (chiavi e Pages, `docs/sviluppo/chiavi.md`) prima di costruire la ISO della 0.1, altrimenti i sistemi della 0.1 non ricevono né le versioni successive né i pacchetti corretti.

## Riesame

- Se un aggiornamento di sicurezza di Debian rompe la voce o il desktop: valutare un ritardo breve con prova automatica prima dell'installazione.
- Con Btrfs e gli snapshot (v1.5): aggiornamenti con ritorno indietro.
