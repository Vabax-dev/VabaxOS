# VabaxOS — Accessibility API Specification

| Campo | Valore |
|---|---|
| ID | VABAX-DOC-14 |
| Versione | 0.1.0 |
| Stato | Bozza di design — nessuna API Vabax pubblicata |
| Data | 2026-09-23 |
| Dipendenze | DOC-03, DOC-05, DOC-13, DOC-15, DOC-17 |

## 1. Scopo

Valutare un livello d'integrazione Vabax per consentire a shell, app e AT di scambiarsi semantica, eventi e azioni. L'API non deve duplicare o rompere AT-SPI2: la roadmap lo identifica come infrastruttura Linux principale. L'API Vabax è un'estensione facoltativa da motivare con un prototipo e interoperabilità upstream.

## 2. Principi

- AT-SPI2 e i toolkit accessibili restano il percorso interoperabile primario finché un ADR non dimostri un limite concreto.
- Un'app deve esporre nomi, ruolo, stato, valore, relazioni, azioni, testo e selection usando la semantica standard disponibile.
- API additive, versionate, documentate e indipendenti dal linguaggio dove possibile.
- Nessuna API richiede privilegi root; bus e dati accessibili rispettano confini di sessione e privacy.
- Gli eventi sono ordinati, minimizzati e non duplicano annunci non necessari.
- Supportare fallback a tastiera e output testuale in caso di AT non compatibile.

## 3. Possibili domini (da prototipare)

1. **Semantic tree adapter:** mapping di widget/modelli non standard verso oggetti accessibili, senza creare un albero concorrente.
2. **System announcements:** eventi di avvio, rete, batteria, update e errori con livello/priorità.
3. **Speech/Braille routing:** invio di messaggi strutturati a broker di speech e Braille, se non coperto adeguatamente da API correnti.
4. **Accessibility profile:** lettura/modifica autorizzata delle preferenze accessibili e loro persistenza.
5. **Diagnostics:** ispezione accessibile dell'albero e dump redatti per issue, con consenso.

Questi sono ambiti possibili, non API già decise.

## 4. Schema concettuale di un evento

Un prototipo può rappresentare evento con: `event_id`, `source_id`, `type`, `priority`, `timestamp`, `locale`, `payload` semantico, azioni disponibili e privacy class. Il payload non deve includere testo sensibile indiscriminato. Definire ack/deduplication, durata, cancellazione, ordering, timeout, rate limits e comportamento in assenza di consumer.

## 5. Requisiti di interoperabilità e sicurezza

- Non bloccare client AT standard o interrompere l'albero AT-SPI esistente.
- API versionate con negoziazione capabilities e comportamento fallback.
- Test con Orca e toolkit; evitare che ogni app dipenda da Vabax-only extension per accessibilità di base.
- Controlli per identità applicazione, sessione, consenso, autorizzazioni e redazione.
- L'API non può annunciare comandi arbitrari come già eseguiti: azioni mutative richiedono conferma e risultato.

## 6. Criteri per l'adozione

Un ADR deve indicare lacuna non risolta da standard/toolkit, schema prototipale, interop con AT-SPI2, client di prova, minacce, governance e piano di deprecazione. Testare con almeno un'app GTK e una non-GTK e verificare che Orca continui a funzionare senza il servizio Vabax. Se il caso d'uso è risolvibile con un contributo upstream, preferire upstream.

## 7. Decisioni aperte

Necessità effettiva di API aggiuntiva; trasporto (D-Bus candidato); schema ID/versionamento; SDK linguaggi; licenza; mantenimento compatibilità; ownership progetto; accesso dati diagnostici.

## Riferimenti ufficiali

- [AT-SPI2 developer guide](https://gnome.pages.gitlab.gnome.org/at-spi2-core/devel-docs/index.html)
- [AT-SPI API](https://docs.gtk.org/atspi2/)
- [GTK accessibility](https://docs.gtk.org/gtk4/section-accessibility.html)
- [D-Bus specification](https://dbus.freedesktop.org/doc/dbus-specification.html)
- [Freedesktop specifications](https://specifications.freedesktop.org/)

## Cronologia

- 0.1.0 — 2026-09-23: bozza esplorativa, non implementabile senza ADR.
