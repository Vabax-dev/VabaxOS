# Il desktop di VabaxOS

## Tasti utili

- **Super**: apre il [menu Start](menu-start.md).
- **Super+Alt+I**: dice lo stato del computer: ora e data, batteria, rete Wi-Fi o cavo, Bluetooth, volume. È una notifica, quindi Orca la legge dovunque sia il cursore. Da terminale: `vabaxos-status`, oppure `vabaxos-status battery` per la sola batteria.
- **Super+Alt+S**: accende e spegne Orca.
- **Super+Alt+8**: accende e spegne lo zoom.
- **Super+A**: la panoramica di GNOME con tutti i programmi.

## Come appare

Per chi vede poco, VabaxOS usa ovunque lo stesso aspetto:

- il font **Atkinson Hyperlegible Next**, disegnato per chi vede poco: lettere facili da distinguere, come I, l e 1;
- il viola del logo come colore dei pulsanti e delle selezioni;
- la percentuale della batteria sempre visibile nella barra in alto;
- il logo nella schermata di accesso e nel menu Start.

Tutto si cambia nelle Impostazioni e nella [configurazione iniziale](configurazione.md): contrasto, dimensione del testo, zoom.

## I suoni

Il tema dei suoni **VabaxOS** ha il timbro dei suoni di Ubuntu, perché ricordano un sistema vero, con melodie di VabaxOS (scelta di Vabax, 2026-09-25). Ogni nota è un colpo del suono «campanello» di Ubuntu, trasposto. Le melodie usano le due note dei bip del menu di avvio: **salgono** quando qualcosa inizia o arriva (accesso, dispositivo collegato, rete collegata), **scendono** quando qualcosa finisce o se ne va (uscita, dispositivo scollegato, rete persa). Così si capisce l'evento senza vedere lo schermo. Avvio e spegnimento sono frasi più lunghe e melodiche. Il suono della cattura dello schermo è quello del tema freedesktop.

Ci sono anche tre temi alternativi: **Cristallo** (campane), **Morbido** (percussioni morbide) e **Aria** (suoni dolci e lunghi). Il tema si sceglie in Impostazioni, Suono, oppure da terminale:

```bash
gsettings set org.gnome.desktop.sound theme-name vabaxos-morbido
```

Crediti: il timbro è di Mads Rosendahl (tema Yaru di Ubuntu, CC BY-SA 4.0); la cattura dello schermo è di horsthorstensen su freesound (CC BY-SA).

## Energia, Wi-Fi e Bluetooth

- La batteria si sente con Super+Alt+I. Quando è quasi scarica, GNOME avvisa con una notifica e con il suono «batteria scarica», e passa da solo al risparmio energetico.
- Wi-Fi e Bluetooth si gestiscono nelle Impostazioni (Wi-Fi, Bluetooth), che si aprono dal menu Start. Da terminale, per il Wi-Fi: `nmtui`, letto da Orca.
- Le cuffie e gli altoparlanti Bluetooth funzionano come quelli con il cavo: il suono, e quindi la voce, passa a loro quando si collegano.
- Nel sistema live la sospensione automatica è spenta: la voce deve restare sempre disponibile.
