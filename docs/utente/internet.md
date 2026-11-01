# Internet con Orca

Il browser di VabaxOS è **Firefox**, in italiano. VabaxOS lo prepara per chi usa il lettore di schermo:

- **l'accessibilità è sempre accesa**, anche se Firefox parte prima di Orca (un difetto noto di Firefox: altrimenti Orca non legge niente finché non si riavvia Firefox);
- **niente pagine di benvenuto**, consigli e novità che si aprono da soli alla prima apertura e dopo gli aggiornamenti;
- **l'audio non parte da solo:** i video con il suono aspettano che tu li avvii, così non coprono la voce di Orca;
- niente richiesta di diventare il browser predefinito, niente invio di dati a Mozilla.

Thunderbird, la posta, ha la stessa accessibilità sempre accesa.

## I tasti di Orca nelle pagine web

- **Ins+Spazio:** passa dalla modalità navigazione (le frecce leggono la pagina) alla modalità focus (le frecce lavorano nei campi), come in NVDA.
- **H** e **Maiusc+H:** titolo successivo e precedente; **1-6** i livelli dei titoli.
- **K:** collegamento successivo; **F:** campo successivo; **T:** tabella successiva; **L:** elenco successivo; **B:** pulsante successivo.
- **Ins+F7:** l'elenco dei collegamenti; **Ins+F6:** dei titoli; **Ins+F5:** dei campi.
- **Ins+Freccia giù:** leggi tutto.

Gli altri tasti sono nella guida [I tasti di Orca](tasti-orca.md).

## Se Orca legge solo le etichette

Con GNOME 50 ci sono state segnalazioni di Orca che, in Firefox e nei programmi fatti con Electron, legge solo i nomi dei comandi e non il testo delle pagine. VabaxOS accende l'accessibilità di Firefox e dei programmi Electron fin dall'avvio, e la prova automatica di VabaxOS controlla che il testo delle pagine si legga. Se capita lo stesso: chiudi Firefox con **Ctrl+Q** e riaprilo.
