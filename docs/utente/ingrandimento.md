# Ingrandimento e contrasto

Per chi vede poco: VabaxOS ingrandisce lo schermo, aumenta il contrasto e fa più grandi testo e puntatore, **con un tasto**. A ogni tasto Orca dice cosa è cambiato; se Orca è spento, compare un breve avviso sullo schermo.

## I tasti

- **Super+più** e **Super+meno** (anche quelli del tastierino numerico): ingrandisce e rimpicciolisce, come Win+più e Win+meno di Windows. Il primo Super+più accende l'ingrandimento; rimpicciolendo fino a 1 si spegne.
- **Super+Alt+8**: accende e spegne l'ingrandimento.
- **Super+Ctrl+C**: alto contrasto, acceso o spento, come Win+Ctrl+C dei filtri colore di Windows.
- **Super+Ctrl+più** e **Super+Ctrl+meno**: testo più grande o più piccolo, da normale a 3 volte.

## La finestra

**Ingrandimento e contrasto**, nel menu Start, ha tutte le scelte:

- **Ingrandimento** e **Quanto**, da 1 a 16 volte;
- **L'ingrandimento segue il cursore:** tenendolo al centro (comodo con la tastiera), spostandosi solo quando serve, oppure spinto dal cursore quando arriva al bordo;
- **Mirino:** due linee che si incrociano dove c'è il puntatore;
- **Alto contrasto**, **Colori invertiti** (lettere chiare su sfondo scuro) e **Bianco e nero**;
- **Grandezza del testo** e **Grandezza del puntatore**, fino a quattro volte;
- **Meno movimento:** meno animazioni.

Colori invertiti e bianco e nero passano dall'ingrandimento di GNOME: se l'ingrandimento è spento, si accende a 1 volta, cioè lo schermo intero com'è.

Le stesse scelte, più semplici, sono anche nella [configurazione iniziale](configurazione.md) e nelle Impostazioni di GNOME, pagina Accessibilità (Super+U): sono le stesse impostazioni.

Dal terminale: `vabaxos-vision zoom-in`, `zoom-out`, `contrast`, `text-bigger`, `text-smaller`, `invert`, `grey`, `status`.
