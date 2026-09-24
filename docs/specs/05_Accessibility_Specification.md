# VabaxOS — Accessibility Specification

| Campo | Valore |
|---|---|
| ID | VABAX-DOC-05 |
| Versione | 0.1.0 |
| Stato | Bozza tecnica — specifica proposta, non baseline approvata |
| Data | 2026-09-23 |
| Ambito | Comportamento accessibile di sistema, sessione, applicazioni e recovery |
| Dipendenze | DOC-03 Architecture Specification; DOC-04 Requirements Specification; roadmap originale da riallineare |

## 1. Scopo e obiettivo

Definire come progettare e verificare VabaxOS perché una persona cieca o ipovedente, con difficoltà motorie o cognitive, oppure con necessità di supporto uditivo, possa usare il sistema in autonomia. L'accessibilità non è solo uno screen reader: comprende boot, installazione, input, focus, audio, Braille, finestre, notifiche, impostazioni, applicazioni, aggiornamenti e diagnostica.

La roadmap tecnica nomina screen reader, TTS, tastiera e rimappatura, Braille, mouse/touchpad, focus, finestre, suoni personalizzati, installer, login, terminale, file manager, gaming, localizzazione e strumenti assistivi. Le tecnologie, i livelli di conformità e le lingue di release esatte non sono tutte decisioni approvate.

## 2. Principi

- **Tastiera prima:** qualsiasi attività essenziale deve poter essere completata senza mouse.
- **Semantica completa:** ogni controllo deve esporre ruolo, nome, stato, valore, relazioni e azioni pertinenti alla tecnologia AT.
- **Focus prevedibile:** il focus deve essere visibile, ordinato, non perso e annunciato nei cambi significativi.
- **Controllo dell'utente:** voce, volume, velocità, tasti rapidi, notifiche, profili e modalità assistive sono configurabili; nessun cambio improvviso senza feedback.
- **Ridondanza sensoriale:** non comunicare stato o errore soltanto con colore, suono o animazione.
- **Coerenza:** impostazioni, scorciatoie, annunci ed errori seguono un comportamento comune.
- **Privacy e dignità:** contenuti personali non sono letti ad alta voce in contesti non appropriati; modalità e output sono sotto controllo utente.
- **Robustezza:** guasti a una singola AT, uscita audio o app non devono bloccare l'intero sistema; offrire una procedura di recupero accessibile.
- **Verifica con persone:** test automatici e audit tecnici non sostituiscono test con utenti con disabilità.

## 3. Livelli e priorità

### Obiettivo accessibilità della v0.1

La roadmap richiede boot fino al desktop con voce: TTS offline, screen reader attivo, configurazione iniziale accessibile e flusso verificato in VM e su almeno un PC fisico. Orca è indicato come integrazione iniziale di riferimento per v0.1, tramite AT-SPI; lo sviluppo progressivo di Vabax Screen Reader è una direzione, non un componente già disponibile. La roadmap considera eSpeak NG come fallback e un TTS neurale locale opzionale, ma entrambi richiedono test e revisione licenze prima dell'adozione. Braille è previsto “se disponibile” nel prototipo e va documentato per dispositivo effettivamente provato.


**A0 — blocco di autonomia:** boot/accesso, scelta lingua/layout, avvio e recupero AT, navigazione base, focus, impostazioni essenziali, installazione/aggiornamento sicuri.
**A1 — uso quotidiano:** finestre, notifiche, file, terminale, rete, software, documenti e browser inclusi o raccomandati.
**A2 — avanzato:** Braille e display specifici, OCR/descrizione, controllo vocale, touchscreen, gaming accessibile e automazioni.

Una funzione è “supportata” solo se è inclusa in una matrice per versione e hardware, con test e limiti noti. Nessuna tecnologia o applicazione di terze parti può essere dichiarata accessibile per presunzione.

## 4. Requisiti comportamentali

| ID | Requisito verificabile |
|---|---|
| A11Y-001 | Ogni controllo interattivo deve avere nome accessibile localizzato, ruolo corretto, stato e valore quando pertinenti. Nome visivo e nome AT non devono contraddirsi. |
| A11Y-002 | L'ordine di navigazione da tastiera deve seguire un ordine logico; non devono esistere trappole di tastiera nei flussi essenziali. |
| A11Y-003 | Il focus tastiera deve essere visivamente distinguibile con contrasto e dimensione configurabili; il focus AT deve essere leggibile e sincronizzato con la vista corrente. |
| A11Y-004 | Apertura/chiusura di finestre, dialoghi, menu, notifiche ed errori deve portare il focus in modo prevedibile e restituirlo al punto di origine quando opportuno. |
| A11Y-005 | Gli aggiornamenti dinamici importanti (esito comando, validazione, avanzamento, notifica) devono essere esposti alle AT senza annunciare ogni variazione non significativa. |
| A11Y-006 | Gli shortcut globali devono essere documentati, non confliggere con combinazioni di sistema/AT e poter essere modificati o disattivati. |
| A11Y-007 | La rimappatura/layout tastiera deve poter essere ispezionata e modificata da tastiera, con annuncio della lingua/layout attivo. |
| A11Y-008 | Sticky/Slow/Bounce Keys e altre funzioni di accesso motorio devono essere valutate; ogni opzione inclusa deve esporre stato, feedback e disattivazione. |
| A11Y-009 | Informazioni non devono dipendere solo dal colore; grafici e indicatori devono avere testo o alternative equivalenti. |
| A11Y-010 | Zoom, dimensione testo, contrasto, temi e riduzione animazioni devono essere disponibili e persistenti; valori e interfaccia di configurazione sono da definire. |
| A11Y-011 | TTS, lingua, voce, volume, velocità e uscita audio devono poter essere scelti separatamente dalla lingua dell'interfaccia quando gli engine lo consentono. |
| A11Y-012 | Il primo avvio deve comunicare come avviare l'AT, scegliere lingua e output accessibile; la fase e la combinazione di tasti sono decisioni da prototipare. |
| A11Y-013 | Se un servizio AT o un'uscita audio fallisce, fornire feedback alternativo e un percorso di riavvio/recupero da tastiera. |
| A11Y-014 | Login, unlock, installazione, partizionamento, aggiornamento, conferme distruttive e recovery devono essere testabili da tastiera e AT; nessun controllo essenziale solo grafico. |
| A11Y-015 | File manager, software center e impostazioni devono esporre selezione, percorso, progressi, ordinamento e errori con semantica accessibile. |
| A11Y-016 | Terminale e output testuale devono supportare selezione, scrollback, focus e feedback coerenti con le AT; non alterare output senza comando dell'utente. |
| A11Y-017 | Notifiche e suoni devono poter essere silenziati, differiti o configurati; le notifiche urgenti devono avere priorità e testo accessibile. |
| A11Y-018 | Drag-and-drop deve avere alternative via tastiera e menu/azioni equivalenti ove la funzione sia essenziale. |
| A11Y-019 | Ogni profilo gaming/performance deve rispettare lo stato delle AT; sospensione o modifica dell'AT richiede consenso, avviso e ripristino accessibile. |
| A11Y-020 | Impostazioni AT e ausili devono persistere al logout/reboot e poter essere ripristinate senza rendere inaccessibile l'interfaccia. |
| A11Y-021 | Braille deve essere valutato per dispositivi, driver, traduzione e input; le combinazioni supportate sono TBD e vanno pubblicate. |
| A11Y-022 | OCR, descrizione immagini e controllo vocale, se inclusi, devono dichiarare elaborazione locale/remota, limiti, privacy, lingue e conferma delle azioni. |
| A11Y-023 | Errori e procedure diagnostiche devono presentare testo chiaro, codice/contesto copiabile e opzione di report, senza inviare dati senza consenso. |
| A11Y-024 | L'interfaccia deve supportare localizzazione senza codificare lingua o formato; le lingue iniziali vanno approvate e verificate per TTS/AT. |

## 5. Modello di verifica

### Test automatici

Ispezionare nomi/ruoli/stati, alberi accessibili, errori di contrasto ove misurabili, stringhe mancanti, trappole note e regressioni di API. Gli scanner non certificano da soli la conformità.

### Test manuali assistiti da tastiera/AT

Per ogni flusso A0: completare da avvio con tastiera; registrare focus atteso e annunci; ripetere con finestra ridimensionata e almeno due lingue/locale quando disponibili; provare errore, annullamento e ritorno. L'AT effettiva e la sua versione devono comparire nel report.

### Test con utenti

Pianificare sessioni consensuali con utenti ciechi/ipovedenti e persone con differenti esigenze motorie/cognitive. Raccogliere esiti e barriere senza dati identificativi non necessari. Protocollo, reclutamento e criteri di release richiedono approvazione e risorse; non sono presunti già operativi.

### Criteri di accettazione

- Nessun difetto bloccante A0 aperto per una release dichiarata accessibile.
- Il 100% dei casi A0 definiti per la release ha esito superato o deroga approvata con alternativa e rischio documentati.
- Copertura di ogni requisito A11Y inclusa in matrice: implementato, non applicabile motivato, differito o fallito.
- Report include build, hardware/VM, lingua, AT, TTS, passi, esito e issue.
- Ogni limite noto è mostrato nell'elenco compatibilità accessibile.

## 6. Matrice minima per scenario

| Scenario | Evidenza attesa |
|---|---|
| Boot e primo avvio | percorso AT documentato, feedback disponibile, recupero in caso di errore |
| Login e blocco schermo | campi semantici, input, feedback non divulgativo e uscita sicura |
| Desktop e finestre | elenco finestre/workspace, focus coerente, menu e dialoghi operabili |
| Impostazioni e tastiera | cambio layout/lingua, scorciatoie e funzioni motorie |
| File/rete/installazione | selezione, progresso, errori e conferme accessibili |
| Aggiornamento/recovery | stato, riavvio, fallimento e ritorno a stato utilizzabile |
| Applicazioni terze | limiti dichiarati, compatibilità per versione e workaround accessibili |
| Gaming (fase successiva) | avvio/uscita, controller, profilo performance e persistenza AT |

## 7. Dipendenze e decisioni aperte

Le decisioni esplicitamente aperte prima della v0.1 nella roadmap includono Orca personalizzato/fork contro Vabax Screen Reader; strategia TTS eSpeak NG + eventuale motore neurale; desktop iniziale e integrazione Wayland/AT. Il prototipo deve provare la catena reale (audio → TTS → Orca/AT-SPI → configurazione → sessione desktop) senza rete. La scelta finale del motore, voce, modalità bootstrap, shortcut e supporto Braille deve apparire in ADR e matrice hardware/software.


La qualità accessibile dipende da compositor/display protocol, toolkit, API AT, screen reader, TTS, audio, Braille, input e packaging. AT-SPI2 e Wayland sono candidati richiamati nella preview, ma vanno verificati con un proof of concept su login, compositor/sessione, app toolkit e applicazioni legacy. Non è ancora scelta una combinazione screen reader/motore/voce, né un livello di conformità formale, né il supporto ai singoli display Braille.

La specifica va mappata ai criteri normativi e alle linee guida applicabili al mercato di distribuzione dopo valutazione legale/tecnica; questo documento non dichiara conformità o certificazione.

## 8. Riferimenti ufficiali

- [AT-SPI2 development guide](https://gnome.pages.gitlab.gnome.org/at-spi2-core/devel-docs/index.html) e [API AT-SPI](https://docs.gtk.org/atspi2/) — API e infrastruttura AT.
- [GTK 4 Accessibility](https://docs.gtk.org/gtk4/section-accessibility.html) — supporto del toolkit e semantica.
- [Wayland protocol/model](https://wayland.freedesktop.org/docs/book/Protocol.html) — protocollo display da considerare nella valutazione.
- [Documentazione Linux kernel](https://docs.kernel.org/) — input, driver e testing di sistema.
- Standard e linee guida di accessibilità applicabili: da selezionare e mappare prima di dichiarazioni di conformità.

## 9. Allineamento ai sorgenti originali

La roadmap tecnica e la guida Windows Development Environment sono state individuate negli output precedenti del progetto. La prima è fonte per il requisito v0.1 di ISO Live x86-64, boot UEFI, voce offline, screen reader e test VM + un PC fisico. La seconda è fonte per il laboratorio di sviluppo: Windows 11/WSL2/Ubuntu 24.04 e QEMU. La combinazione AT va testata sulla sessione scelta; la workstation e la VM sono mezzi di sviluppo/verifica e non sostituiscono il test fisico richiesto dalla roadmap.

## 10. Cronologia

- 0.1.0 (2026-09-23): prima bozza, requisiti derivati dalla roadmap preview e tecnologie candidate lasciate aperte.
