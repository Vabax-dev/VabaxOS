# VabaxOS — Hardware Compatibility Specification

| Campo | Valore |
|---|---|
| ID | VABAX-DOC-11 |
| Versione | 0.1.0 |
| Stato | Bozza — nessuna compatibilità hardware certificata |
| Data | 2026-09-23 |
| Dipendenze | DOC-01 roadmap, DOC-03 architettura, DOC-04 requisiti, DOC-07 QA |

## 1. Scopo

Definire livelli di supporto, raccolta delle prove e pubblicazione della matrice hardware. “Supporto x86/x86-64” nella roadmap è un obiettivo architetturale, non una garanzia per ogni PC. v0.1 è x86-64 UEFI con VM e almeno un PC fisico; la serie 2.x prepara ARM64, Chromebook e Mac con profili dedicati.

## 2. Livelli di compatibilità

- **Tier A — verificato per release:** test completo del boot, tastiera, display, audio/TTS/AT, rete e recovery secondo suite; modello esatto e firmware documentati.
- **Tier B — avvio e uso base:** boot e flussi essenziali passati, ma alcune periferiche o accelerazioni non verificate.
- **Tier C — segnalato:** report utente o upstream, non validato dal progetto.
- **Non supportato/ignoto:** blocco noto oppure nessuna evidenza. Non equivale a incompatibilità.

Non usare il termine “certificato” finché non esistono test di conformità, criteri pubblici e governance per il marchio.

## 3. Inventario minimo

Per ogni host registrare vendor/modello/revisione; CPU/ISA; firmware versione e modalità UEFI/CSM; Secure Boot; RAM; storage/controller; GPU e driver; display/docking; NIC/Wi-Fi/Bluetooth; audio input/output; USB/HID; touchpad/touchscreen; webcam; stampante/scanner; dispositivi Braille; kernel/firmware userspace, immagine e test run. Rimuovere seriali e dati personali da report condivisi.

## 4. Matrice per componenti

| Area | Verifica v0.1 | Aspetti da ampliare |
|---|---|---|
| CPU/platform | x86-64 boot UEFI e virtualizzazione | Intel/AMD generazioni, power states |
| Boot/firmware | UEFI su QEMU + PC campione | Secure Boot, CSM, firmware OEM |
| GPU/display | framebuffer/KMS e desktop | Intel/AMD/NVIDIA, multi-monitor, scaling |
| Input | tastiera USB, focus e shortcut | layout, touchpad, touch, access switch |
| Audio/AT | output, TTS offline, screen reader | microfoni, jack, HDMI, USB, Braille |
| Network | Ethernet/Wi-Fi per setup | chipset, WPA, VPN, Bluetooth PAN |
| Storage | live boot e installazione VM | NVMe/SATA, RAID, suspend/resume |
| Periferiche | USB essenziali | webcam, dock, stampa, scanner |

Modelli GPU, chipset e periferiche target vanno scelti sulla base dei PC realmente disponibili e dei dati kernel/upstream; non si promette compatibilità universale.

## 5. Protocollo di test

Test immagine in QEMU prima di hardware; poi sessione live senza scrittura intenzionale; registrare log diagnostici; testare boot/reboot, rete, audio parlante, tastiera/AT, aggiornamento e recovery se implementati. Ogni issue hardware include identificativi PCI/USB utili, versione firmware/driver, passi, esito, log minimizzati e regressione. Verificare che funzioni critiche restino accessibili quando una periferica manca.

## 6. Hardware Compatibility Database (proposta)

Un database/versionato può contenere hardware ID, modello marketing, kernel/firmware testati, feature, esito, report e confidenza. Schema, privacy, contributi utenti, validazione e aggiornamento automatico sono TBD. La pagina utente deve essere consultabile da screen reader e mostrare data e versione VabaxOS del risultato.

## 7. Criteri di accettazione

Per v0.1: una configurazione QEMU riproducibile e almeno un PC fisico compatibile documentato, entrambi con boot UEFI e flusso boot → voce → configurazione → desktop. Pubblicare limiti e componenti non testati. Per ogni release successiva, la matrice deve avere owner e revisione con nuova immagine/kernel.

## 8. Decisioni aperte

Elenco macchine campione; policy Wi-Fi/GPU NVIDIA; criteri Tier A/B; raccolta telemetria; compatibilità Secure Boot; supporto PC Apple/Chromebook in 2.x; gestione submissions; dichiarazioni marketing richiedono approvazione.

## Riferimenti

- [Linux kernel hardware/driver documentation](https://docs.kernel.org/)
- [Linux x86 documentation](https://docs.kernel.org/arch/x86/)
- [Linux ARM64 documentation](https://docs.kernel.org/arch/arm64/)
- [Linux firmware documentation](https://docs.kernel.org/driver-api/firmware/)
- [QEMU documentation](https://www.qemu.org/docs/master/)

## Cronologia

- 0.1.0 — 2026-09-23: prima matrice e schema.
