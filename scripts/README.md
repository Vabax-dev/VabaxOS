# scripts/

Script di sviluppo. Previsti per la v0.1 (vedi [BUILD.md](../BUILD.md)):

| Script | Cosa fa |
|---|---|
| `check-deps.sh` | Controlla che l'ambiente abbia tutto il necessario |
| `build.sh` | Costruisce la ISO in `out/` |
| `run-qemu.sh` | Avvia la ISO in QEMU con UEFI e audio |
| `test-boot.sh` | Test di avvio automatico, senza interfaccia |

Gli script sono in Bash e vengono controllati con ShellCheck.
