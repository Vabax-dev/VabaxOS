# ADR-0026: L'archivio APT di VabaxOS e la chiave del progetto

- **Stato:** Proposta
- **Data:** 2026-09-26
- **Responsabile:** Vabax (Project Lead), Principal Software Engineer
- **Sostituisce / Sostituita da:** — (attua ADR-0008 e la firma di ADR-0015)

## Contesto

ADR-0008 prevede un archivio APT VabaxOS firmato dalla v0.2: oggi i pacchetti `vabaxos-*` arrivano solo con la ISO, e un sistema installato non riceve le correzioni (per esempio quelle di Kokoro e di Orca del 2026-09-26) se non si reinstalla. ADR-0015 chiede che dalla prima alpha pubblica `SHA256SUMS` sia firmato con una chiave OpenPGP del progetto. Il 2026-09-26 Vabax ha scelto di pubblicare la 0.1 dopo la prova sul mini PC e con la firma (scelta A), e ha approvato il blocco 13 «Aggiornamenti VabaxOS».

Cose da sapere:

- APT verifica le firme con `sqv` (Sequoia): le chiavi con SHA-1 sono rifiutate dal 2026, le chiavi RSA a 2048 bit lo saranno dal 2030. Una chiave **Ed25519** va bene per molti anni.
- Il formato moderno delle sorgenti APT è **deb822** (file `.sources`) con `Signed-By`: la chiave vale solo per l'archivio VabaxOS, non per tutti gli archivi del sistema.
- Sulla postazione ci sono già `apt-ftparchive` e `gpg`: bastano per costruire e firmare un archivio piccolo, senza servizi in più.
- Un archivio APT è un insieme di file statici: può stare su qualunque hosting web.

## Decisione proposta

### 1. Dove sta l'archivio

- **GitHub Pages di un repository a parte, `Vabax-dev/vabaxos-apt`**, all'indirizzo `https://vabax-dev.github.io/vabaxos-apt/`. È gratuito, con HTTPS, e tiene fuori dal repository del codice i file binari che cambiano a ogni pubblicazione.
- Creare quel repository e attivare Pages è un'impostazione di GitHub: **lo fa Vabax, o lo autorizza**.
- Struttura: `dists/forky/main/binary-{all,amd64}` con `InRelease` firmato; i pacchetti in `pool/main/`. La serie 0.x usa il nome `forky`, come la base (ADR-0017).

### 2. La chiave del progetto

- **Una chiave OpenPGP Ed25519** «VabaxOS Project Signing Key»: una chiave principale che serve solo a certificare, e una **sottochiave di firma** con scadenza di due anni, rinnovabile.
- La sottochiave firma **l'archivio APT** e **`SHA256SUMS` delle ISO** (ADR-0015). Una chiave sola da custodire e da verificare, per un progetto piccolo.
- **La crea Vabax** sulla postazione, con `scripts/keys/create-project-key.sh` nella finestra di Debian: la passphrase la scrive solo lui, e non passa mai dalla chat. Lo script esporta la chiave pubblica in `keys/vabaxos-project.asc` (nel repository) e una copia di sicurezza della chiave segreta su una chiavetta scelta da Vabax.
- L'impronta si pubblica nel README, nella guida alla verifica e su vabax.it.

### 3. I pacchetti

- **`vabaxos-archive-keyring`**: la chiave pubblica in `/usr/share/keyrings/vabaxos-archive-keyring.pgp` e le sorgenti in `/etc/apt/sources.list.d/vabaxos.sources` (deb822, `Signed-By`). È nella ISO, quindi il sistema installato riceve gli aggiornamenti VabaxOS senza fare niente.
- Finché l'archivio non è online le sorgenti restano scritte ma disattivate (`Enabled: no`), così `apt update` non segnala errori.
- **Versioni che crescono sempre:** la base è in `packages/VERSION` (per esempio `0.1.0~alpha.1`); le costruzioni di sviluppo aggiungono `+git` con la data del commit. Così un aggiornamento dall'archivio vince sempre su una ISO più vecchia.

### 4. Come si pubblica

- `scripts/apt-repo.sh` costruisce l'archivio in `out/apt` dai pacchetti di `out/packages` e lo firma con la chiave del progetto (la passphrase la chiede gpg a Vabax, nella finestra di Debian).
- `scripts/publish-apt.sh` lo copia nel repository `vabaxos-apt` e lo invia. Pubblicare è come fare un rilascio: **solo con il sì di Vabax**.
- La CI costruisce ogni volta un archivio con una chiave usa e getta e lo prova con APT (`tests/apt/test_apt_repo.sh`): firma, `Signed-By`, versioni, installazione.
- Più avanti la firma potrà passare alla CI con una sottochiave dedicata nei segreti di GitHub (altro ADR, altra impostazione di Vabax).

## Alternative considerate

- **Archivio nel repository del codice (cartella `docs/` su Pages):** un solo repository, ma il codice si riempie di file binari a ogni pubblicazione.
- **Server nostro con aptly o reprepro:** più funzioni (più suite, rimozioni), ma un server da mantenere e da pagare; da rivalutare con molti utenti.
- **Launchpad PPA o Open Build Service:** servono per Ubuntu e openSUSE; per Debian forky non c'è un servizio comodo.
- **Due chiavi separate, archivio e ISO (come Debian):** più sicuro, ma due chiavi da custodire per una persona sola. Si separano quando il progetto cresce.
- **Firma nella CI da subito:** comodo, ma la chiave uscirebbe dalla postazione prima di avere regole per custodirla.
- **Sigstore (ADR-0015):** APT non lo verifica.

## Motivazione

Con l'archivio le correzioni arrivano a chi ha già installato VabaxOS, anche la voce e il lettore di schermo. Con file statici, `apt-ftparchive` e `gpg` non c'è niente da mantenere. La chiave Ed25519 con `Signed-By` segue le regole attuali di APT e di Debian, e tenerla sulla postazione di Vabax, con la passphrase solo sua, lascia a lui il controllo di cosa viene firmato.

## Conseguenze

- Vabax crea la chiave (un comando) e il repository `vabaxos-apt` con Pages (o autorizza a crearlo).
- `SHA256SUMS` della 0.1 si firma con la stessa chiave: `scripts/sign-release.sh`, e la guida accessibile «Verificare la ISO».
- ADR-0020 (aggiornamenti e sicurezza, ancora Proposta) decide invece da dove arrivano i pacchetti Debian: questo ADR riguarda solo quelli VabaxOS.
- I sistemi installati prima del 2026-09-26 hanno i pacchetti `0.1.0~dev`, che per APT vengono dopo `0.1.0~alpha.1`: sono solo installazioni di prova (per esempio quella in VMware), da reinstallare.
- Se la chiave si perde, o la passphrase: nuova chiave, nuovo `vabaxos-archive-keyring` firmato con la vecchia finché è valida, avviso nel CHANGELOG.

## Riesame

- Alla v0.5 o con molti utenti: server proprio, suite separate (stabile e di prova), firma nella CI.
- Quando scade la sottochiave (due anni), o se la chiave è compromessa.
