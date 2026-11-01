# Wi-Fi e Bluetooth

**Wi-Fi e Bluetooth**, nel menu Start, ha due pagine: Wi-Fi e Bluetooth. **Super+K** apre subito la pagina Bluetooth. **Ctrl+Pagina giù** e **Ctrl+Pagina su** cambiano pagina; **Esc** chiude.

Quando apri una pagina, VabaxOS dice come stanno le cose, per esempio «Collegato a Casa, segnale ottimo» oppure «Bluetooth acceso, collegato: Cuffie Sony».

## Wi-Fi

- **Wi-Fi** accende e spegne il Wi-Fi.
- **Reti**: le reti vicine, dalla più forte. Ogni rete ha il nome, se è protetta da password e il segnale a parole: ottimo, buono, discreto o debole.
- **Invio** su una rete la collega. Se è protetta, VabaxOS chiede la password: scrivila e premi Invio. VabaxOS dice «Collegato a…» oppure «Non collegato: la password forse è sbagliata, o la rete è troppo lontana».
- **Invio** sulla rete collegata offre **Scollega** e **Dimentica** (VabaxOS non ricorda più la password).
- **F5** cerca di nuovo le reti.
- **Rete nascosta**: per le reti che non mostrano il nome; scrivi nome e password.

Le reti «aperte, non protette» funzionano, ma chi è vicino può vedere cosa fai: VabaxOS te lo ricorda prima di collegarle.

Le reti delle università e delle aziende chiedono anche un nome utente: per queste usa una volta le Impostazioni di GNOME, pagina Wi-Fi; poi VabaxOS le collega da solo.

Se la password salvata non è più giusta, GNOME può chiederla di nuovo in una sua finestra: Orca la legge.

## Bluetooth

- **Bluetooth** lo accende e lo spegne.
- **I miei dispositivi**: quelli già abbinati, con il tipo (cuffie, tastiera, display Braille…), se sono collegati e la batteria, quando il dispositivo la comunica. **Invio** offre **Collega** o **Scollega** e **Rimuovi**.
- **Dispositivi nuovi**: metti il dispositivo in modalità di abbinamento (di solito tenendo premuto il tasto di accensione o il tasto Bluetooth), poi **Cerca dispositivi** (oppure **F5**). Per 30 secondi VabaxOS dice i nomi dei dispositivi che trova. **Invio** su un dispositivo lo abbina e lo collega.

Durante l'abbinamento, alcuni dispositivi chiedono un codice:

- **Stesso codice?** VabaxOS dice il codice cifra per cifra: se il dispositivo mostra lo stesso, scegli **Sì**.
- **Codice del dispositivo**: scrivi il codice indicato nel manuale, spesso 0000 o 1234.
- **Scrivi il codice sulla tastiera**: per le tastiere Bluetooth, VabaxOS dice le cifre da scrivere sulla tastiera nuova, seguite da Invio.

Le cuffie e gli altoparlanti di solito si abbinano senza domande. Un dispositivo abbinato si ricollega da solo quando lo accendi.

## Display Braille

Molti display Braille si collegano anche con il Bluetooth: abbinali qui, poi controlla con il comando `vabaxos-braille-check` (vedi [Il Braille](braille.md)).
