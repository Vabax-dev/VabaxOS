# Verificare la ISO di VabaxOS

Prima di installare VabaxOS conviene controllare che la ISO scaricata sia quella pubblicata dal progetto e che non si sia rovinata durante lo scaricamento. Servono tre file, nella stessa cartella:

- la ISO, per esempio `VabaxOS-0.1.0-alpha.1-amd64.iso`;
- `SHA256SUMS`: l'impronta di ogni file;
- `SHA256SUMS.sign`: la firma di `SHA256SUMS`, fatta con la chiave del progetto ([ADR-0015](../decisions/0015-versioni-e-rilasci.md), [ADR-0026](../decisions/0026-archivio-apt-e-chiave.md)).

La verifica ha due passi: la firma dice che `SHA256SUMS` viene da VabaxOS; l'impronta dice che la ISO è quella elencata in `SHA256SUMS`.

## L'impronta della chiave

La chiave pubblica del progetto è `keys/vabaxos-project.asc` nel repository. La sua impronta è pubblicata nel README e su vabax.it: deve essere la stessa in tutti e due i posti. Si legge a gruppi di quattro caratteri, come la scrive `gpg`.

## Da Linux (anche da VabaxOS)

Tutti i comandi si scrivono nel terminale, nella cartella dei file scaricati. Ogni comando risponde con una riga di testo, che Orca legge.

Primo passo: scarica la chiave del progetto e importala.

```bash
gpg --import vabaxos-project.asc
```

Secondo passo: controlla la firma. La risposta giusta contiene «Good signature from "VabaxOS Project Signing Key"»; se c'è «BAD signature», non usare la ISO.

```bash
gpg --verify SHA256SUMS.sign SHA256SUMS
```

Terzo passo: controlla l'impronta della ISO. La risposta giusta è il nome della ISO seguito da «OK».

```bash
sha256sum --check --ignore-missing SHA256SUMS
```

`gpg` può aggiungere un avviso che la chiave «non è certificata con una firma fidata»: vuol dire solo che non l'hai firmata tu. Confronta l'impronta mostrata con quella pubblicata.

## Da Windows

Con PowerShell si controlla l'impronta; per la firma serve Gpg4win (programma libero), che ha lo stesso comando `gpg`.

Primo passo: apri PowerShell nella cartella dei file scaricati.

Secondo passo: cerca l'impronta della ISO in `SHA256SUMS`. Il comando calcola l'impronta e risponde con la riga della ISO se la trova; se non risponde niente, la ISO non è quella giusta.

```powershell
Select-String -Path .\SHA256SUMS -Pattern (Get-FileHash .\VabaxOS-0.1.0-alpha.1-amd64.iso).Hash
```

Terzo passo, con Gpg4win installato: la firma si controlla come su Linux.

```powershell
gpg --import vabaxos-project.asc
```

```powershell
gpg --verify SHA256SUMS.sign SHA256SUMS
```

Sostituisci il nome della ISO con quello che hai scaricato.
