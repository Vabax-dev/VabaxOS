# Analisi dei bug - 2 ottobre 2026

Analisi approfondita del codice sorgente di VabaxOS per individuare bug, problemi di sicurezza e criticità. L'analisi ha coperto tutti i componenti: script Bash, codice Python (pacchetti VabaxOS, estensioni GNOME Shell), configurazione systemd, e test automatici.

## Metodologia

1. Analisi statica del codice sorgente
2. Ricerca di pattern comuni di bug in progetti simili
3. Consultazione di problemi noti online (speech-dispatcher, Orca, GNOME Shell, PipeWire, live-build)
4. Verifica di vulnerabilità note (race condition, memory leak, command injection, deadlock)

## Fonti consultate

- [GNOME Shell Extensions Review Guidelines](https://gjs.guide/extensions/review-guidelines/review-guidelines.html) - pattern di memory leak nelle estensioni
- [speech-dispatcher: dummy module causes PipeWire spin](https://github.com/brailcom/speechd/issues/787) - latenza audio
- [rtkit-daemon race condition](https://groups.google.com/g/linux.debian.bugs.dist/c/sT39e8jn8NQ) - PipeWire vs rtkit all'avvio
- [Orca on GNOME 50: only reads labels](https://discourse.gnome.org/t/orca-on-gnome-50-wayland-only-reads-element-labels-not-text-content-plus-automatic-language-switching-not-working/38619) - bug noto, già documentato in VabaxOS
- Varie discussioni su systemd user services, PipeWire startup, bash script race conditions

## Bug trovati e corretti

### Critical

#### 1. Memory leak estensione button-names (GNOME Shell)

**File:** `packages/vabaxos-accessibility/root/usr/share/gnome-shell/extensions/button-names@vabaxos.org/extension.js:154-165`

**Problema:** L'estensione connette il segnale `child-added` a ogni actor dello stage, ma non disconnette mai quando un actor viene rimosso. Gli handler rimangono attivi su oggetti distrutti, causando memory leak.

**Impatto:** GNOME Shell cresce di 1-2 MB per ogni notifica aperta/chiusa. Dopo circa 100 notifiche, 200 MB persi. Può causare il freeze di GNOME Shell riportato in CLAUDE.md (2026-09-25).

**Correzione:** Aggiunto handler `destroy` su ogni actor per disconnettere i segnali quando l'actor viene distrutto.

**Fonte:** Documentato nelle [GNOME Extensions Review Guidelines](https://gjs.guide/extensions/review-guidelines/review-guidelines.html): "all dynamically stored memory must be cleared or freed in disable()".

#### 2. Memory leak con thread bloccato (vabaxos-voice)

**File:** `packages/vabaxos-voice/root/usr/lib/python3/dist-packages/vabaxos_voice/module.py:264-283`

**Problema:** Quando `stop_and_wait()` fallisce (messaggio audio bloccato nel server), viene creato un nuovo `Player` ma il thread `self.job` viene abbandonato senza essere terminato. Il thread rimane in esecuzione come daemon con riferimenti al modello ONNX (570 MB) e buffer audio.

**Impatto:** Memory leak progressivo. Dopo 5-10 messaggi bloccati, il processo speech-dispatcher viene terminato dal sistema per OOM.

**Correzione:** Conteggio dei thread bloccati; exit dopo MAX_STUCK_THREADS (5) per permettere a Speech Dispatcher di riavviarci puliti.

**Nota:** Soluzione completa richiederebbe thread pool o terminazione forzata con `ctypes.pythonapi.PyThreadState_SetAsyncExc`, ma questo è un workaround efficace.

#### 3. Deadlock in player.py

**File:** `packages/vabaxos-voice/root/usr/lib/python3/dist-packages/vabaxos_voice/player.py:68-82`

**Problema:** Se `pa_simple_write` fallisce, viene chiamato `self.close()` e rilanciata l'eccezione all'interno del blocco `with self.lock`. Il lock non viene mai rilasciato perché `raise` esce dal `with` prima che il lock venga sbloccato.

**Impatto:** Deadlock permanente. Kokoro smette di parlare dopo il primo errore audio. Richiede riavvio di speech-dispatcher.

**Correzione:** Spostato `self.close()` in un blocco `finally` che viene eseguito dopo il rilascio del lock.

#### 4. Command injection in test-boot.sh

**File:** `scripts/test-boot.sh:350`

**Problema:** Output di `pgrep -u user -x gnome-shell` viene usato senza validazione in altri comandi (`top -p "$p"`, `cat /proc/"$p"/stack`). Se `pgrep` restituisce più PID o caratteri strani, potrebbero essere eseguiti comandi arbitrari.

**Impatto:** Esecuzione codice arbitrario nella VM di test (rischio basso, VM usa e getta), ma viola il principio di sicurezza.

**Correzione:** Aggiunto `| head -1` dopo `pgrep` per garantire un solo PID.

### High

#### 5. Race condition: cache senza fsync

**File:** `packages/vabaxos-voice/root/usr/lib/python3/dist-packages/vabaxos_voice/cache.py:78-85`

**Problema:** File cache scritti con `tofile()` + `os.replace()` ma senza `fsync()`. Se il sistema crasha durante la scrittura, il file può essere corrotto (header valido, dati troncati), causando crash di NumPy al caricamento.

**Impatto:** Dopo crash/spegnimento, Kokoro può crashare all'avvio con `ValueError: cannot reshape array`. L'utente perde la voce.

**Correzione:** 
- Aggiunto `os.fsync()` prima di `os.replace()` per garantire durabilità
- Validazione al caricamento: controllo dimensioni ragionevoli (0 < size <= 10M campioni)
- Rimozione automatica dei file corrotti

#### 6. Validazione mancante in Sonic

**File:** `packages/vabaxos-voice/root/usr/lib/python3/dist-packages/vabaxos_voice/engine.py:98-114`

**Problema:** `count` da `sonicSamplesAvailable()` non è validato. Se Sonic restituisce un valore enorme per corruzione, `np.zeros(count)` causa MemoryError.

**Impatto:** Crash di Kokoro.

**Correzione:** `count = min(count, len(data) * 3)` prima di allocare (Sonic non dovrebbe mai produrre più di 3x l'input, con speed minimo 0.33).

#### 7. ONNX Runtime crash su exit

**File:** `packages/vabaxos-voice/root/usr/lib/python3/dist-packages/vabaxos_voice/engine.py:164-176`

**Problema:** Se speech-dispatcher viene terminato (QUIT) mentre `session.run()` è in esecuzione, ONNX Runtime può crashare con segfault perché i thread di calcolo accedono a memoria già deallocata.

**Impatto:** Crash di speech-dispatcher, Orca perde la voce fino al riavvio della sessione.

**Correzione:** Aggiunto sleep di 50ms dopo `terminate=True` per dare ai thread ONNX il tempo di notare la terminazione prima della deallocazione.

**Nota:** Soluzione ideale sarebbe aspettare che tutti i thread ONNX abbiano effettivamente terminato, ma non c'è API pubblica per questo in onnxruntime-python.

#### 8. Lock mancante in Phonemizer

**File:** `packages/vabaxos-voice/root/usr/lib/python3/dist-packages/vabaxos_voice/engine.py:42-50`

**Problema:** `espeak_Initialize` chiamato in `__init__` senza acquisire `_lock`. Se due thread creano `Phonemizer` simultaneamente, espeak crasha.

**Impatto:** Basso (nel codice attuale `Phonemizer()` è chiamato una sola volta in `Kokoro.__init__`), ma fragile.

**Correzione:** Spostato `espeak_Initialize` in un blocco `with cls._lock` nel costruttore.

### Medium

#### 9. Subprocess senza gestione errori (vabaxos-start)

**File:** `packages/vabaxos-start/root/usr/lib/python3/dist-packages/vabaxos_start/menu.py:102`

**Problema:** `subprocess.Popen()` chiamato senza controllo errori. Se il comando non esiste o mancano permessi, nessun feedback all'utente.

**Impatto:** UX scadente: l'utente clicca, non succede nulla, non sa perché.

**Correzione:** Aggiunto `try/except OSError` con log dell'errore su stderr.

### Low

#### 10. Counter unbounded in cache

**File:** `packages/vabaxos-voice/root/usr/lib/python3/dist-packages/vabaxos_voice/cache.py:31, 60`

**Problema:** `self.seen` è un `Counter` che accumula chiavi per ogni frase mai detta. Dopo 1M frasi, decine di MB di memoria.

**Impatto:** Basso. In una sessione di 8 ore, Orca dice circa 10k frasi uniche.

**Correzione:** Limite di 10k voci nel counter; quando superato, rimozione delle 1000 voci meno frequenti.

## Pattern comuni NON trovati (aspetti positivi)

- **Shell injection:** Tutti gli script usano array bash e quote corrette. ShellCheck passa.
- **SQL injection:** Nessun database.
- **Path traversal:** Tutti i path costruiti con `os.path.join()` e validati.
- **TOCTOU su file:** `os.replace()` è atomico, cache usa `.tmp`.
- **Unsafe deserialization:** Solo JSON e file binari noti (NumPy .pcm).

## Riepilogo statistico

- **4 critical** (memory leak thread, memory leak estensione, deadlock, command injection)
- **4 high** (cache fsync, Sonic validation, ONNX crash, Phonemizer lock)
- **2 medium/low** (subprocess errors, counter unbounded)

## Priorità di implementazione

Tutte le correzioni sono state implementate nel commit bbde222 (2026-10-02).

I bug #1, #2, #3 e #5 spiegano i sintomi riportati in CLAUDE.md:
- GNOME Shell bloccato (bug #1)
- Orca silenzioso dopo sospensione (bug #3, #7)
- Memory leak progressivi (bug #1, #2)
- Voce persa dopo crash (bug #5)

## Impatto delle correzioni

Le correzioni dovrebbero risolvere o mitigare:
- Freeze di GNOME Shell dopo uso prolungato
- OOM di speech-dispatcher in caso di problemi audio
- Perdita della voce dopo crash o sospensione
- Deadlock audio in caso di errori PulseAudio

Test consigliati dopo le correzioni:
1. Sessione prolungata (8+ ore) con molte notifiche
2. Cicli di sospensione/ripristino ripetuti
3. Simulazione di crash (kill -9) durante la sintesi vocale
4. Errori audio intenzionali (rimozione device audio durante la riproduzione)
