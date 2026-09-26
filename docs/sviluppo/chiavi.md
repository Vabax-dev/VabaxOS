# Le chiavi di VabaxOS

VabaxOS ha due chiavi OpenPGP (ADR-0020, decisione di Vabax del 2026-09-26):

- **la chiave dell'archivio** firma l'archivio APT di VabaxOS su GitHub Pages. La usa la CI, quindi non ha passphrase. La parte segreta sta solo nel segreto `VABAXOS_ARCHIVE_KEY` di GitHub Actions e nel portachiavi di Vabax (`~/.gnupg`);
- **la chiave delle versioni** firma `SHA256SUMS` delle ISO ufficiali. Ha una passphrase e sta solo sul computer di Vabax.

Le parti pubbliche vanno in `keys/` (vedi [keys/README.md](../../keys/README.md)). **La passphrase e le parti segrete non passano mai dalla chat né dal repository.**

## 1. Creare la chiave dell'archivio

Nella finestra di Debian, nella cartella del repository:

```bash
bash scripts/crea-chiavi.sh archivio
```

Crea la chiave, scrive la parte pubblica in `keys/vabaxos-archive.asc` e copia la parte segreta negli appunti di Windows. Non stampa mai la parte segreta.

## 2. Mettere la chiave segreta su GitHub

Subito dopo, con la chiave negli appunti:

1. apri <https://github.com/Vabax-dev/VabaxOS/settings/secrets/actions/new>;
2. nel campo «Name» scrivi `VABAXOS_ARCHIVE_KEY`;
3. nel campo «Secret» incolla (Ctrl+V);
4. premi «Add secret».

Poi copia qualcos'altro, per togliere la chiave dagli appunti.

## 3. Attivare GitHub Pages

1. apri <https://github.com/Vabax-dev/VabaxOS/settings/pages>;
2. in «Source» scegli «GitHub Actions».

## 4. Pubblicare la chiave pubblica

La chiave pubblica entra nel repository con un commit, come ogni altro file:

```bash
git switch -c keys/archive && git add keys/vabaxos-archive.asc && git commit -s -m "feat(keys): VabaxOS archive public key" && git push -u origin keys/archive
```

Da quel momento, a ogni unione su `main` la CI `archive.yml` pubblica l'archivio firmato, e il pacchetto `vabaxos-apt` aggiunge l'archivio di VabaxOS alle fonti di APT.

Ordine da rispettare: prima il segreto e Pages (punti 2 e 3), poi la chiave pubblica (punto 4). Una ISO costruita con la chiave pubblica ma senza archivio pubblicato non riuscirebbe ad aggiornare le liste di APT.

## 5. La chiave delle versioni

```bash
bash scripts/crea-chiavi.sh versioni
```

GnuPG chiede la passphrase due volte, nel terminale. Sceglila lunga e conservala: senza, non si possono firmare le versioni. La parte pubblica va in `keys/vabaxos-release.asc`, con un commit come al punto 4.

Conviene anche una copia di sicurezza del portachiavi (`~/.gnupg`) su una chiavetta che resta a casa.

## Se una chiave si perde o viene rubata

- **Chiave dell'archivio:** si crea una chiave nuova, si cambia il segreto, e una versione di `vabaxos-apt` firmata ancora con la vecchia porta la chiave nuova. Se la vecchia è stata rubata, serve una ISO nuova.
- **Chiave delle versioni:** si crea una chiave nuova, la si pubblica e le versioni successive si firmano con quella. Le versioni già uscite restano verificabili con la vecchia chiave pubblica.
