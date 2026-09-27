# Gli aggiornamenti

**Aggiorna VabaxOS**, nel menu Start, cerca gli aggiornamenti e li installa annunciando ogni passo: quanti sono, quanti di sicurezza, l'avanzamento ogni 25% e il risultato. Aggiorna anche le applicazioni Flatpak.

Da terminale:

- `vabaxos-update`: controlla e dice cosa c'è, senza installare;
- `vabaxos-update --now`: scarica e installa subito;
- `vabaxos-update --at-restart`: scarica ora e installa al prossimo avvio, con la voce della console. È il modo più sicuro per gli aggiornamenti grossi, perché la sessione in uso non si rompe a metà.

Ci sono due tipi di aggiornamenti (ADR-0028):

- **Sicurezza:** arrivano subito da Debian e **si installano da soli**, una volta al giorno, senza chiedere niente. Non sulla batteria, e il computer non si riavvia mai da solo: se serve un riavvio (per esempio per un kernel nuovo), una notifica letta da Orca dice «Sono stati installati aggiornamenti di sicurezza. Riavvia il computer appena puoi».
- **VabaxOS:** le versioni nuove di VabaxOS e dei programmi di Debian si installano **solo quando lo chiedi** con Aggiorna VabaxOS. Alla fine VabaxOS dice se serve riavviare: la voce e Orca prendono la versione nuova all'avvio.

Dalla chiavetta (senza installazione) non si installa niente da solo.

La password di amministratore la chiede la finestra di GNOME, che Orca legge.

## Da dove arrivano

VabaxOS si basa su Debian 13 stable. Per non rompere la voce o il desktop, VabaxOS non segue Debian giorno per giorno, tranne che per la sicurezza:

- **Debian a una data controllata.** Il sistema prende i pacchetti di Debian a una data precisa, la stessa con cui VabaxOS è stato costruito e provato. Ogni settimana le prove automatiche di VabaxOS provano una data nuova: costruiscono il sistema, lo avviano, controllano che parli e lo installano. Solo se tutto passa la data nuova arriva agli utenti, come aggiornamento del pacchetto `vabaxos-apt`.
- **I pacchetti di VabaxOS** (voce, benvenuto, impostazioni, menu Start) arrivano dall'archivio di VabaxOS, firmato con la chiave di VabaxOS. APT rifiuta ogni pacchetto con una firma diversa.
- **Sicurezza.** Dall'archivio di sicurezza di Debian, com'è oggi. Alcuni programmi di Debian hanno correzioni di VabaxOS (per esempio speech-dispatcher, che fa parlare Orca): quando Debian li aggiorna per sicurezza, l'aggiornamento arriva subito, e lo stesso giorno VabaxOS lo ripubblica con le sue correzioni; anche questo si installa da solo.
- Il modello della voce Kokoro (330 MB) arriva solo con la ISO: gli aggiornamenti non lo riscaricano.

«Aggiorna ora» installa prima la data nuova di Debian e poi, nello stesso passaggio, i pacchetti di quella data. Con «al prossimo avvio», la data nuova si installa al riavvio e il resto al controllo successivo.

## vabaxctl

`vabaxctl` riassume lo stato del sistema in poche righe, comode da leggere con il lettore di schermo:

- `vabaxctl status` (o solo `vabaxctl`): versione di VabaxOS, se il sistema è installato o avviato dalla chiavetta, la data di Debian, se l'archivio di VabaxOS è attivo, se gli aggiornamenti di sicurezza sono automatici, se serve riavviare, la voce del desktop, se Orca è acceso;
- `vabaxctl voice`: dice la voce del desktop; `vabaxctl voice kokoro`, `vabaxctl voice espeak` o `vabaxctl voice auto` la cambiano (chiede la password di amministratore). La voce nuova parla quando Orca riparte: Super+Alt+S due volte;
- `vabaxctl update`: come `vabaxos-update`, con le stesse opzioni (`--now`, `--at-restart`);
- `vabaxctl report`: come `vabaxos-report`, il rapporto per chiedere aiuto.
