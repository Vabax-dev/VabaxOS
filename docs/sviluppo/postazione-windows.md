# Guida alla postazione di sviluppo su Windows

Questa guida prepara un PC Windows 11 per sviluppare VabaxOS insieme a Claude. È scritta per chi usa NVDA: ogni passo si fa da tastiera, e gli script scrivono messaggi brevi, una riga alla volta, che iniziano con **OK** oppure con **PROBLEMA**.

Le scelte sono quelle di [ADR-0013](../decisions/0013-ambiente-di-sviluppo.md): Windows resta il tuo computer di tutti i giorni, dentro c'è **Debian** (tramite WSL2) dove si costruisce VabaxOS, e **QEMU** è il laboratorio dove VabaxOS si avvia e parla senza toccare il tuo PC.

**Tempo:** da un'ora a due, quasi tutto di attesa per i download.

## Come è fatta la postazione

- **Windows 11 con NVDA:** il tuo ambiente, come sempre.
- **App Claude:** il posto dove parli con me. Io lavoro dentro Debian: scrivo il codice, costruisco la ISO, la avvio in QEMU.
- **WSL2 con Debian 13:** un Linux vero dentro Windows. È lo stesso sistema su cui si basa VabaxOS.
- **QEMU:** un PC virtuale dentro Debian. Lì VabaxOS si avvia e la sua voce esce dalle cuffie o dagli altoparlanti del tuo PC.
- **GitHub:** la copia ufficiale del progetto, su cui salvo il lavoro.

## Cosa serve prima di iniziare

- Windows 11 (il Galaxy Book4 360 va bene).
- NVDA **installato** (non la versione portatile), così parla anche nelle finestre di conferma di amministratore.
- Almeno 8 GB di memoria (16 consigliati) e almeno **60 GB liberi** sul disco C.
- Il caricatore collegato e una connessione a Internet stabile: si scaricano alcuni gigabyte.
- La password del tuo account GitHub **Vabax-dev**.
- La cartella **VabaxOS-postazione-Windows** (o il file zip con lo stesso nome), che contiene questa guida e gli script.

## Parte 1 — Aggiornare Windows e NVDA

### 1.1 Windows Update

1. Premi **Windows+I** per aprire Impostazioni.
2. Vai su **Windows Update** e attiva **Verifica disponibilità aggiornamenti**.
3. Installa tutto quello che trova e riavvia se richiesto. Ripeti finché non ci sono più aggiornamenti.

### 1.2 NVDA

1. Premi **NVDA+N** per aprire il menu di NVDA.
2. Vai su **Aiuto**, poi **Verifica aggiornamenti**.
3. Se c'è una versione nuova, installala.

### 1.3 Programma di installazione app (winget)

Lo script usa **winget**, il programma di Windows che scarica e installa le applicazioni. È già presente in Windows 11. Se lo script dice che manca:

1. Apri il **Microsoft Store** (menu Start, scrivi «Store», Invio).
2. Cerca **Programma di installazione app** (in inglese «App Installer») e aggiornalo.

## Parte 2 — Copiare la cartella su Windows

1. Copia la cartella **VabaxOS-postazione-Windows** in **Documenti**, per esempio con una chiavetta o dal cloud.
2. Se hai il file **zip**: selezionalo in Esplora file, premi il **tasto Applicazioni** (oppure Maiusc+F10), scegli **Estrai tutto**, poi Invio.

Dentro la cartella ci sono:

| File | A cosa serve |
|---|---|
| `Guida-postazione-Windows.html` | Questa guida, da aprire nel browser (con NVDA navighi per intestazioni con **H**) |
| `1-prepara-windows.cmd` | Avvia la preparazione di Windows |
| `prepara-windows.ps1` | Lo script di Windows vero e proprio (lo avvia il file precedente) |
| `prepara-debian.sh` | Lo script che prepara Debian |
| `verifica-postazione.sh` | Controlla che sia tutto pronto |
| `pacchetti-debian.txt` | L'elenco dei programmi per Debian |
| `PROMPT-avvio-Claude.txt` | Il messaggio da darmi la prima volta |
| `LEGGIMI.txt` | Un riassunto di una pagina |

## Parte 3 — Preparare Windows

### 3.1 Avviare lo script

1. In Esplora file, entra nella cartella **VabaxOS-postazione-Windows**.
2. Seleziona **1-prepara-windows.cmd** e premi **Invio**.
3. Windows chiede il permesso di amministratore (Controllo account utente). Scegli **Sì** e premi Invio.
4. Si apre una finestra di PowerShell. Lo script parla per passi numerati («Passo 1 di 7» e così via) e si ferma quando ti fa una domanda: scrivi **s** per sì oppure **n** per no, poi **Invio**.

Se Windows dice che il file viene da Internet e chiede conferma, scegli **Esegui comunque** (o **Esegui**).

### 3.2 Cosa scarica e installa lo script

Lo script fa sette passi:

1. **Controlli:** versione di Windows, memoria, spazio libero, virtualizzazione.
2. **Programmi per Windows**, scaricati con winget:
   - **Windows Terminal**, di solito già presente: è la finestra dove si leggono i terminali.
   - **Claude**, l'app per lavorare con me. Te lo chiede, perché installarla vuol dire accettarne i termini d'uso.
   - **Visual Studio Code**, facoltativo: serve solo se vuoi aprire i file da solo. Io non ne ho bisogno.
3. **WSL e Debian:** aggiorna WSL e installa Debian.
4. **Configurazione di WSL:** crea il file `.wslconfig` nella tua cartella utente con la virtualizzazione annidata attiva (serve a QEMU per essere veloce) e, se hai 16 GB o più, riserva a Debian 10 GB di memoria.
5. **Copia degli script** per Debian nella cartella `C:\VabaxOS-postazione`, un percorso breve e facile da scrivere.
6. **Sospensione:** ti chiede se disattivare la sospensione automatica **solo quando il caricatore è collegato**, perché una costruzione della ISO può durare mezz'ora e la sospensione la interromperebbe.
7. **Riepilogo** e riavvio.

Alla fine rispondi **s** per riavviare Windows. Il riavvio serve perché WSL diventi attivo.

### 3.3 Se preferisci fare a mano

Sono gli stessi comandi che usa lo script. Apri **Terminale (amministratore)**: premi **Windows+X**, poi **A**. Poi esegui:

```powershell
winget install --exact --id Anthropic.Claude
```

```powershell
winget install --exact --id Microsoft.VisualStudioCode
```

```powershell
wsl --install --distribution Debian
```

Puoi anche scaricare i programmi dai siti ufficiali: Claude da [claude.com/download](https://claude.com/download), Visual Studio Code da [code.visualstudio.com](https://code.visualstudio.com/).

## Parte 4 — Primo avvio di Debian

1. Premi il tasto **Windows**, scrivi **Debian** e premi **Invio**. Si apre una finestra di terminale.
2. La prima volta Debian si prepara per qualche secondo, poi chiede in inglese:
   - **Enter new UNIX username:** scrivi un nome breve, tutto minuscolo e senza spazi, per esempio `vabax`, poi Invio.
   - **New password:** scrivi una password. **Mentre la scrivi non si sente niente e non compare niente sullo schermo: è normale.** Poi Invio.
   - **Retype new password:** riscrivila e premi Invio.
3. Conserva questa password in un posto sicuro: te la chiederà Debian quando installa programmi. **Non scriverla mai nella chat con Claude.**

Quando compare il prompt, una riga che finisce con il simbolo del dollaro, Debian è pronta.

## Parte 5 — Preparare Debian

Nella finestra di Debian scrivi questo comando e premi Invio:

```bash
bash /mnt/c/VabaxOS-postazione/prepara-debian.sh
```

Lo script fa otto passi. Quando chiede la password, è quella di Debian della Parte 4.

1. **Versione di Debian:** se WSL ha installato Debian 12, ti propone di aggiornarla a Debian 13. Rispondi **s**.
2. **Pacchetti:** installa i programmi per costruire VabaxOS: Git e GitHub CLI, live-build, QEMU con il firmware UEFI, eSpeak NG, ShellCheck, gli strumenti per le licenze e le librerie GTK 4 per i programmi Vabax. Ci vogliono alcuni minuti.
3. **KVM:** ti dà il permesso di usare la virtualizzazione, così QEMU è veloce.
4. **Permesso per costruire la ISO.** Ti chiede se Claude può eseguire la costruzione come amministratore **senza chiederti la password**. Ti consiglio **s**: altrimenti ogni volta dovrai costruire tu la ISO con un comando. Il permesso vale solo dentro Debian. Windows e i tuoi file restano protetti dai normali permessi del tuo utente Windows.
5. **Identità dei commit:** chiede nome ed email da scrivere nella storia del progetto, per esempio `Vabax` e `info@vabax.it`.
6. **Repository:** scarica VabaxOS da GitHub nella cartella `~/projects/VabaxOS`.
7. **Prova della voce:** il PC dice «La postazione VabaxOS sta parlando». Se la senti, l'audio fra Debian e Windows funziona.
8. **Riavvio di WSL:** premi Invio e la finestra si chiude.

## Parte 6 — Collegare GitHub

Serve perché io possa salvare il lavoro sul repository. **L'accesso lo fai tu**: la password non passa mai da me.

1. Riapri **Debian** dal menu Start.
2. Scrivi questo comando e premi Invio:

   ```bash
   gh auth login
   ```

3. Rispondi alle domande con le frecce e Invio:
   - *Where do you use GitHub?* → **GitHub.com**
   - *What is your preferred protocol?* → **HTTPS**
   - *Authenticate Git with your GitHub credentials?* → **Yes**
   - *How would you like to authenticate?* → **Login with a web browser**
4. Compare un **codice di otto caratteri**, nella forma `ABCD-1234`. Leggilo con NVDA e copialo o annotalo, poi premi Invio.
5. Nel browser di Windows apri [github.com/login/device](https://github.com/login/device), accedi con l'account **Vabax-dev**, scrivi il codice e conferma con **Authorize**.
6. Torna in Debian e scrivi:

   ```bash
   gh auth setup-git
   ```

## Parte 7 — Verificare la postazione

In Debian scrivi:

```bash
bash ~/projects/VabaxOS/scripts/postazione/verifica-postazione.sh
```

Lo script controlla tutto e scrive una riga per ogni controllo. Alla fine **lo dice a voce**: «La postazione VabaxOS è pronta», oppure quanti problemi ci sono. Per trovare le righe con un problema, in Windows Terminal premi **Ctrl+Maiusc+F** e cerca **PROBLEMA**.

Se c'è la riga **AVVISO** sul comando `lb`, vuol dire che alla Parte 5 hai risposto no al permesso di costruzione. Va bene lo stesso: sarai tu a costruire la ISO quando te lo chiedo.

## Parte 8 — Collegare Claude al progetto

### 8.1 Aprire il progetto nell'app Claude

1. Apri l'app **Claude** e accedi con il tuo account.
2. Vai nella sezione **Code**.
3. Prima di scrivere, apri il selettore dell'**ambiente** (dove si sceglie dove lavora Claude) e scegli **WSL**, poi **Debian**.
4. Nel selettore della cartella scegli `/home/NOME/projects/VabaxOS`, dove NOME è il nome utente di Debian della Parte 4.
5. La prima volta l'app chiede se ti fidi della cartella: rispondi di sì. La prima sessione in Debian è un po' più lenta, perché l'app si prepara.

Da quel momento la cartella compare fra quelle recenti di Debian: le volte successive basta sceglierla.

### 8.2 Il primo messaggio

1. Apri **PROMPT-avvio-Claude.txt** con il Blocco note: selezionalo in Esplora file e premi Invio.
2. Premi **Ctrl+A** e poi **Ctrl+C** per copiarlo tutto.
3. Torna nell'app Claude, nella casella del messaggio premi **Ctrl+V**, poi **Invio**.

Il file `CLAUDE.md` nel repository mi dice tutto il resto a ogni sessione: chi sei, le regole del progetto e a che punto siamo.

### 8.3 Permessi

All'inizio l'app ti chiede il permesso prima che io esegua un comando o modifichi un file. Puoi concederlo volta per volta, oppure sempre per quel tipo di comando. Più permessi concedi, meno ti interrompo. Le cose rischiose te le chiedo comunque: scrivere su una chiavetta, pubblicare una release, cambiare le impostazioni del repository.

### 8.4 In alternativa: Claude nel terminale

Se preferisci il terminale all'app, in Debian:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Chiudi e riapri Debian, poi:

```bash
cd ~/projects/VabaxOS && claude
```

La prima volta ti chiede di accedere: segui il collegamento che compare, come per GitHub.

## Parte 9 — Come lavoriamo ogni giorno

1. Apri l'app Claude, sezione Code, ambiente **Debian**, cartella **VabaxOS**.
2. Dimmi cosa vuoi fare, oppure chiedimi «a che punto siamo?».
3. Io lavoro, costruisco la ISO e la avvio in QEMU. **Quando VabaxOS deve parlare, te lo dico prima**: la voce esce dalle cuffie o dagli altoparlanti del PC. Tu mi dici cosa senti. Io non posso ascoltare: la tua conferma è una parte vera dei test.
4. Se serve un comando con la password di amministratore, te lo scrivo intero in un blocco a parte: lo copi nella finestra di Debian e premi Invio.

Le ISO costruite si trovano, da Windows, in questa cartella (sostituisci NOME):

```text
\\wsl.localhost\Debian\home\NOME\projects\VabaxOS\out
```

Per aiutarmi a lavorare al meglio: tieni il caricatore collegato durante le costruzioni, non chiudere l'app mentre lavoro, e dimmi sempre cosa hai sentito o dove ti sei fermato, anche quando sembra un dettaglio.

## Problemi comuni

**La virtualizzazione è spenta.** Si attiva nel firmware del PC (sul Galaxy Book si entra premendo F2 all'accensione). Il firmware non parla e non funziona con NVDA: serve l'aiuto di una persona vedente. Cerca una voce come «Intel Virtualization Technology» o «VT-x» e impostala su «Enabled».

**/dev/kvm non esiste.** Controlla che nella tua cartella utente il file `.wslconfig` contenga `nestedVirtualization=true` nella sezione `[wsl2]`. Poi in PowerShell esegui `wsl --shutdown` e riapri Debian. Serve Windows 11.

**Non si sente la voce da Debian.** In PowerShell esegui `wsl --update` e poi `wsl --shutdown`, riapri Debian e riprova. Controlla anche che su Windows l'uscita audio predefinita sia quella giusta.

**winget non installa un programma.** Aggiorna Programma di installazione app dal Microsoft Store (Parte 1.3), oppure scarica il programma dal sito ufficiale (Parte 3.3).

**Ho dimenticato la password di Debian.** In PowerShell esegui `wsl -d Debian -u root passwd NOME`, sostituendo NOME con il tuo nome utente di Debian, e scegli una password nuova.

**Uno script .sh dà errori con `$'\r'`.** Il file è stato convertito nel formato di testo di Windows durante la copia. In Debian esegui `sed -i 's/\r$//' NOMEFILE` e riprova.

## Cosa non fare

- **Non installare VabaxOS sul Galaxy Book.** Le prove si fanno in QEMU e poi su un PC dedicato, sempre in modalità live.
- **Non scrivere una ISO su chiavetta o su disco** senza aver controllato due volte il dispositivo. Quando arriverà il momento ci sarà una guida apposta.
- **Non scrivere password, codici o token nella chat con Claude.**

## Riepilogo di cosa viene installato

| Dove | Programma | Perché |
|---|---|---|
| Windows | Windows Terminal | Per leggere i terminali con NVDA |
| Windows | App Claude | Per lavorare con Claude |
| Windows | Visual Studio Code (facoltativo) | Per aprire i file da solo |
| Windows | WSL2 | Per avere Linux dentro Windows |
| WSL | Debian 13 | Base di sviluppo, uguale a quella di VabaxOS |
| Debian | Git, GitHub CLI | Storia del progetto e GitHub |
| Debian | live-build e strumenti per le ISO | Costruire la ISO |
| Debian | QEMU, OVMF | Avviare VabaxOS in un PC virtuale con UEFI |
| Debian | eSpeak NG, pulseaudio-utils | Provare la voce e l'audio |
| Debian | ShellCheck, reuse, jq | Controllo del codice e delle licenze |
| Debian | Python, GTK 4, libadwaita | Programmi Vabax |
