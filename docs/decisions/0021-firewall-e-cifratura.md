# ADR-0021: Firewall e cifratura del disco

- **Stato:** Accettata (Vabax, 2026-09-26)
- **Data:** 2026-09-25
- **Responsabile:** Vabax (Project Lead), Principal Software Engineer
- **Sostituisce / Sostituita da:** — (completa ADR-0009 per la cifratura)

## Contesto

Nel blocco 7 Vabax ha chiesto un sistema completo, e sicuro. Due funzioni che Windows ha e VabaxOS non ha ancora:

- **Firewall.** Debian non ne attiva uno, GNOME non ha una pagina nelle Impostazioni. VabaxOS non apre servizi di rete per default, ma una persona può installare un programma che lo fa (condivisione di file, desktop remoto).
- **Cifratura del disco.** L'installer di Debian sa cifrare il disco (LUKS2). ADR-0009 la lascia spenta e non consigliata finché non è provata con la voce: la password si chiede all'avvio, **prima** che la voce della console parta. Chi non vede sente solo silenzio e non sa che il computer sta aspettando.

## Decisione

Accettata da Vabax il 2026-09-26: ufw attivo per default già nella 0.1; la cifratura del disco resta per la 0.2, con voce e segnale alla richiesta della password.

### Firewall

1. **ufw attivo per default** nel sistema installato: tutto il traffico in entrata bloccato, quello in uscita permesso. È la stessa scelta di Ubuntu, ma già accesa.
2. Le app che hanno bisogno di ricevere connessioni si aprono con un comando o dalla configurazione VabaxOS, che lo annuncia a voce. Niente finestre in più per chi non le usa.
3. `vabaxos-status` (Super+Alt+I) dice anche «Firewall attivo».
4. Nel sistema live il firewall è attivo allo stesso modo.

### Cifratura del disco

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

- Si aggiunge `ufw` ai pacchetti e un servizio che lo attiva al primo avvio.
- Per la cifratura serve un hook dell'initramfs VabaxOS (voce e segnale), qualche MB in più nell'initramfs, e la prova automatica con registrazione.

## Riesame

- Quando la prova della cifratura con voce passa e Vabax l'ha ascoltata: la cifratura diventa consigliata nell'installer.
- Se ufw blocca qualcosa che le persone usano spesso (stampanti di rete, condivisione): si valuta firewalld con le zone.
