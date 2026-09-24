# image/

Configurazione della ISO per live-build ([ADR-0002](../docs/decisions/0002-build-live-build.md)). Non si usa direttamente: `scripts/build.sh` la copia nella cartella di lavoro `build/` e costruisce da lì (vedi [BUILD.md](../BUILD.md)).

| File o cartella | Contenuto |
|---|---|
| `build.conf` | Versione di Debian e data dello snapshot di snapshot.debian.org |
| `auto/config` | Opzioni di `lb config`: mirror, avvio, parametri del kernel |
| `config/package-lists/` | Pacchetti del sistema live, un file `.list.chroot` per argomento |
| `config/archives/` | Impostazioni di APT durante la costruzione |
| `config/bootloaders/grub-pc/` | File del menu di avvio GRUB (UEFI e BIOS) che sostituiscono quelli di live-build |
| `config/hooks/normal/` | Script eseguiti nel chroot durante la costruzione |
| `config/rootfs/excludes` | File da non mettere nello squashfs (schemi di `mksquashfs -ef`, uno per riga, senza commenti) |

## Scelte della ISO minima

- Avvio con GRUB sia in UEFI sia in BIOS, con la catena firmata di Debian per Secure Boot (ADR-0003).
- Il menu di avvio emette il segnale acustico di live-build e parte da solo dopo 10 secondi. Il menu parlante completo arriva con il lavoro 4 della v0.1 (ADR-0014).
- Il sistema live si chiama `vabaxos`. L'utente è `user`, con password `live` (valori di live-config).
- Il kernel scrive anche sulla prima porta seriale (`console=ttyS0`), dove compare una richiesta di accesso: serve ai test di avvio senza schermo. La console principale resta lo schermo (`console=tty0`), che il lettore di schermo leggerà.
- Niente firmware non libero e niente installer, per ora: arrivano con i lavori 9 e 11.
- Niente indici di APT nella ISO (`--apt-indices false`) e niente cache di APT nello squashfs (`config/rootfs/excludes`): live-build li scarica da deb.debian.org durante la costruzione, quindi cambierebbero ogni giorno e la ISO non sarebbe riproducibile. Nel sistema live si esegue `apt update` prima di installare.

## File presi da live-build

Questi file vengono da live-build 20250505 (Debian, GPL-3.0-or-later), come indicato in `REUSE.toml`:

- `config/hooks/normal/*reproducible*` e `*cleanup*`: gli hook che Debian consiglia per le immagini live riproducibili (`/usr/share/doc/live-build/examples/hooks/reproducible/`). Sono copiati nel repository perché nel container della CI la documentazione dei pacchetti non viene installata.
- `config/bootloaders/grub-pc/config.cfg`: copia del file di live-build, con in più il tempo di attesa.

Quando si aggiorna live-build, questi file vanno confrontati con i nuovi.
