# Modalità di recupero

Quando VabaxOS non parte bene, o la voce del desktop non torna nemmeno con **Ctrl+Super+Invio**, la modalità di recupero avvia il computer solo fino alla console di testo, con la voce, e offre un menu per rimettere le cose a posto.

## Come si entra

- **Dalla chiavetta o dal DVD (sistema live):** ai due bip del menu di avvio premi **R**.
- **Nel sistema installato:** ai due bip del menu di avvio premi **Freccia giù** una volta e poi **Invio**. La seconda voce del menu è la modalità di recupero con voce. Se ci sono più versioni del kernel, le voci sono a coppie: avvio normale, poi recupero.

## Il menu

La voce della console legge il menu una riga alla volta. Premi il numero, senza Invio:

1. **Avvia il desktop:** continua l'avvio fino al desktop;
2. **Rimetti la voce:** per ogni utente, riaccende la voce di Orca con eSpeak NG e il lettore di schermo, dopo aver salvato una copia delle impostazioni di Orca (come Ctrl+Super+Invio);
3. **Rimetti le impostazioni di ieri:** per ogni utente, rimette voce e desktop dall'ultima [copia automatica](copia-impostazioni.md);
4. **Completa gli aggiornamenti interrotti:** se un aggiornamento si è fermato a metà, per esempio per un computer spento, lo porta a termine;
5. **Salva un rapporto:** scrive `vabaxos-report-recovery.txt` nella cartella Home di ogni utente, da mandare con una segnalazione;
6. **Rete:** apre `nmtui` per collegarsi a una rete Wi-Fi;
7. **Console di testo:** chiude il menu e chiede nome e password, per lavorare nel terminale;
8. **Riavvia;**
9. **Spegni.**

Dopo ogni azione la voce dice com'è andata e rilegge il menu. I tasti di revisione della voce della console rileggono tutto quello che è stato detto.

## Cosa cambia rispetto a Debian

In Debian la modalità di recupero chiede la password dell'amministratore (root), che in VabaxOS non esiste, ed è muta. In VabaxOS il menu parla e non chiede password: le sue azioni rimettono solo a posto. La console di testo chiede nome e password, come sempre.
