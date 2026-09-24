# VabaxOS — Gaming Specification

| Campo | Valore |
|---|---|
| ID | VABAX-DOC-18 |
| Versione | 0.1.0 |
| Stato | Bozza di visione tecnica — nessun supporto gioco garantito |
| Data | 2026-09-23 |
| Dipendenze | DOC-03, DOC-05, DOC-09, DOC-10, DOC-11, DOC-13, DOC-17 |

## 1. Obiettivo

La roadmap include ottimizzazione di giochi Linux e compatibilità con giochi Windows compatibili con Proton. Gaming è obiettivo evolutivo, non requisito del prototipo v0.1. VabaxOS deve riusare progetti upstream e pubblicare risultati per gioco/driver/versione; nessuna promessa “tutti i giochi funzionano”.

## 2. Stack candidato

Kernel/driver → Vulkan/OpenGL/Mesa o driver vendor → Wayland → runtime Steam → native Linux oppure Proton/Wine → eventuale Gamescope → game profile/diagnostica. Proton e Gamescope sono progetti Valve candidati; Mesa fornisce implementazioni API grafiche/driver. Disponibilità, licenze e requisiti variano per GPU e gioco.

## 3. Requisiti prodotto

- Installare strumenti gaming opzionalmente/on-demand per mantenere leggera la base.
- Per ogni gioco mostrare stato “testato”, versione Proton/runtime, GPU/driver e data del test.
- Profilo per gioco può scegliere risoluzione, limiter, scaler, controller, modalità energia; nessuna ottimizzazione che disabiliti sicurezza o AT senza consenso.
- Profili e overlay devono poter essere navigati e configurati da tastiera/AT quando tecnicamente possibile.
- Crash, anti-cheat, DRM e problemi online sono comunicati con limiti chiari; non aggirare controlli di terzi.
- Supportare controller/gamepad e rimappatura dove lo stack lo consente; accessibilità dei singoli giochi resta responsabilità/compatibilità specifica.
- Evitare tuning globale automatizzato senza consenso, benchmark e ripristino.

## 4. Accessibility Gaming Layer

Visione esplorativa: overlay o strumenti che leggano testo esposto dal gioco, annuncino menu/eventi e offrano OCR solo dopo revisione. Giochi spesso non espongono al sistema la semantica UI; OCR/AI non garantiscono comprensione o input legale. Raccogliere solo dati locali per default, evitare cattura/upload schermo senza consenso e testare latenza. Primo gate: investigare APIs/telemetria dei giochi e prototipo non invasivo.

## 5. Test e compatibilità

Matrice include titolo/versione/store, native o Proton version, runtime, GPU/driver, compositor, risoluzione, controller, anti-cheat, avvio/uscita, crash, prestazioni e funzioni AT. Benchmark ripetuti con configurazione fissa; dichiarare mediane e variabilità, non solo numeri migliori. VM non è sufficiente per prestazioni GPU.

## 6. Gate di sviluppo

Prima compatibilità applicazioni generale; poi test Vulkan/driver; poi un set limitato di giochi nativi; quindi Proton e gestione librerie; solo dopo profiles/performance layer; infine accessibility overlay se prove dimostrano fattibilità. No gaming services nella v0.1.

## 7. Decisioni aperte

Steam inclusion/redistribution; Proton source vs client-managed; Gamescope scope; Mesa/vendor policy; GameMode/MangoHud; anti-cheat; controller UI; OCR/privacy; hardware tier; support matrix; licensing of redistributable assets.

## Riferimenti upstream

- [Valve Proton](https://github.com/ValveSoftware/Proton)
- [Valve Gamescope](https://github.com/ValveSoftware/gamescope)
- [Steamworks Proton documentation](https://partner.steamgames.com/doc/steamhardware/proton)
- [Mesa documentation](https://docs.mesa3d.org/)
- [Steam Runtime](https://github.com/ValveSoftware/steam-runtime)

## Cronologia

- 0.1.0 — 2026-09-23: definizione iniziale; nessun tier gaming approvato.
