# packages/

Pacchetti Debian di VabaxOS, uno per cartella, con prefisso `vabaxos-` ([ADR-0008](../docs/decisions/0008-pacchetti-e-applicazioni.md)). Fino al repository APT Vabax (v0.2) stanno solo dentro la ISO.

| Pacchetto | Cosa fa |
|---|---|
| `vabaxos-accessibility` | Voce della console (Speakup con eSpeak NG) nella lingua del sistema, Orca attivo di default, «senza voce» che spegne entrambi, nomi dei pulsanti di GNOME Shell con la sola icona (ADR-0022), `vabaxos-a11y-check`, `vabaxos-status`, `vabaxos-report` |
| `vabaxos-apps` | La finestra «Programmi»: avvio automatico, disinstalla |
| `vabaxos-branding` | Nome, logo, sfondi, font Atkinson Hyperlegible Next |
| `vabaxos-agenda` | Agenda a frasi dai calendari di GNOME (anche Google e Outlook), nuovi appuntamenti scritti come si dicono, Super+Alt+A, avviso 15 minuti prima |
| `vabaxos-translate` | Traduttore senza Internet con il modello della descrizione delle immagini (Qwen3.5); Super+Alt+T traduce il testo copiato |
| `vabaxos-vision` | Ingrandimento e contrasto con un tasto, detti a voce: Super+più e meno, Super+Ctrl+C, testo grande; colori invertiti, bianco e nero, mirino |
| `vabaxos-books` | Libri e audiolibri gratuiti: Project Gutenberg nel lettore, LibriVox in Notizie e podcast, Liber Liber nel browser |
| `vabaxos-radio` | Radio via Internet da tastiera (Radio Browser): ricerca per nome o genere, preferite, brano in onda con Ctrl+I |
| `vabaxos-orca-sounds` | Suoni del lettore di schermo: un suono breve al posto di «pulsante», «collegamento» e degli altri ruoli, con un'estensione di Orca 51 approvata su richiesta; impara i suoni |
| `vabaxos-camera` | Leggi con la fotocamera: la voce guida il foglio davanti alla webcam (luce, lati, distanza), scatta da sola e legge con l'OCR; Ctrl+D descrive |
| `vabaxos-checkup` | Controllo del computer a voce: audio, rete, batteria e usura, Braille, Bluetooth, microfono, fotocamera, memoria, disco; al primo accesso, poi le lezioni dei tasti |
| `vabaxos-store` | Negozio dei programmi per Orca: ricerca mentre si scrive, Installa, Apri, Rimuovi; Debian con PackageKit e, su richiesta, Flathub per l'utente |
| `vabaxos-connections` | Wi-Fi e Bluetooth a voce: reti con protezione e segnale a parole, password, abbinamento con il codice detto cifra per cifra; Super+K |
| `vabaxos-trouble` | «Qualcosa non va»: primi controlli detti a voce e rapporto dei registri con i dati personali nascosti, da allegare; niente invio, niente aiuto remoto |
| `vabaxos-games` | Giochi audio: memory dei suoni, indovina il numero, tris contro il computer; tutto a voce e da tastiera |
| `vabaxos-communication` | WhatsApp, Telegram e videochiamata (Jitsi Meet) nel menu Start, nelle finestre di Firefox |
| `vabaxos-describe` | Descrizione delle immagini senza Internet (Super+Alt+P); il modello (Qwen3.5 0,8B) si scarica a richiesta (ADR-0029) |
| `vabaxos-dictation` | La dettatura senza Internet (Super+H), con whisper.cpp |
| `vabaxos-firewall` | Il firewall come quello di Windows: reti private e pubbliche (ADR-0021) |
| `vabaxos-help` | L'aiuto di VabaxOS: le guide di `docs/utente` in HTML |
| `vabaxos-lessons` | Impara i tasti: lezioni con esercizi controllati a voce |
| `vabaxos-math` | Calcolatrice parlante e formule dette a parole (Super+Alt+M) |
| `vabaxos-news` | Notizie e podcast: feed RSS e Atom, riassunti, episodi con pausa, salti e velocità |
| `vabaxos-ocr` | Il testo dello schermo riconosciuto per il lettore di schermo (Super+Alt+R) |
| `vabaxos-print` | Stampanti e scanner: stampa di prova, predefinita, scansiona e leggi; niente cups-browsed |
| `vabaxos-reader` | Il [lettore di documenti](../docs/utente/lettore.md) |
| `vabaxos-reminders` | Promemoria e sveglie scritti come si dicono, detti all'ora giusta |
| `vabaxos-restore` | Il ripristino del sistema con Timeshift: copie prima di ogni aggiornamento e ogni settimana (ADR-0027) |
| `vabaxos-screen-reader` | Le impostazioni e i tasti di Orca (blocchi 9 e 10) |
| `vabaxos-settings` | Impostazioni di GNOME: niente tour, niente sospensione automatica, niente blocco dello schermo con password, tasti di Windows e pulsante Start (`vabaxos-keys@vabaxos.org`) |
| `vabaxos-setup` | La configurazione iniziale: vista, voce, tastiera, rete |
| `vabaxos-sounds` | I suoni di sistema |
| `vabaxos-start` | Il [menu Start](../docs/utente/menu-start.md) (ADR-0025) |
| `vabaxos-tuning` | Ottimizzazioni del sistema: memoria compressa (zram) prima del disco |
| `vabaxos-unlock` | La voce quando all'avvio si chiede la password del disco cifrato (ADR-0021) |
| `vabaxos-update` | Gli aggiornamenti a voce (ADR-0020) |
| `vabaxos-voice` | La voce naturale Kokoro per speech-dispatcher (ADR-0019) e il programma «Voce naturale» (scarica, misura, usa per Orca); per ora **fuori dalla ISO** (ADR-0026, file `not-in-iso`; ADR-0030 proposta: nella ISO senza il modello) |
| `vabaxos-welcome` | Il [benvenuto parlato](../docs/utente/benvenuto.md) prima del desktop (ADR-0016) e «Installa ora» (ADR-0023) |

## Com'è fatta una cartella

- `control`: il file `DEBIAN/control`, senza la riga `Version` (la aggiunge lo script);
- `root/`: i file da installare, nella posizione che avranno nel sistema;
- `postinst`, `postrm`: script del pacchetto, facoltativi;
- `po/*.po`: traduzioni gettext del programma, facoltative;
- `not-in-iso`: il pacchetto si costruisce per i test ma non entra nella ISO; il file dice perché.

`scripts/build-packages.sh CARTELLA` costruisce tutti i pacchetti senza privilegi di root. `scripts/build.sh` lo chiama da solo e mette i pacchetti nella ISO.

## Test

```bash
python3 tests/welcome/test_welcome.py
```

Prova il benvenuto in un terminale finto, senza voce e senza cambiare il sistema: il programma scrive in un file cosa avrebbe detto e fatto (`VABAXOS_WELCOME_DRY_RUN`).
