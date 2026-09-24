# VabaxOS — Build System & Base Distribution Decision

| Campo | Valore |
|---|---|
| ID | VABAX-DOC-06 |
| Versione | 0.1.0 |
| Stato | Decision record in bozza — **nessuna base o build system selezionata** |
| Data | 2026-09-23 |
| Ambito | Criteri, alternative e processo per scegliere base e generazione immagini |
| Dipendenze | Roadmap originale, Windows Development Environment, DOC-03/04/05/07 |

## 1. Scopo

La roadmap originale richiede una decisione sulla base userspace (Debian/Ubuntu-like o indipendente) e sul build system (Debian live-build o pipeline personalizzata), senza averli ancora selezionati. Questo documento fornisce una matrice decisionale e un piano di prova, non un verdetto. La distro base e il framework di build sono decisioni distinte, anche se interdipendenti.

## 2. Obiettivi e vincoli proposti

### Stato delle scelte nella roadmap

La roadmap già propone Linux kernel, systemd, Wayland/XWayland, AT-SPI2, PipeWire/WirePlumber, NetworkManager, x86-64, boot UEFI, ext4 iniziale, pacchetti nativi + Flatpak, systemd-boot con GRUB da valutare, e Calamares fortemente personalizzato oppure installer Vabax. Non sono tutti decisioni ADR definitive. Prima della v0.1 la roadmap richiede una decisione specifica su: base userspace Debian/Ubuntu-like o indipendente; live-build Debian o pipeline personalizzata; inoltre installer, desktop, screen reader, TTS, packaging, filesystem e boot manager. Per questo documento la **base e il build system sono ancora TBD**, mentre gli altri nomi sono candidati/proposte preliminari.


- Ottenere una ISO Live x86-64 avviabile in QEMU come obiettivo v0.1 stabilito dalla roadmap.
- Rendere AT/TTS e desktop accessibili disponibili nel flusso di boot e sessione.
- Gestire un ecosistema Linux applicativo ampio, driver e firmware ragionevolmente aggiornati, sicurezza e manutenzione sostenibili.
- Generare artefatti identificabili, con manifest, versioni e verifiche di integrità; puntare alla riproducibilità e misurarla.
- Tenere sviluppo accessibile su workstation Windows/WSL2 come indicato dalla guida, ma consentire toolchain/build Linux nativi in CI. Compatibilità specifica WSL/QEMU va verificata.
- Non impegnare un prodotto indipendente, un kernel personalizzato o una release commerciale prima che siano dimostrati necessari.

## 3. Alternative da confrontare

La prima valutazione deve considerare in modo prioritario la strada Debian/Ubuntu-like + Debian Live/live-build per il prototipo, perché la roadmap la cita direttamente, e confrontarla con una pipeline Vabax personalizzata e una base indipendente. Fedora e Arch possono essere benchmark secondari, non sono opzioni esplicitamente selezionate nella roadmap. Buildroot è descritto dalla roadmap come orientato soprattutto all'embedded e non scelta desktop predefinita; Yocto è un riferimento futuro possibile per ARM/dispositivi e aumenta la complessità desktop iniziale.


### Famiglie di base

1. **Debian stable** — base generale; valutare disponibilità versioni, politiche pacchetti, immagini live e supporto hardware.
2. **Ubuntu LTS** — ecosistema e documentazione ampi; confrontare release/ciclo, componenti e vincoli di personalizzazione.
3. **Fedora** — software e stack recenti; valutare cadenza aggiornamenti, manutenzione e requisiti AT.
4. **Arch/rolling** — aggiornamento rapido e grande flessibilità; valutare carico operativo, regressioni e supporto utenti.
5. **Base indipendente** — controllo massimo e costo massimo; richiede motivazione, infrastruttura, sicurezza, pacchetti, release e team di manutenzione.

L'elenco è esplorativo, non esaustivo né endorsement. Stato attuale delle versioni e dei cicli va controllato nelle fonti ufficiali al momento della decisione.

### Sistemi di costruzione

1. **Debian Live / live-build** — candidato naturale per ISO live basata su Debian; verificare personalizzazione, installer, accessibilità del boot e manutenzione.
2. **mkosi** — candidate per costruzione immagini di sistema basate su distribuzioni supportate; valutare output e integrazione.
3. **Buildroot** — orientato a sistemi Linux embedded e immagini rootfs; confrontare adeguatezza a desktop general-purpose e software esistente.
4. **Yocto Project** — framework flessibile per distribuzioni/embedded; valutare complessità, recipe, manutentori e costo per obiettivo desktop.
5. **Tooling distro-native o composable OS** — includere nella ricerca aggiornata; confrontare aggiornamenti, rollback, firma e immagine installabile.

Non si assume che una sola alternativa copra bootstrap, aggiornamento e installazione; una combinazione può essere valutata se il costo è documentato.

## 4. Criteri di valutazione

Scala proposta: 1 = debole, 3 = adeguato con limiti, 5 = forte; punteggio vuoto finché prove e pesi non sono approvati. Il punteggio finale è comparativo, non sostituisce le soglie bloccanti.

| Criterio | Peso iniziale | Evidenza richiesta |
|---|---:|---|
| Boot, live image e installazione accessibili | 20% | prototipo UEFI VM, tastiera/AT, recovery |
| Compatibilità software e disponibilità pacchetti | 15% | inventario di applicazioni target e test installazione |
| Accessibilità del desktop, display e input | 15% | PoC AT su sessione e flussi A0 |
| Ciclo di supporto e manutenzione sicurezza | 15% | policy ufficiale, durata, update e responsabilità |
| Build ripetibile, tracciabilità e automazione | 10% | due build, manifest e confronto artefatti |
| Driver/firmware e hardware target | 10% | matrice QEMU e campione hardware |
| Aggiornamento, rollback e recovery | 5% | prova riuscita e prova di interruzione |
| Licenze e redistribuzione | 5% | inventario componenti, obblighi e firmware |
| Costo di competenze/complessità operativa | 5% | stima documentata e manutentori disponibili |

I pesi sono **proposti**; il team deve approvarli prima di usare un totale numerico. Soglie bloccanti: accessibilità A0 non dimostrata; aggiornamenti di sicurezza non sostenibili; redistribuzione non chiara; artefatti non attribuibili a sorgenti/versioni.

## 5. Piano di valutazione riproducibile

1. Confermare roadmap originale, release iniziale, target CPU/firmware e flussi utente.
2. Congelare versioni di prova e configurazioni per ciascuna alternativa; annotare data di ricerca e fonti upstream.
3. Costruire un prototipo minimo: boot UEFI in QEMU, lingua selezionabile, sessione grafica, avvio AT/TTS, tastiera, log accessibile o esportabile.
4. Provare installazione live/immagine, aggiornamento e recovery; interrompere deliberatamente un'operazione in VM e verificare recupero.
5. Verificare applicazioni target (browser, terminale, file manager, audio, toolkit) e due applicazioni legacy rappresentative.
6. Eseguire due build pulite dello stesso manifest in ambiente documentato; confrontare hash o spiegare timestamp/fonti di non-determinismo.
7. Generare SBOM/inventario componenti e licenze; verificare firmware, codecs, repository e redistribuzione.
8. Compilare punteggi con prove collegate; pubblicare ADR motivato, alternative respinte, rischi, owner e condizioni di riesame.

## 6. Dipendenze e criteri d'accettazione decisionale

Dipende dalla disponibilità dei target hardware, dal desktop/compositor e stack AT scelti, dalle lingue e applicazioni prioritarie, dal team di manutenzione, dalle esigenze di gaming, dalla strategia update e da vincoli di licenza. Le versioni upstream sono mutevoli: annotare data e usare documentazione ufficiale aggiornata.

**Una decisione è accettabile soltanto se:** (a) requisiti e pesi sono approvati; (b) almeno le alternative plausibili per ciascuna dimensione sono confrontate; (c) esiste immagine avviabile con flusso A0 dimostrato; (d) update/recovery e tracciabilità sono provati; (e) licenze e supporto sono controllati; (f) ADR dichiara rischi, costi, owner e trigger di riesame. Finché non soddisfatto, la decisione rimane **TBD**.

## 7. Fonti ufficiali da usare nella valutazione

- [Debian Live project](https://www.debian.org/devel/debian-live/) — descrizione framework e immagini ufficiali.
- [Debian Live images](https://www.debian.org/CD/live/) — caratteristiche delle immagini live ufficiali; non implica che siano la base Vabax.
- [Documentazione systemd e mkosi](https://systemd.io/) — mkosi compare tra i progetti/documenti correlati; verificare documentazione propria prima della scelta.
- [Buildroot documentation](https://buildroot.org/docs.html) — documentazione ufficiale progetto.
- [Yocto Project documentation](https://docs.yoctoproject.org/) — documentazione ufficiale.
- [Ubuntu release cycle](https://ubuntu.com/about/release-cycle) — verificare il supporto dichiarato.
- [Fedora release life cycle](https://docs.fedoraproject.org/en-US/releases/lifecycle/) — verificare ciclo e supporto.
- [Arch Linux official installation guide](https://wiki.archlinux.org/title/Installation_guide) — documentazione ufficiale della community; valutare manutenzione rolling.
- [Linux kernel documentation](https://docs.kernel.org/) — supporto tecnico e licenze kernel.

## 8. Allineamento all'ambiente di sviluppo Windows

La guida Windows conferma Windows 11 come workstation, WSL2 con Ubuntu 24.04 LTS come ambiente Linux per build, Git/GitHub e repository nel filesystem Linux di WSL, VS Code Remote WSL e QEMU come laboratorio principale. Il build principale deve essere eseguito dentro WSL; ciò non determina la base userspace dell'ISO VabaxOS. La guida prevede ISO `VabaxOS-x86_64.iso` e test di boot QEMU, mentre la roadmap richiede anche un PC fisico compatibile per v0.1.

## 9. Registro decisioni

| Decisione | Stato | Owner | Evidenza richiesta |
|---|---|---|---|
| Distro base / release | TBD prima di v0.1; Debian/Ubuntu-like è alternativa esplicita prioritaria da valutare | Architect/Project Lead | matrice e PoC |
| Framework build ISO | TBD prima di v0.1; Debian live-build contro pipeline Vabax personalizzata | Principal Software Engineer | prototipo ripetibile |
| Strategia pacchetti/update/rollback | TBD | Architect + Engineering | prova update/recovery |
| Architettura CPU v0.1 | proposta x86-64 da confermare | Project Lead | roadmap e target validati |
| Base ARM64 e timing | aperto, visione successiva in preview | Project Lead | roadmap, hardware e capacità team |

## 10. Riferimenti alla documentazione di progetto

- `VabaxOS_Roadmap_v0.1-v1.0.txt`, bozza tecnica v0.1 del 23 settembre 2026: obiettivi v0.1, risorse open source, scelte architetturali preliminari e sezione “Decisioni da prendere prima della v0.1”.
- `VabaxOS_Windows_Development_Environment.txt`, versione 1.0 del 23 settembre 2026: workstation e workflow Linux/WSL/QEMU.

## 11. Cronologia

- 0.1.0 (2026-09-23): prima bozza decisionale; nessun prodotto o framework approvato.
