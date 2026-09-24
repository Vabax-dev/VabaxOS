# VabaxOS — Product Vision, Positioning & Excellence Framework

| Campo | Valore |
|---|---|
| ID | VABAX-DOC-24 |
| Versione | 0.1.0 |
| Stato | Posizionamento proposto — approvazione fondatore necessaria |
| Data | 2026-09-24 |
| Ambito | Promessa di prodotto, esperienza inclusiva, misure di qualità |

## 1. Visione

**VabaxOS nasce accessibile.** L'accessibilità è un requisito architetturale e di qualità per l'intero sistema, non una patch applicata dopo aver progettato l'esperienza standard. L'obiettivo è un Linux usabile da tutti, con più modalità equivalenti di interazione e una base comune, mantenendo compatibilità e scelte personali.

La frase “il miglior Linux di sempre” può essere una stella polare interna; non è una promessa pubblica verificabile. La promessa pubblica deve descrivere versione, hardware, lingua, attività e prova.

## 2. Portafoglio prodotti

Gli strumenti Vabax per Windows e macOS sono già in sviluppo secondo il fondatore. Vanno gestiti come filoni distinti ma coerenti di un progetto più ampio: possono costruire esperienza, strumenti riutilizzabili e rapporto con gli utenti, ma non sono VabaxOS e non sostituiscono l'obiettivo del sistema operativo. Non assumere condivisione di codice, roadmap o finanziamento prima di una decisione esplicita.

## 3. Posizionamento

**Categoria:** distribuzione Linux general-purpose, accessibile by design.  
**Differenza da dimostrare:** boot e configurazione vocale offline, desktop keyboard-first, supporto accessibilità mantenuto nel ciclo di release, trasparenza delle barriere e compatibilità applicativa misurata.  
**Per chi:** persone cieche/ipovedenti e utenti con esigenze motorie, uditive o cognitive; famiglie, scuole e professionisti che vogliono un sistema mainstream con impostazioni flessibili. Le personas vanno validate, non inventate dall'ufficio marketing.

**Non promettere:** funziona su qualsiasi PC; ogni app/gioco è accessibile; sostituisce Windows/macOS per tutti; sicurezza assoluta; screen reader “al livello di NVDA” prima di test comparativi e utenti.

## 4. Principi prodotto

1. Accessibilità entra nel brief, wireframe/API, implementazione, test e release.
2. Modalità visiva, tastiera, voce e Braille si incontrano in un unico desktop, non in edizioni separate.
3. Offline-first per bootstrap e percorso essenziale di assistenza.
4. L'utente mantiene controllo su output, privacy, aggiornamenti e profili.
5. Compatibilità Linux upstream prima di fork; limiti espliciti per app di terzi.
6. Leggerezza e velocità sono misurate su hardware definito, senza sacrificare autonomia o sicurezza.
7. Errori e recovery sono esperienze di prodotto, non note a piè pagina.

## 5. Quality Scorecard

Per ogni milestone pubblicare un punteggio con evidenze, non un voto sintetico opaco: task essenziali completabili (keyboard/AT); autonomia al primo avvio; tasso test passati; stabilità e crash; tempo e latenza; hardware/app matrix; localizzazione; security findings; soddisfazione e barriera top. Test automatici sono integrati con sessioni di persone disabili. Metriche e soglie si approvano prima del test.

## 6. Promessa per fase

- **v0.1:** dimostrazione limitata boot → TTS offline → configurazione → desktop, su configurazioni dichiarate.
- **alpha/beta:** miglioramento dei task supportati; known issues visibili e canale di feedback.
- **v1.0:** stabile solo quando la matrice hardware, i flussi A0 e i processi update/supporto rispettano gate pubblici.
- **serie 2.x:** nuove architetture e dispositivi attraverso programmi di compatibilità separati.

## 7. Messaggio esterno consigliato

“Stiamo costruendo VabaxOS, una distribuzione Linux progettata con l'accessibilità al centro. È un progetto in sviluppo: pubblichiamo le prove, i limiti e le decisioni man mano che arriviamo ai prototipi.” Evitare superlativi e certificazioni non conseguite.

## 8. Criteri di accettazione

Una feature non è pronta finché l'attività d'uso, gruppi utenti, alternativa d'accesso, criterio misurabile, test AT, prestazioni e failure path sono documentati. Una dichiarazione marketing deve essere collegabile a release e matrice pubblica.

## 9. Decisioni aperte

Nome/tagline ufficiale; utenti primari v0.1; desktop scope; standard di conformità; soglie prestazioni; confronto misurabile con altri OS; lingue e mercato; definizione di stable.

## Riferimenti

- [Vabax.it — Home](https://vabax.it/) e [Progetti](https://vabax.it/progetti/): contesto editoriale esistente di accessibilità, tecnologia e progetti digitali.
- [W3C WCAG 2.2](https://www.w3.org/TR/WCAG/): riferimento per l'accessibilità del sito, non certificazione del desktop OS.
- DOC-01 Roadmap; DOC-04 Requirements; DOC-05 Accessibility; DOC-07 QA.

## Cronologia

- 0.1.0 — 2026-09-24: visione e scorecard proposte.
- Nota 2026-09-24: registrati come filoni attivi gli strumenti Vabax per Windows e macOS, su conferma del fondatore.
