# Il Braille

VabaxOS scrive sul display Braille quello che il lettore di schermo legge. Il display lo gestisce BRLTTY, e il lettore di schermo (Orca) ci scrive attraverso BrlAPI.

## Collegare il display

- **Con il cavo USB:** collegalo e accendilo. VabaxOS lo riconosce da solo.
- **Con il Bluetooth:** prima associalo: Super+I, Impostazioni, pagina **Bluetooth**, scegli il display e conferma il codice se lo chiede. Poi accendilo.

## È pronto?

Apri il Terminale e scrivi:

```bash
vabaxos-braille-check
```

VabaxOS dice, una cosa alla volta, se BRLTTY è attivo, se c'è la chiave di BrlAPI, se sei nel gruppo `brlapi`, se il display è collegato e quante celle ha, se il Braille è acceso nel lettore di schermo.

Se qualcosa non va:

```bash
vabaxos-braille-check --fix
```

Accende il Braille nel lettore di schermo, ti aggiunge al gruppo `brlapi` (chiede la password di amministratore; poi bisogna uscire e rientrare) e riavvia BRLTTY.

## Le impostazioni

Le impostazioni del Braille (tabella, abbreviato o integrale, cursore, barre di avanzamento) sono nella pagina **Braille** delle impostazioni del lettore di schermo (Super+Alt+O).
