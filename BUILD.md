# Costruire VabaxOS

Questa pagina spiega come si costruisce la ISO di VabaxOS e come si prova in una macchina virtuale, secondo [ADR-0002](docs/decisions/0002-build-live-build.md) e [ADR-0013](docs/decisions/0013-ambiente-di-sviluppo.md).

> **Stato:** la ISO è ancora minima. Si avvia in UEFI, con Secure Boot e in BIOS, e arriva a una console testuale. Voce, desktop e installer arrivano con i prossimi lavori della v0.1 (vedi [ROADMAP.md](ROADMAP.md)).

## Cosa serve

- Un sistema **Debian 13** amd64: su Windows è la distribuzione Debian di WSL2, in CI il container `debian:trixie`.
- I privilegi di amministratore, perché live-build lavora in un chroot. Lo script chiama `sudo /usr/bin/lb`: sulla postazione si può permettere solo quel comando senza password (vedi la [guida alla postazione](docs/sviluppo/postazione-windows.md)).
- Circa 20 GB liberi e una connessione a Internet per scaricare i pacchetti.

## I comandi

```bash
./scripts/check-deps.sh   # controlla che ci sia tutto il necessario
./scripts/build.sh        # costruisce la ISO in out/
./scripts/run-qemu.sh     # avvia la ISO in una macchina virtuale con audio
./scripts/test-boot.sh    # prova l'avvio senza schermo, dalla console seriale
```

Sulla postazione di sviluppo la prima costruzione scarica qualche centinaio di MB e dura circa 7 minuti; le successive riusano i pacchetti già scaricati e durano circa 6 minuti. La ISO minima pesa circa 280 MB. Alla fine, sulla postazione, una voce dice se la costruzione è riuscita o fallita.

## Cosa produce

Tutto va nella cartella `out/`, che Git ignora:

| File | Contenuto |
|---|---|
| `VabaxOS-<versione>-amd64.iso` | L'immagine da avviare in QEMU o da scrivere su una chiavetta |
| `SHA256SUMS` | Checksum per verificare l'immagine |
| `manifest.txt` | Commit Git, data dello snapshot Debian, versione di live-build, kernel, checksum dello squashfs, elenco dei pacchetti con versione |
| `logs/build-AAAA-MM-GG-HHMMSS.log` | Log completo della costruzione, mai sovrascritto |

Ogni costruzione sostituisce la ISO, `SHA256SUMS` e `manifest.txt` precedenti. I log restano.

Il nome della ISO segue [ADR-0015](docs/decisions/0015-versioni-e-rilasci.md):

- di solito è `VabaxOS-nightly-AAAAMMGG-<commit>-amd64.iso`;
- con la variabile `VABAXOS_VERSION` diventa il nome di una versione, per esempio `VABAXOS_VERSION=0.1.0-alpha.1 ./scripts/build.sh` produce `VabaxOS-0.1.0-alpha.1-amd64.iso`.

## Provare la ISO

`./scripts/run-qemu.sh` avvia la ISO di `out/` in QEMU, in UEFI, con la scheda audio e l'altoparlante del PC collegati all'audio della postazione. Opzioni utili:

- `--secure-boot`: UEFI con Secure Boot attivo e le chiavi Microsoft, come un PC venduto oggi;
- `--bios`: avvio in modalità BIOS;
- `--headless`: senza finestra;
- `--help`: tutte le opzioni.

La prima porta seriale della macchina virtuale finisce in `out/logs/qemu-serial-<data>.log`: lì si leggono i messaggi del kernel e la richiesta di accesso, senza guardare lo schermo.

`./scripts/test-boot.sh` fa la stessa prova in automatico: avvia la ISO senza finestra, aspetta la richiesta di accesso sulla console seriale, entra come utente live (`user`, password `live`), controlla il tipo di firmware, lo stato di Secure Boot e di systemd, poi spegne la macchina. Accetta `--secure-boot` e `--bios`. Il log va in `out/logs/test-boot-<modalità>-<data>.log`.

## Come è fatta la configurazione

- `image/build.conf`: la versione di Debian e la **data dello snapshot**.
- `image/auto/config`: le opzioni di live-build (`lb config`).
- `image/config/`: elenchi di pacchetti, hook, file per il menu di avvio. Vedi [image/README.md](image/README.md).

`scripts/build.sh` copia `image/` nella cartella di lavoro `build/` (ignorata da Git), esegue `lb config` e `lb build`, poi copia i risultati in `out/`. `./scripts/build.sh --config-only` esegue solo `lb config` in una cartella temporanea, senza privilegi: la CI lo usa per controllare la configurazione.

## Riproducibilità

I pacchetti vengono da snapshot.debian.org alla data fissata in `image/build.conf`. Tutte le date dei file nella ISO sono quella dello snapshot (`SOURCE_DATE_EPOCH`), e gli hook di riproducibilità di Debian sono in `image/config/hooks/normal/`.

Due costruzioni dallo stesso commit devono produrre lo stesso filesystem della ISO: il confronto si fa con la riga `squashfs-sha256` del manifest. Se non succede è un difetto da segnalare.

Stato al 2026-09-24: due costruzioni consecutive sulla postazione hanno dato lo stesso squashfs. Una ricostruzione indipendente, su un'altra macchina, non è ancora stata fatta.

Per ricevere gli aggiornamenti di Debian si cambia la data dello snapshot, in un commit a parte.
