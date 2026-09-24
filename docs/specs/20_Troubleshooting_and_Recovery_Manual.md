# VabaxOS — Troubleshooting & Recovery Manual

| Campo | Valore |
|---|---|
| ID | VABAX-DOC-20 |
| Versione | 0.1.0 |
| Stato | Bozza — procedure operative soggette a test per release |
| Data | 2026-09-23 |
| Dipendenze | DOC-03, DOC-05, DOC-10, DOC-11, DOC-12, DOC-16 |

## 1. Scopo e sicurezza

Manuale di diagnosi per utenti e maintainer. Le procedure devono avere edizione specifica per release: un comando di riparazione valido su una base può distruggere dati su un'altra. Mai chiedere di eseguire comandi root copiati senza spiegazione; non scrivere sull'unità sospetta prima di fare copia/immagine quando i dati sono importanti. Percorsi hardware reali e reinstallazione sono esclusi dalle procedure automatiche non confermate.

## 2. Percorso generale

1. Annotare build, hardware/firmware, sintomo, ultima modifica e riproducibilità.
2. Provare riavvio una volta solo se non vi sono segni di disco guasto/perdita dati.
3. Accedere a modalità safe/recovery prevista dalla release; fornire alternativa tastiera e voce.
4. Esportare log redatti e raccogliere ID hardware; mai includere password/chiavi.
5. Applicare solo workaround verificati per versione; registrare ogni modifica.
6. Ripristinare configurazione/rollback e controllare che AT, rete e boot siano ripresi.
7. Aprire issue con template DOC-07 se irrisolto.

## 3. Tabelle sintomi e azioni

| Sintomo | Verifica sicura | Possibile percorso | Non fare senza approvazione |
|---|---|---|---|
| ISO non parte | hash, UEFI/CSM, immagine corretta, QEMU log | provare VM nota e media verificato | scrivere bootloader su disco host |
| Schermo nero | tentare TTY/accessibilità, registrare GPU/parametri | modalità grafica fallback se prevista | rimuovere driver a caso |
| Nessuna voce | cuffie/volume/output, AT service status, log | speech fallback/riavvio AT da shortcut accessibile | inserire password nel log |
| Wi-Fi assente | device ID, blocco rfkill, firmware notice | Ethernet/USB tethering, driver documentato | installare pacchetti sconosciuti |
| Aggiornamento fallito | boot slot/stato package, spazio disponibile | usare rollback supportato e preservare dati | cancellare manualmente database package |
| Login bloccato | layout tastiera, account, TTY/recovery accessibile | recovery account owner/documentazione | rimuovere password o cifratura |
| Kernel panic | foto/testo, build, ultimo update, hardware | boot kernel precedente se implementato | ripetere su disco con scritture |

## 4. Modalità recovery — requisiti futuri

Menu testuale/audio dove possibile; network off by default; diagnostics redact; mount read-only per ispezione; recovery boot media verificata; riparazione boot config; restore backup; rollback solo se supportato; conferma prima di operazioni distruttive; uscita accessibile verso sessione normale. Implementazione e key combos sono TBD.

## 5. Log e privacy

Raccogliere versioni kernel, sessione, driver, servizi, boot events e hardware IDs essenziali. Redigere usernames, percorsi privati, SSID, indirizzi, contenuti documenti e token. Il report locale resta controllato dall'utente; l'invio remoto è opt-in, con preview e cancellazione.

## 6. Criteri di accettazione

Per ogni scenario DOC-11, scrivere passi ripetibili specifici versione, escalation, fallback AT e condizione di stop. Provare recovery su VM snapshot con successo e failure injection prima di pubblicare. Non dichiarare “recovery supported” senza test e recovery media/boot verificati.

## 7. Decisioni aperte

Recovery partition; rollback system; snapshot; rescue environment; accessibilità preboot; encryption recovery keys; support lifecycle; remote support; log retention.

## Riferimenti

- [systemd diagnosing boot problems](https://systemd.io/DIAGNOSE_BOOT/)
- [Linux kernel reporting issues](https://docs.kernel.org/admin-guide/reporting-issues.html)
- [Linux kernel fault injection/testing](https://docs.kernel.org/fault-injection/)
- [Vabax Testing & QA Plan](07_Testing_and_QA_Plan.md)

## Cronologia

- 0.1.0 — 2026-09-23: manuale iniziale; comandi specifici release da aggiungere dopo scelta base.
