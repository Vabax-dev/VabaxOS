# ADR-0020: Aggiornamenti e sicurezza

- **Stato:** Accettata
- **Data:** 2026-10-02
- **Responsabile:** Vabax, Claude
- **Sostituisce / Sostituita da:** —

## Contesto

VabaxOS deve gestire gli aggiornamenti in modo sicuro e accessibile. Problemi da risolvere:

1. **Sicurezza:** Aggiornamenti di sicurezza critici (kernel, librerie, GNOME, Orca) devono arrivare velocemente
2. **Accessibilità:** L'utente deve sapere cosa si aggiorna, con output vocale
3. **Affidabilità:** Non rompere il sistema con aggiornamenti non testati
4. **Autonomia:** L'utente deve poter aggiornare da solo, senza vista

Serie 0.x (sviluppo):
- Base: Debian testing «forky» a snapshot fisso (ADR-0017)
- `--security false --updates false` come le ISO live di testing
- Nessun aggiornamento automatico Debian (testing non ha security)

Serie 1.x (produzione):
- Base: Debian 14 «forky» stable
- Security updates disponibili
- Necessario un sistema completo

## Decisione

VabaxOS fornisce **aggiornamenti accessibili a voce** attraverso:

1. **Repository APT VabaxOS** (GitHub Pages o server dedicato)
   - Pacchetti `vabaxos-*` firmati con chiave OpenPGP del progetto
   - File deb822 `.sources` per repository separato
   - Pubblicato con `reprepro` o `aptly`

2. **Programma `vabaxos-update`** (GTK 4 + CLI)
   - Controlla aggiornamenti disponibili (APT + Flatpak)
   - Legge i changelog a voce
   - Mostra priorità (sicurezza, bug fix, nuove funzionalità)
   - Installa con progress vocale
   - Riavvia se necessario (con avviso)

3. **Notifiche accessibili**
   - Controllo giornaliero automatico (impostabile)
   - Notifica vocale: "3 aggiornamenti disponibili, 2 di sicurezza"
   - Cliccabile per aprire `vabaxos-update`

4. **Aggiornamenti automatici di sicurezza** (opzionali)
   - Solo per pacchetti Debian con priorità security
   - Mai per kernel o GNOME (richiedono riavvio)
   - Disabilitabili dall'utente

## Alternative considerate

### A. Solo aggiornamenti manuali
**Perché no:** Utenti non tecnici rischiano di rimanere senza patch di sicurezza per mesi.

### B. `unattended-upgrades` di Debian
**Perché no:** Non accessibile (log solo testuali, nessuna voce), non gestisce pacchetti VabaxOS.

### C. GNOME Software
**Perché no:** Problemi di accessibilità noti con Orca (navigazione confusa, feedback vocale incompleto).

### D. Repository diretto su GitHub Releases
**Perché no:** APT non supporta nativamente GitHub API, richiederebbe wrapper complesso.

## Motivazione

### Repository APT separato
- **Indipendenza:** Pacchetti VabaxOS aggiornabili senza aspettare Debian
- **Velocità:** Correzioni critiche (es. bug Orca, Kokoro) disponibili in ore, non settimane
- **Controllo:** Possiamo testare ogni aggiornamento prima del rilascio
- **Standard:** APT è lo standard Debian, nessun tool custom

### Interfaccia vocale
- **Necessità:** `apt upgrade` nel terminale non è accessibile (troppo output, nessuna struttura)
- **Esperienza:** Windows Update funziona con NVDA, VabaxOS deve fare altrettanto
- **Fiducia:** Sapere cosa si installa aumenta la fiducia dell'utente

### Aggiornamenti automatici limitati
- **Sicurezza critica:** Patch SSL, sudo, kernel (tramite livepatch se disponibile) non devono aspettare
- **Prudenza:** Desktop e componenti critici solo con approvazione esplicita
- **Scelta:** Opzione disattivabile per utenti esperti

## Conseguenze

### Cosa diventa più facile
- Correggere bug nei pacchetti VabaxOS senza aspettare Debian
- Fornire nuove voci Kokoro, aggiornamenti Orca, estensioni GNOME
- Garantire sicurezza anche su testing/unstable (serie 0.x)

### Cosa diventa più difficile
- Manutenzione del repository APT (build, firma, pubblicazione)
- Infrastruttura (server, CI per build automatiche, bandwidth)
- Coordinamento versioni (VabaxOS packages vs Debian base)

### Da fare ora (v0.1 / v0.2)
1. Generare chiave OpenPGP del progetto VabaxOS (Ed25519)
2. Setup repository (GitHub Pages + reprepro, o server dedicato)
3. CI per build e pubblicazione automatica pacchetti
4. Pacchetto `vabaxos-keyring` con la chiave pubblica
5. File `.sources` per il repository in `/etc/apt/sources.list.d/`
6. Implementare `vabaxos-update`:
   - Backend: python-apt per query e installazione
   - Frontend GTK 4: lista aggiornamenti, dettagli, pulsante "Installa"
   - CLI: output strutturato, opzione `--speak`
   - Lettura changelog con speech-dispatcher
7. Servizio systemd timer per controllo giornaliero
8. Test: simulare aggiornamenti, verificare voce, rollback

### Da fare più avanti (v1.0+)
- Aggiornamenti differenziali (delta updates) per risparmiare banda
- Firma delle release ISO con la stessa chiave
- Mirror del repository per resilienza
- Integrazione con `vabaxos-doctor` (verifica dopo aggiornamento)

## Riesame

Questa decisione va rivista se:
1. Debian introduce un sistema di aggiornamenti accessibile nativo
2. La manutenzione del repository diventa insostenibile
3. Un sistema di terze parti (Flatpak, Snap) copre tutti i casi d'uso
4. Feedback utenti: il sistema non è abbastanza accessibile

## Note implementative

### Struttura del repository

```
deb822-style .sources file:
Types: deb deb-src
URIs: https://apt.vabax.org/vabaxos
Suites: forky forky-updates
Components: main
Signed-By: /usr/share/keyrings/vabaxos-archive-keyring.gpg
```

### Priorità changelog
- **Security:** Vulnerabilità CVE, patch critiche
- **Bug fix:** Correzioni di difetti (crash, voce muta, estensioni)
- **Feature:** Nuove funzionalità
- **Update:** Aggiornamenti versioni (es. nuova voce Kokoro)

### Speech output
```
"3 aggiornamenti disponibili.
2 di sicurezza: vabaxos-accessibility, orca.
1 aggiornamento di funzionalità: vabaxos-voice.

vabaxos-accessibility, versione 0.1.2:
Corretto il memory leak dell'estensione button-names che causava
il freeze di GNOME Shell dopo molte notifiche.

Installa ora?"
```

### Comando completo
```bash
# Interfaccia grafica
vabaxos-update

# CLI con sintesi vocale
vabaxos-update --cli --speak

# Solo controllo (no installazione)
vabaxos-update --check

# Aggiornamenti di sicurezza automatici
vabaxos-update --security --non-interactive
```
