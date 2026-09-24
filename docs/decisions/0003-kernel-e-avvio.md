# ADR-0003: Kernel e avvio — kernel Debian firmato, GRUB con Secure Boot

- **Stato:** Accettata
- **Data:** 2026-09-24
- **Responsabile:** Vabax (Project Lead)

## Contesto

La roadmap propone systemd-boot come prima scelta e GRUB come alternativa (DOC-01 §26, punto 9), UEFI come standard e il BIOS «dove possibile». DOC-02 prevede di compilare il kernel dentro il progetto. Molti PC moderni hanno Secure Boot attivo: una ISO che non si avvia con Secure Boot costringe l'utente a entrare nel firmware, e i menu del firmware non parlano mai. Per una persona cieca sono un muro.

## Decisione

- **Kernel:** il kernel Linux di Debian (`linux-image-amd64`), firmato da Debian. VabaxOS non compila un proprio kernel.
- **Avvio:** **GRUB** con la catena firmata di Debian (shim firmato Microsoft → GRUB firmato → kernel firmato), quindi **Secure Boot funziona senza chiavi nostre**. Il BIOS legacy è supportato dalla ISO ibrida di live-build.
- **Init:** systemd, come in Debian.
- **Segnale acustico:** il menu di avvio della ISO emette un suono quando è pronto (comando `play` di GRUB), come fa l'installer Debian. Chi non vede sa quando può premere un tasto.

## Alternative considerate

- **systemd-boot:** più semplice, ma solo UEFI (niente BIOS) e fuori dalla catena shim/GRUB che Debian usa per le ISO. Con Secure Boot servirebbero chiavi e firme nostre, da custodire.
- **Kernel compilato dal progetto:** nessun beneficio per la v0.x, più il costo di seguire da soli tutte le correzioni di sicurezza e di perdere la firma per Secure Boot.

## Motivazione

L'utente deve poter infilare la chiavetta e avviare, senza toccare il firmware. La catena firmata di Debian lo permette oggi e con zero infrastruttura di firma nostra. Il kernel Debian riceve gli aggiornamenti di sicurezza dal team di sicurezza Debian.

## Conseguenze

- Le patch al kernel sono vietate senza un ADR. Se serve un driver più recente si usa il kernel di `trixie-backports`, sempre firmato.
- Moduli esterni (per esempio driver NVIDIA proprietari) con Secure Boot richiedono la registrazione di una chiave MOK: è un passaggio da rendere accessibile e va trattato nella v0.6 (hardware).
- Ogni build registra la versione esatta del kernel nel manifest (DOC-02 §17).

## Riesame

Se Debian firma systemd-boot per le immagini live, oppure se VabaxOS passa a immagini unificate (UKI) con aggiornamenti atomici.
