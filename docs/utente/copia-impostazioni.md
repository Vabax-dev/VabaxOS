# Copia delle impostazioni

La **Copia delle impostazioni** salva il tuo VabaxOS in un file: quando cambi computer, o dopo una nuova installazione, lo rimetti e ritrovi tutto come prima. La trovi nel menu Start, in Sistema, oppure cercando «copia».

## Cosa va nella copia

Scegli con gli interruttori:

- **Voce e lettore di schermo:** tutte le impostazioni di Orca (profili, tasti, impostazioni per programma, pronunce) e della voce;
- **Impostazioni e tasti del desktop:** le impostazioni di GNOME, compresi i tasti e l'accessibilità. Restano fuori quelle che valgono solo per questo computer, come la grandezza delle finestre;
- **Reti Wi-Fi, con le password:** le reti salvate. Tieni il file in un posto sicuro: chi lo ha può leggere le password;
- **Programmi che hai installato:** i programmi presi da Software, da Programmi di VabaxOS o con `apt`. Quando rimetti la copia, VabaxOS li installa di nuovo; serve Internet e la password di amministratore.

La stessa scelta vale quando rimetti una copia: per esempio puoi rimettere solo la voce.

## Salvare e rimettere

- **Salva una copia...** chiede dove salvare il file. Per esempio su una chiavetta.
- **Rimetti una copia...** chiede il file, dice di quale giorno è e cosa sostituisce, e aspetta la tua conferma. Orca riparte con le impostazioni della copia.

## Copie automatiche

Ogni giorno VabaxOS salva da solo una copia di voce, desktop e programmi, senza le password del Wi-Fi, e tiene le ultime sette. Sono nella finestra, sotto **Copie automatiche**: accanto a ogni giorno c'è **Rimetti**. Servono quando una modifica non ti piace e vuoi tornare a ieri.

I file sono in `~/.local/share/vabaxos/settings-copies`.

## Nel terminale

```bash
vabaxos-settings-copy save ~/copia.json
```

Salva una copia di tutto. Con `--without-wifi` lascia fuori le reti Wi-Fi.

```bash
vabaxos-settings-copy restore ~/copia.json --only voice,desktop
```

Rimette solo le parti scelte: `voice`, `desktop`, `wifi`, `programs`.
