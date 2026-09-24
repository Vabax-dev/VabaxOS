# VabaxOS — Architecture Specification

| Campo | Valore |
|---|---|
| ID | VABAX-DOC-03 |
| Versione documento | 0.1.0 |
| Stato | Bozza tecnica — proposta, non approvata |
| Data | 2026-09-23 |
| Ambito | Architettura logica del sistema e criteri per le decisioni successive |
| Dipendenze documentali | Roadmap VabaxOS v0.1–v1.0 (antecedente, non disponibile in questo workspace); Windows Development Environment (antecedente, non disponibile in questo workspace); documenti 04–07 |

## 1. Scopo

Definire un modello architetturale verificabile per VabaxOS, una distribuzione Linux orientata all'accessibilità, all'uso quotidiano, alla compatibilità con applicazioni Linux e, nelle fasi successive, al gaming. Il documento stabilisce confini e requisiti; non dichiara già scelti componenti che richiedono prototipi, ricerca di compatibilità o approvazione del progetto.

La roadmap originale documenta Linux, systemd, Wayland, AT-SPI2, accessibilità, desktop Vabax, applicazioni, localizzazione, input, audio, installer, aggiornamenti e gaming. Distingue le scelte preliminari dalle decisioni ancora da prendere prima della v0.1; questo documento mantiene tale distinzione.

## 2. Stato delle decisioni

**Indirizzi preliminari già presenti nella roadmap (non ancora ADR approvati):** Linux come kernel; systemd come init; Wayland con XWayland per compatibilità X11; AT-SPI2; PipeWire + WirePlumber; NetworkManager; x86-64 come target v1.0 e v0.1; ISO Live UEFI; audio/TTS offline. La roadmap nomina anche systemd-boot con GRUB da valutare, ext4 iniziale, pacchetti nativi + Flatpak e Calamares oppure installer dedicato, ma questi restano proposte da verificare. La v0.1 deve dimostrare boot → configurazione accessibile → desktop, prima in VM e poi su almeno un PC fisico. Questi indirizzi non sostituiscono gli ADR previsti dalla roadmap.

**Da decidere con ADR prima della v0.1, come richiesto dalla roadmap:** desktop iniziale (GNOME personalizzato o Wayland minimale); base userspace (Debian/Ubuntu-like o indipendente); build system (live-build o pipeline Vabax); installer (Calamares personalizzato o dedicato); strategia screen reader (Orca personalizzato/fork o Vabax Screen Reader); TTS (eSpeak NG fallback e motore neurale locale opzionale da valutare); packaging; filesystem; boot manager (systemd-boot/GRUB); toolkit e composizione GNOME/GTK, KDE/Qt o Vabax. Confermare inoltre versione/release base, display manager e stack Braille, componenti gaming e relative licenze. systemd, Wayland/XWayland, AT-SPI2, PipeWire/WirePlumber e NetworkManager sono indirizzi preliminari della roadmap, soggetti comunque a compatibilità e ADR.

## 3. Principi architetturali

1. **Accessibilità end-to-end:** ogni funzione critica deve essere raggiungibile da tastiera e percepibile tramite AT supportate, anche in avvio, login, recupero ed errore.
2. **Standard prima delle estensioni proprietarie:** riutilizzare protocolli, API e componenti upstream quando adeguati; le estensioni Vabax devono avere interfacce documentate.
3. **Degrado controllato:** guasti di rete, audio, TTS o un'applicazione non devono rendere irraggiungibile l'intero sistema; fornire canale alternativo quando tecnicamente possibile.
4. **Confini chiari:** kernel/driver, servizi di sistema, sessione utente, shell, AT, applicazioni e strumenti di build hanno responsabilità distinguibili.
5. **Osservabilità e recuperabilità:** eventi di boot, servizi e aggiornamento devono essere diagnosticabili e recuperabili con tastiera e output accessibile.
6. **Portabilità e manutenzione:** non introdurre fork upstream senza necessità dimostrata; registrare versioni, patch, origine e licenze.
7. **Decisioni reversibili finché possibile:** tenere le scelte provvisorie configurabili e provare più alternative prima del congelamento.

## 4. Modello a strati

```text
Firmware UEFI/BIOS e hardware
  └─ Bootloader / immagine avviabile [da selezionare]
     └─ Kernel Linux + driver + firmware [release/base da selezionare]
        └─ Init, device, log, rete, sessioni [systemd proposto; ADR da completare]
           └─ Audio, input, display server/compositor [da selezionare]
              ├─ Bus e API di accessibilità (AT-SPI2 proposto; validazione necessaria)
              ├─ Servizi Vabax: profili, TTS, screen reader integration, Braille,
              │  suoni, scorciatoie, diagnostica, localizzazione [confini/API da definire]
              └─ Sessione desktop Vabax e applicazioni
                 ├─ impostazioni, finestre, file, terminale, browser, software center
                 └─ gaming/compatibilità (fasi successive; opt-in e profilati)
Build riproducibile → repository di pacchetti/immagine → aggiornamento/rollback
```

Le frecce indicano dipendenza logica, non un vincolo su un singolo prodotto. Il compositor e il protocollo grafico devono esporre gli eventi e le relazioni necessari alle AT e supportare fallback per applicazioni legacy. Wayland/XWayland sono proposti dalla roadmap; adeguatezza per login, accesso remoto e AT va prototipata prima dell'ADR finale.

## 5. Componenti e requisiti d'interfaccia

| Area | Responsabilità | Dipendenze / interfacce | Stato |
|---|---|---|---|
| Boot e sistema base | Avvio, driver, processi, storage, rete, logging | Firmware, kernel, systemd proposto; bootloader da ADR | Da decidere |
| Sessione grafica | Output, input, finestre, focus, clipboard, workspace | Protocollo display/compositor; input device | Wayland/XWayland indirizzo preliminare; compositor/desktop da ADR |
| Accessibility bus | Albero accessibile, ruoli, proprietà, eventi | Toolkit, compositor/servizi, AT | AT-SPI2 indirizzo preliminare; copertura Wayland da validare |
| Accessibility broker | Avvio/controllo AT, preferenze, recovery, profili | Sessione, bus AT, audio e input | API e ownership da definire |
| Speech e Braille | Sintesi e uscita Braille, lingua e voce selezionabili | Motori, driver e dispositivi | eSpeak NG fallback + TTS neurale locale opzionale sono proposti; verifica/licenze necessarie |
| Desktop Vabax | Navigazione e impostazioni coerenti e accessibili | Sessione grafica e servizi | Shell/compositor non selezionati |
| Localizzazione | Lingua interfaccia, AT/voce, locale e tastiera indipendenti | gettext o altra tecnologia da valutare | requisiti funzionali nel DOC-04/05 |
| Software e compatibilità | Pacchetti nativi e, se approvati, formati portabili/compat layer | Repository, sandbox, dipendenze ABI | politiche aperte |
| Gaming | Rilevamento profili, runtime, controller, performance, AT | GPU, driver, Vulkan, Steam/Proton/Gamescope candidati | fuori dal prototipo minimo |
| Build, release e update | Creazione immagine, provenienza, firma, aggiornamento, rollback | Base, repository, chiavi e pipeline | build framework da selezionare |

## 6. Flussi critici

### Avvio accessibile

Firmware → bootloader → kernel → sistema base → schermata di scelta/avvio sessione → caricamento AT e TTS → sessione desktop. Il progetto deve stabilire in quale fase parte la sintesi, come selezionare lingua/uscita senza vista e che cosa accade se l'AT primaria fallisce. Non si presume che ogni firmware o bootloader possa parlare: definire un percorso accessibile dal primo ambiente controllato da VabaxOS.

### Input e focus

Dispositivo → stack input → compositor/sessione → widget/applicazione → evento AT → screen reader/utente. I cambi di focus, finestra, dialogo, notifica e layout tastiera devono mantenere semantica e ordine coerenti. Evitare che l'AT consumi globalmente tasti necessari alle applicazioni senza impostazione esplicita.

### Build e aggiornamento

Sorgenti e manifest versionati → build isolata e registrata → immagine/pacchetti → verifica firma/integrità → installazione → verifica salute → conferma o rollback. La strategia precisa dipende dal sistema base e resta aperta.

## 7. Sicurezza e confini di fiducia

- Separare privilegi di sistema, sessione e applicazioni; usare i meccanismi di controllo accessi disponibili nella base scelta.
- Le AT possono richiedere accesso ampio all'interfaccia: documentare il confine di fiducia, ridurre privilegi non necessari e rendere trasparente l'accesso remoto/diagnostico.
- Firmware, repository, chiavi di firma, toolchain e artefatti devono avere provenienza registrata.
- Le integrazioni di gaming/compatibilità non devono applicare modifiche di performance o disabilitare AT senza consenso, stato visibile e ripristino.
- Definire minacce, aggiornamenti di sicurezza, gestione vulnerabilità e threat model in ADR e documenti successivi.

## 8. Criteri di accettazione del documento e gate architetturali

Il DOC-03 è accettabile quando ogni componente ha proprietario, interfacce, dipendenze e stato decisionale; ogni scelta irreversibile ha un ADR con alternative e prove; i prototipi validano in VM il boot, il focus, l'avvio AT e la diagnostica accessibile; una build documentata produce un'immagine avviabile. Nessun gate equivale ad approvazione fino a revisione del responsabile di architettura.

**Gate A — bootstrap:** kernel/base, bootloader, target iniziale e toolchain fissati per prototipo.
**Gate B — esperienza accessibile:** dimostrazione avvio → TTS/AT → login/sessione → navigazione tastiera.
**Gate C — release foundation:** aggiornamento verificabile, rollback o recovery documentato, inventario licenze e test ripetibili.

## 9. Riferimenti ufficiali

- [Documentazione Linux kernel](https://docs.kernel.org/) — kernel, driver, build e testing.
- [systemd](https://systemd.io/) — documentazione ufficiale; menzionato come candidato, non come scelta.
- [Wayland: Protocol and Model of Operation](https://wayland.freedesktop.org/docs/book/Protocol.html) — modello del protocollo.
- [AT-SPI2 development guide](https://gnome.pages.gitlab.gnome.org/at-spi2-core/devel-docs/index.html) e [API AT-SPI](https://docs.gtk.org/atspi2/) — infrastruttura/API di accessibilità.
- [GTK 4 Accessibility](https://docs.gtk.org/gtk4/section-accessibility.html) — esempio di supporto toolkit per AT.
- [Debian Live project](https://www.debian.org/devel/debian-live/) — candidato di riferimento per immagini live, non decisione di base.

## 9A. Allineamento ai documenti sorgente disponibili

Sono stati consultati `VabaxOS_Roadmap_v0.1-v1.0.txt` (bozza tecnica v0.1, 23 settembre 2026) e `VabaxOS_Windows_Development_Environment.txt` (versione 1.0, 23 settembre 2026). La roadmap distingue indirizzi preliminari dalle dieci decisioni da prendere prima della v0.1. La guida workstation fissa Windows 11 + WSL2 + Ubuntu 24.04 LTS, repository e build Linux in WSL, VS Code Remote WSL e QEMU come laboratorio; queste sono scelte dell'ambiente di sviluppo, non della base runtime VabaxOS.

Correzione rispetto alla bozza iniziale: systemd e i componenti citati non sono scelte completamente ignote; sono proposte preliminari esplicite. La base Linux e il sistema di build restano invece realmente indecisi. La v0.1 richiede inoltre un test su almeno un PC fisico oltre alla VM.

## 10. Cronologia

- 0.1.0 (2026-09-23): prima bozza; architettura a strati e decisioni aperte.
