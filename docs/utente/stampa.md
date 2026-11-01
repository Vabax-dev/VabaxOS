# Stampanti e scanner

**Stampanti e scanner**, nel menu Start, aiuta a stampare e a leggere i fogli di carta.

## Le stampanti

Le stampanti moderne (quasi tutte quelle degli ultimi dieci anni) **non hanno bisogno di installare niente**: accendile, collegale alla stessa rete del computer oppure con il cavo USB, poi premi **Cerca di nuovo** (F5).

Per ogni stampante trovata:

- **Stampa una prova:** una pagina di prova, per sapere se funziona;
- **Rendi predefinita:** sarà quella scelta quando stampi da un programma (Ctrl+P).

Per le stampanti più vecchie, **Altre stampanti** apre le Impostazioni di GNOME.

## Gli scanner

Per ogni scanner trovato c'è **Scansiona e leggi**: metti il foglio sul vetro e premi Invio. In circa un minuto il foglio è salvato nella cartella **Documenti, Scansioni**, e si apre il [lettore di documenti](lettore.md), che riconosce il testo e lo legge ad alta voce.

## Sicurezza

VabaxOS non installa il servizio `cups-browsed`, che nel 2024 ha avuto una falla grave raggiungibile dalla rete (CVE-2024-47176); le stampanti si trovano lo stesso.
