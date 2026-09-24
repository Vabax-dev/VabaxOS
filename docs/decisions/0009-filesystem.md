# ADR-0009: Filesystem — ext4, LUKS2 opzionale

- **Stato:** Accettata
- **Data:** 2026-09-24
- **Responsabile:** Vabax (Project Lead)

## Contesto

La roadmap propone ext4 all'inizio e Btrfs dopo, per snapshot e rollback (DOC-01 §26, punto 8). La cifratura con LUKS2 è candidata (DOC-01 §44, DOC-10 SEC-007).

## Decisione

- **ext4** è il filesystem predefinito per le installazioni della serie 0.x e 1.0.
- **La cifratura del disco (LUKS2)** è una scelta dell'installer, disattivata per default. La richiesta della passphrase all'avvio deve essere accessibile: non si consiglia finché non è provata con la voce.
- **Btrfs con snapshot** si valuta per la v1.5, insieme agli aggiornamenti con rollback.

## Alternative considerate

- **Btrfs subito:** gli snapshot sono utili, ma aggiungono complessità a installer, recupero e documentazione proprio quando si deve dimostrare l'essenziale.

## Motivazione

ext4 è il filesystem più provato e più semplice da recuperare. Per la v0.x conta non perdere dati.

## Conseguenze

- Il recupero (DOC-20) viene documentato per ext4.
- La richiesta della passphrase LUKS all'avvio (plymouth o console) va provata con Speakup e documentata prima di consigliare la cifratura.

## Riesame

Alla v1.5 (snapshot e rollback), oppure se i test mostrano che la passphrase LUKS è accessibile e che la cifratura può diventare predefinita.
