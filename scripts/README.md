# scripts/

Script di sviluppo (vedi [BUILD.md](../BUILD.md)):

| Script | Cosa fa |
|---|---|
| `check-deps.sh` | Controlla che l'ambiente abbia tutto il necessario |
| `build.sh` | Costruisce la ISO in `out/` |
| `run-qemu.sh` | Avvia la ISO in QEMU con UEFI e audio |
| `test-boot.sh` | Test di avvio automatico senza schermo, dalla console seriale |

La cartella `postazione/` contiene la preparazione della postazione Windows: `prepara-windows.ps1` (avviato da `1-prepara-windows.cmd`), `prepara-debian.sh`, `verifica-postazione.sh` e l'elenco `pacchetti-debian.txt`. Vedi la [guida](../docs/sviluppo/postazione-windows.md).

Gli script sono in Bash e vengono controllati con ShellCheck.
