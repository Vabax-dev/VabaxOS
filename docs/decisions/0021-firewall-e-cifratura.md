# ADR-0021: Firewall e cifratura del disco

- **Stato:** Accettata. Cifratura: Vabax, 2026-11-01 («devi mettere la cifratura»), fatta in `vabaxos-unlock`. Firewall: Vabax, 2026-11-01 («il firewall sì, ma come quello di Windows, cioè non troppo limitante»), con firewalld al posto di ufw, fatto in `vabaxos-firewall`
- **Data:** 2026-09-25
- **Responsabile:** Vabax (Project Lead), Principal Software Engineer
- **Sostituisce / Sostituita da:** — (completa ADR-0009 per la cifratura)

## Contesto

Nel blocco 7 Vabax ha chiesto un sistema completo, e sicuro. Due funzioni che Windows ha e VabaxOS non ha ancora:

- **Firewall.** Debian non ne attiva uno, GNOME non ha una pagina nelle Impostazioni. VabaxOS non apre servizi di rete per default, ma una persona può installare un programma che lo fa (condivisione di file, desktop remoto).
- **Cifratura del disco.** L'installer di Debian sa cifrare il disco (LUKS2). ADR-0009 la lascia spenta e non consigliata finché non è provata con la voce: la password si chiede all'avvio, **prima** che la voce della console parta. Chi non vede sente solo silenzio e non sa che il computer sta aspettando.

## Decisione

### Firewall

Vabax (2026-11-01): «il firewall sì, ma come quello di Windows, cioè non troppo limitante». Per questo **firewalld** e non ufw, come proposto all'inizio: firewalld ha le zone, che NetworkManager assegna a ogni rete come i profili di Windows; i programmi possono aprire una porta via D-Bus; con ufw ci sono segnalazioni di KDE Connect bloccato.

1. **firewalld attivo**, nel sistema live e in quello installato. In uscita tutto è permesso, come in Windows.
2. **Due tipi di rete, come in Windows** (pacchetto `vabaxos-firewall`):
   - **privata** (casa, lavoro; zona `vabaxos-private`): entrano solo le risposte che servono a trovare dispositivi e stampanti (mDNS, LLMNR, UPnP, stampanti), le cartelle condivise degli altri computer e il collegamento con il telefono (KDE Connect, GSConnect);
   - **pubblica** (bar, albergo, treno; zona `vabaxos-public`): non entra niente, il computer non si mostra agli altri.
3. **Le reti nuove sono private** (zona predefinita `vabaxos-private`): «non troppo limitante». Windows chiede alla prima connessione; VabaxOS lo fa scegliere nella configurazione, pagina Rete («Tipo di rete»), e con `vabaxos-firewall public`.
4. **Programmi consentiti**, spenti all'inizio come in Windows, solo nelle reti private: condivisione dei file (Samba), desktop remoto (RDP), terminale remoto (SSH). Si accendono nella configurazione, pagina Rete, o con `vabaxos-firewall allow`; la password di amministratore la chiede polkit, che Orca legge.
5. `vabaxos-status` (Super+Alt+I) dice «Firewall attivo».

Non c'è, per ora, la finestra di Windows «Consentire a questo programma di comunicare?»: firewalld non avvisa quando un programma vuole ricevere connessioni.

### Cifratura del disco

Fatto il 2026-11-01 (pacchetto `vabaxos-unlock`, prove in `tests/unlock` e `test-install.sh --encrypt`):

- l'installer offre già «Guidato - usa l'intero disco e imposta LVM cifrato»; `cryptsetup`, `cryptsetup-initramfs` e `lvm2` sono nella ISO, perché l'installer copia il sistema della chiavetta;
- un hook dell'initramfs, solo quando un disco è cifrato, aggiunge eSpeak NG con la lingua del sistema, aplay, alsactl, i driver audio e l'altoparlante del PC, e mette davanti all'`askpass` di Debian quello di VabaxOS: due note, «Scrivi la password del disco, poi premi Invio», «Password sbagliata» dal secondo tentativo (`CRYPTTAB_TRIED`), «Disco aperto» alla fine; la password la legge sempre il programma di Debian, la voce parla in sottofondo;
- nessuna modifica a `/etc/crypttab`; `/etc/vabaxos/unlock.conf` permette di spegnere la voce o cambiare le frasi.

Restano: la prova in QEMU (`test-install.sh --encrypt`) e l'ascolto di Vabax; il Braille (brltty nell'initramfs); i portatili con audio SOF, il cui firmware può non essere nell'initramfs.

Il piano iniziale:

1. Resta **una scelta dell'installer**, spenta per default (ADR-0009).
2. Si potrà consigliare solo quando la richiesta della password è accessibile. Prima di quel momento:
   - un segnale sonoro con l'altoparlante del PC, come i bip del menu di avvio, ma diverso, indica che il computer aspetta la password;
   - la voce: eSpeak NG e i driver audio dentro l'initramfs, per dire «Scrivi la password del disco, poi premi Invio», e poi «Password sbagliata» o «Disco aperto»;
   - il Braille: brltty nell'initramfs, che Debian già supporta, per le barre Braille.
3. Una prova automatica in QEMU installa con la cifratura, riavvia, registra l'audio alla richiesta della password e controlla che la voce parli. Vabax ascolta prima di rendere la scelta consigliata.
4. Obiettivo: v0.2.

## Alternative considerate

- **Nessun firewall, come Debian:** oggi non c'è nulla in ascolto, ma basta un programma installato dopo.
- **firewalld:** più ricco (zone per rete di casa, lavoro, pubblica), integrato con NetworkManager, ma più complesso da spiegare e senza una finestra accessibile in GNOME.
- **Cifratura consigliata subito:** senza voce alla richiesta della password, una persona cieca può restare bloccata all'avvio senza capire perché.

## Conseguenze

- Si aggiungono firewalld e `vabaxos-firewall` (le due zone, il comando, il gruppo Firewall nella configurazione). firewalld è un servizio in Python: qualche decina di MB di memoria.
- Per la cifratura serve un hook dell'initramfs VabaxOS (voce e segnale), qualche MB in più nell'initramfs, e la prova automatica con registrazione.

## Riesame

- Quando la prova della cifratura con voce passa e Vabax l'ha ascoltata: la cifratura diventa consigliata nell'installer.
- Se la rete privata blocca qualcosa che le persone usano spesso: si aggiunge il servizio alla zona `vabaxos-private`.
- Se serve l'avviso di Windows quando un programma vuole ricevere connessioni.
