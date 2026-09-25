# Analisi dell'installer (2026-09-25)

Richiesta di Vabax: analizzare tutto l'installer attuale e trovare soluzioni utili, tenendo presente che Ubuntu 26.04 ha le impostazioni di accessibilità già nell'installer. Questo documento descrive com'è l'installer, dove sono le barriere, cosa fa Ubuntu, cosa è stato fatto e cosa resta da proporre.

## Com'è fatto oggi

- **L'installer è quello di Debian** ([ADR-0007](../decisions/0007-installer.md)), in modalità «live»: copia sul disco il sistema della chiavetta, poi toglie i pacchetti che servono solo alla versione live. I pacchetti VabaxOS arrivano quindi nel sistema installato insieme a tutto il resto.
- **Voci del menu di avvio:** I, installer con la voce (Speakup ed espeakup leggono l'installer testuale); O poi K, installer grafico ad alto contrasto; O poi G, grafico; O poi T, testuale senza voce. L cambia la lingua anche per l'installer.
- **Risposte automatiche:** nessuna per le installazioni vere. C'era solo il file per le prove automatiche (`vabaxos-test.cfg`).
- **Firmware non libero:** sulla ISO ci sono 96 file in `/firmware` (Wi-Fi, audio, microcodice). Il criterio della v0.1 sull'installer con il firmware è soddisfatto.
- **Italiano:** i testi dell'installer sono tradotti (25 componenti su 27 nell'initrd grafico hanno l'italiano). Nota: sulla console seriale l'installer mostra solo le lingue in caratteri semplici, cioè C e English: non è un difetto della ISO.
- **Voce nel sistema installato:** l'installer configura espeakup per la console; Orca è attivo per le impostazioni di `vabaxos-accessibility`.
- **Benvenuto:** «Installa VabaxOS» diceva solo di riavviare e premere I nel menu di avvio.
- **Prove:** `test-boot.sh --entry install` controlla che l'installer parli; `test-install.sh` fa un'installazione automatica, ma girava solo sulla postazione.

## Le domande dell'installer, una per una

Elenco ricavato dai componenti dell'installer presenti sulla ISO del blocco 8 e dai loro testi: 1205 modelli di domanda diversi, quasi tutti mostrati solo in casi particolari (errori, partizionamento manuale, hardware raro). Sotto ci sono quelli che una persona incontra di solito. In una macchina virtuale senza KVM l'installer è troppo lento per contarle dal vivo: circa 12 minuti fra una domanda e l'altra.

1. Lingua (non chiesta se scelta nel menu di avvio con L)
2. Paese
3. Tastiera (non chiesta se scelta con L)
4. Rete: senza cavo, il messaggio «configurazione automatica fallita» e cosa fare; con il Wi-Fi, la rete e la sua password
5. **Nome del computer in rete** (ora risposta da VabaxOS: `vabaxos`)
6. **Dominio** (ora risposto da VabaxOS: nessuno)
7. **Password di root** (ora non chiesta: niente root, chi installa è amministratore)
8. **Password di root, di nuovo** (ora non chiesta)
9. Nome completo
10. Nome utente
11. Password
12. Password, di nuovo
13. Fuso orario, se il paese ne ha più di uno
14. Partizionamento: metodo (disco intero, con LVM, cifrato, manuale)
15. Quale disco
16. Schema (tutto in una partizione, ...)
17. Fine del partizionamento
18. Conferma prima di scrivere sul disco
19. **Altri dischi di installazione da cercare** (ora non chiesto)
20. Usare un mirror di rete? (resta: ha una risposta vera, e senza rete vale già «no»)
21. **Paese del mirror** (ora risposto: server principale di Debian)
22. **Mirror** (ora risposto)
23. **Proxy** (ora risposto: nessuno)
24. Dove installare GRUB, solo con il BIOS e più dischi
25. Installazione completata

Ogni risposta automatica di VabaxOS è stata confrontata con i testi dell'installer della ISO: tutte corrispondono a domande che esistono.

## Barriere trovate

1. **Le scelte del benvenuto si perdono.** Velocità della voce, testo grande, alto contrasto, zoom e tasti permanenti valgono solo per la sessione live.
2. **Il menu di avvio va ritrovato**, con i due bip, e per l'italiano bisogna premere di nuovo L e poi I.
3. **Domande tecniche** che una persona non dovrebbe dover capire: nome del computer, dominio, mirror, proxy.
4. **Due password** da inventare e ricordare (root e utente), otto campi da compilare invece di quattro.
5. **L'installer parla alla velocità predefinita**, anche se nel benvenuto la voce era più veloce.
6. **Al primo avvio il benvenuto chiede di nuovo la lingua**, in inglese.
7. **L'alto contrasto dell'installer (K) non arriva nel sistema installato.**
8. **Nessuna prova automatica dell'installazione nella CI.**

## Cosa fa Ubuntu 26.04

- L'installer di Ubuntu (`ubuntu-desktop-provision`, in Flutter) comincia con: **lingua**, poi **accessibilità** (vista, udito, digitazione, puntamento e clic, zoom), poi **prova o installa**. Le impostazioni valgono subito.
- Chiede solo un utente, che è amministratore: niente password di root.
- Le note di rilascio della 26.04 parlano di molte correzioni per chi usa un lettore di schermo nell'installer, ma dicono anche che il supporto del lettore di schermo nell'installer è ancora incompleto, con diverse segnalazioni aperte.

Cosa prendiamo da Ubuntu: scegliere lingua e accessibilità una volta sola, all'inizio; niente password di root; niente domande tecniche. Cosa non prendiamo per ora: un installer grafico nuovo. È la decisione della v0.5 (ADR-0007), e l'installer di Debian con la voce funziona già.

## Soluzioni fatte

1. **Risposte automatiche sicure** (`image/config/includes.installer/preseed.cfg`): dentro l'installer, valgono per ogni voce del menu di avvio. Tolgono le domande 5, 6, 7, 8, 19, 21, 22, 23. Non toccano mai le domande su di te e sul disco.
2. **Installare dal benvenuto** ([ADR-0023](../decisions/0023-installare-dal-benvenuto.md), proposta): «Installa VabaxOS», poi «Installa ora», fa ripartire il computer direttamente nell'installer con la voce (`vabaxos-install`, con kexec), senza firmware e senza menu di avvio. L'installer riceve la lingua, la tastiera e la velocità della voce del benvenuto (`speakup_soft.rate`). Se il computer non riesce a ripartire così, il benvenuto spiega il menu di avvio come prima.
3. **Le scelte arrivano nel sistema installato:** l'installer salva in `/var/lib/vabaxos/installer-choices` accessibilità, velocità della voce e lingua; con K anche l'alto contrasto. Al primo avvio il benvenuto parte da lì: nella lingua giusta, alla velocità giusta, con le impostazioni già attive.
4. **Prove:** `test-install.sh` passa all'installer le scelte di accessibilità e controlla che arrivino nel sistema installato; la CI ora esegue `test-install.sh` e `test-boot.sh --entry welcome-install`, anche con Secure Boot.

## Proposte per dopo

- **«Installa VabaxOS» nel menu Start della sessione live**, come l'icona di Ubuntu: una finestra di conferma accessibile, poi `vabaxos-install`.
- **Braille nell'installer:** l'installer di Debian riconosce da solo i display Braille USB (brltty). Va provato con un display vero; se serve, una voce del menu di avvio con i parametri di brltty.
- **Wi-Fi scelto una volta sola:** la rete scelta nella sessione live potrebbe passare all'installer. La password però non deve finire sulla riga di avvio, che tutti i programmi possono leggere: serve un altro modo.
- **Cifratura del disco** ([ADR-0021](../decisions/0021-firewall-e-cifratura.md), proposta): le domande di cifratura dell'installer vanno provate con la voce.
- **Contare le domande nella CI:** l'installer testuale sulla console seriale, con KVM, per accorgersi subito se una nuova versione di Debian aggiunge domande.
- **Riepilogo parlato prima di scrivere il disco**, come la pagina «Conferma» di Ubuntu: l'installer di Debian elenca già le modifiche, ma va ascoltato con Vabax.

## Fonti

- [ubuntu-desktop-provision, pagine dell'installer](https://github.com/canonical/ubuntu-desktop-provision/blob/main/README.md)
- [Ubuntu 24.04: opzioni di accessibilità nell'installer (Phoronix)](https://www.phoronix.com/news/Ubuntu-24.04-Installer-Access)
- [Note di rilascio di Ubuntu 26.04](https://documentation.ubuntu.com/release-notes/26.04/summary-for-lts-users/)
- [Debian: preconfigurazione dell'installer, opzioni avanzate](https://www.debian.org/releases/forky/arm64/apbs05.en.html)
