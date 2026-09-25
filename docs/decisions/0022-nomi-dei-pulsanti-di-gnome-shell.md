# ADR-0022: Nomi dei pulsanti di GNOME Shell, corretti da VabaxOS

- **Stato:** Accettata (Vabax, 2026-09-25)
- **Data:** 2026-09-25
- **Responsabile:** Vabax (Project Lead, responsabile accessibilità), Principal Software Engineer
- **Sostituisce / Sostituita da:** — (eccezione ad ADR-0010 per il linguaggio)

## Contesto

La CI del blocco 8 (PR #13) ha trovato un pulsante senza nome nella barra in alto. Non era del menu Start: era il pulsante di chiusura di una notifica.

In GNOME Shell 50.5 (`js/ui/messageList.js`) i pulsanti di ogni notifica sono disegnati con la sola icona e senza nome accessibile: Espandi, Chiudi, Comprimi (per un gruppo di notifiche) e i comandi dei programmi musicali (precedente, riproduci, successivo). Orca dice soltanto «pulsante». Anche la versione di GNOME Shell in sviluppo (ramo `main`, settembre 2026) ha lo stesso difetto.

Una correzione di GNOME arriverebbe in VabaxOS solo con una nuova versione di GNOME in Debian testing. Vabax ha deciso di correggere il difetto in VabaxOS subito (2026-09-25).

## Decisione

1. **Un'estensione di GNOME Shell di VabaxOS, `button-names@vabaxos.org`**, nel pacchetto `vabaxos-accessibility`, attiva per tutti gli utenti (elenco delle estensioni in `vabaxos-settings`).
2. L'estensione guarda tutti gli elementi di GNOME Shell, anche quelli che compaiono dopo (notifiche, menu). A ogni pulsante che non ha né un nome né un testo dentro dà un nome preso dalla sua icona: `window-close` → «Chiudi», `notification-expand` → «Espandi», `media-playback-start` → «Riproduci», e così via. Per le icone che non conosce usa il nome dell'icona in parole («view list bullet»), che dice comunque più di «pulsante».
3. **Non tocca mai un pulsante che ha già un nome**, dato da GNOME o da un'altra estensione. Se l'icona cambia (Riproduci diventa Pausa), cambia anche il nome. Quando l'estensione si spegne, toglie i nomi che ha dato.
4. I nomi sono traducibili con gettext, nel dominio `vabaxos-accessibility`.
5. **Eccezione ad ADR-0010:** l'estensione è in JavaScript, perché è l'unico linguaggio delle estensioni di GNOME Shell (come già previsto in ADR-0018, alternativa B).

## Alternative considerate

- **Segnalare il difetto a GNOME e aspettare:** giusto da fare, ma la correzione arriverebbe fra mesi, e intanto ogni notifica avrebbe pulsanti muti.
- **Modificare GNOME Shell (una patch al pacchetto Debian):** VabaxOS dovrebbe ricostruire e mantenere GNOME Shell, contro l'idea di usare i pacchetti di Debian così come sono (ADR-0008).
- **Correggere solo i pulsanti delle notifiche, uno per uno:** più semplice, ma si romperebbe al primo cambiamento del codice di GNOME e non correggerebbe gli altri pulsanti con la sola icona (per esempio quelli delle estensioni).

## Motivazione

Per chi usa Orca un pulsante senza nome è un pulsante che non si può usare. L'estensione corregge il difetto per tutto GNOME Shell con poche righe, senza cambiare il codice di GNOME, e si toglie da sola il giorno in cui GNOME darà i nomi (non tocca i pulsanti che ne hanno già uno).

## Conseguenze

- `tests/button-names/test_button_names.py` avvia GNOME Shell senza schermo e controlla, come farebbe Orca, i nomi dei pulsanti di una notifica e di alcuni pulsanti di prova, in inglese e in italiano, e che l'estensione spenta lasci tutto come prima. La CI lo esegue con GNOME 50 di Debian forky.
- `test-boot.sh` controlla che l'estensione sia attiva e che, con il menu Start aperto e una notifica sullo schermo, GNOME Shell non abbia comandi senza nome.
- A ogni nuova versione di GNOME bisogna controllare l'estensione e aggiornare `shell-version`.
- Il difetto va comunque segnalato a GNOME. Aprire la segnalazione spetta a Vabax.

## Riesame

- GNOME Shell dà un nome a questi pulsanti: allora l'estensione si può togliere;
- l'estensione dà un nome sbagliato a un pulsante (una persona lo sente leggere in modo sbagliato);
- l'estensione rallenta GNOME Shell in modo misurabile.
