# Chiavi pubbliche di VabaxOS

Qui ci sono solo chiavi **pubbliche** OpenPGP (ADR-0020). Le chiavi segrete non entrano mai nel repository.

- `vabaxos-archive.asc`: la chiave dell'archivio APT di VabaxOS. Firma l'archivio pubblicato su GitHub Pages (`scripts/build-archive.sh`, CI `archive.yml`). La sua parte segreta è solo nel segreto `VABAXOS_ARCHIVE_KEY` di GitHub Actions. Il pacchetto `vabaxos-apt` la installa come `/usr/share/keyrings/vabaxos-archive-keyring.asc`; senza questo file `vabaxos-apt` non aggiunge l'archivio di VabaxOS alle fonti di APT.
- `vabaxos-release.asc`: la chiave delle versioni ufficiali. Firma `SHA256SUMS` delle ISO pubblicate. La sua parte segreta è solo sul computer di Vabax.

Come si creano le due chiavi è spiegato in [docs/sviluppo/chiavi.md](../docs/sviluppo/chiavi.md).
