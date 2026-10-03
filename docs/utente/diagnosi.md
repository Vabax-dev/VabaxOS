# Diagnosi di VabaxOS

La **Diagnosi di VabaxOS** controlla le parti del computer che servono di più a chi usa il lettore di schermo, dice in una frase cosa non va e lo rimette a posto. La trovi nel menu Start, in Sistema, oppure cercando «diagnosi».

Se non senti nessuna voce, prima premi **Ctrl+Super+Invio**: rimette la voce da qualsiasi punto (vedi [Se la voce si ferma](voce.md#se-la-voce-si-ferma)).

## Cosa controlla

In quest'ordine:

1. **Scheda audio:** se il computer ne ha una;
2. **Audio:** se il server audio risponde, se è muto, se il volume è sotto il 40 per cento;
3. **Voce:** se il servizio della voce (speech-dispatcher) risponde, e con quale voce;
4. **Lettore di schermo:** se Orca è acceso, se è in esecuzione, se la sua voce è accesa;
5. **Voce della console:** se la console di testo parla;
6. **Tasto d'emergenza:** se Ctrl+Super+Invio è pronto;
7. **Rete:** se c'è Internet, o se la rete chiede di accedere, come in un albergo;
8. **Firewall:** se è attivo;
9. **Disco:** lo spazio libero, anche della cartella Home se è su un altro disco;
10. **Memoria:** la memoria libera;
11. **Aggiornamenti:** se serve un riavvio;
12. **Servizi:** i servizi fermi per un errore.

## Come si usa

Ogni controllo è una riga: il nome, poi «OK», «Attenzione» o «Problema» e una frase. Con Tab e le frecce ti muovi fra le righe e Orca le legge.

- **Correggi**, accanto a una riga, rimette a posto quella cosa. Audio, voce e Orca si correggono subito; voce della console, tasto d'emergenza e firewall chiedono la password di amministratore, in una finestra che Orca legge.
- **Correggi tutto** fa tutte le correzioni possibili.
- **Controlla di nuovo** rifà i controlli. Dopo ogni correzione i controlli si rifanno da soli.

## Nel terminale

Nel terminale o nella console di testo (Ctrl+Alt+F3):

```bash
vabaxctl doctor
```

Scrive un controllo per riga e alla fine il riassunto. Per correggere tutto quello che si può:

```bash
vabaxctl doctor --fix
```

Per i dettagli da mandare con una segnalazione: `vabaxctl report`.
