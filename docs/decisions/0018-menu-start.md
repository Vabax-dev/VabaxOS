# ADR-0018: Menu Start con il logo di VabaxOS

- **Stato:** Sostituita (Vabax, 2026-09-26: ADR-0025, il menu Start di VabaxOS per tutti; ArcMenu tolto nel blocco 15)
- **Data:** 2026-09-24
- **Responsabile:** Vabax (Project Lead, responsabile accessibilità), Principal Software Engineer
- **Sostituisce / Sostituita da:** sostituita da [ADR-0025](0025-menu-start-vabaxos.md)

## Contesto

Richiesta di Vabax: un menu Start a metà fra il menu Start di Windows 7 e il menu Apple di macOS, con il logo di VabaxOS come simbolo.

- Il menu Start di Windows 7 ha i programmi usati di recente, la ricerca mentre si scrive, le cartelle principali e i comandi di spegnimento.
- Il menu Apple di macOS ha i comandi di sistema: informazioni, impostazioni, stop, riavvia, spegni, blocca schermo, esci.

GNOME (ADR-0004) non ha un menu Start. Il tasto Super apre la panoramica delle attività, che Orca legge, ma è a schermo intero e non ha i comandi di sistema in un solo posto.

Il menu deve stare nella barra in alto di GNOME Shell. Con Wayland solo un'estensione di GNOME Shell può mettere un pulsante lì; un normale programma GTK non può scegliere dove comparire.

## Decisione

1. **Si usa ArcMenu**, l'estensione di GNOME Shell già pacchettizzata in Debian (`gnome-shell-extension-arc-menu`, 69.2 in forky, licenza GPL-2.0-or-later, dichiara il supporto per GNOME 45–50).
2. **Aspetto:** il simbolo di VabaxOS (icona `vabaxos-logo` di `vabaxos-branding`) all'inizio della barra in alto. Il menu ha tre parti:
   - la casella di ricerca, con il cursore già dentro;
   - i programmi preferiti e recenti, poi «Tutti i programmi»;
   - i comandi di sistema: Informazioni su VabaxOS, Impostazioni, Blocca, Esci, Sospendi, Riavvia, Spegni.
3. **Tasti:** Super apre e chiude il menu, come in Windows. La panoramica di GNOME resta con Super+A e con il pulsante Attività. Nel menu: si scrive per cercare, frecce per scorrere, Invio per aprire, Esc per chiudere.
4. **Configurazione da VabaxOS:** l'estensione è attiva per tutti gli utenti e le impostazioni stanno in un file di `vabaxos-settings` (override di GSettings), non in modifiche al codice di ArcMenu.
5. **Condizione per accettarla:** prima della prova di ascolto, `vabaxos-a11y-check gnome-shell` non deve trovare comandi senza nome dentro il menu, e Orca deve leggere ogni voce. Se ArcMenu non supera questa prova, si passa all'alternativa B.

## Alternative considerate

- **A. Solo la panoramica di GNOME:** nessun lavoro, ma non è quello che Vabax ha chiesto e non ha i comandi di sistema in un posto solo.
- **B. Un'estensione di VabaxOS scritta da noi:** controllo completo di cosa legge Orca, ma va scritta in JavaScript (l'unico linguaggio delle estensioni di GNOME Shell, eccezione ad ADR-0010) e va aggiornata a ogni versione di GNOME. È il ripiego se ArcMenu non è accessibile.
- **C. Un programma GTK 4 aperto con un tasto:** accessibile e in Python, ma su Wayland compare come una finestra normale al centro dello schermo, non attaccato al simbolo nella barra.
- **D. Apps Menu delle estensioni classiche di GNOME:** accessibile, ma è solo un elenco di categorie, senza ricerca e senza comandi di sistema.

## Motivazione

ArcMenu è l'estensione di menu più usata, già in Debian, con molti schemi già pronti, fra cui uno simile a Windows 7. Usare un pacchetto di Debian invece di codice nostro riduce il lavoro di manutenzione.

## Conseguenze

- Si aggiunge `gnome-shell-extension-arc-menu` alla lista dei pacchetti; `vabaxos-settings` lo attiva e lo configura.
- A ogni nuova versione di GNOME bisogna aspettare che ArcMenu sia aggiornato in Debian. Il tracker di Debian segnala già la transizione a GNOME 51.
- Le traduzioni di ArcMenu esistono già per l'italiano.
- `test-boot.sh` controlla che il menu si apra con Super e che la prova di accessibilità passi.

## Riesame

- ArcMenu non supera la prova con Orca;
- ArcMenu esce da Debian testing o non segue una nuova versione di GNOME;
- Vabax, ascoltando, trova il menu scomodo.
