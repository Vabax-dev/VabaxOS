"""VabaxOS Doctor - Sistema di diagnostica automatica dell'accessibilità.

Controlla che tutti i componenti di accessibilità funzionino correttamente:
- Audio (PipeWire, PulseAudio, scheda audio)
- Sintesi vocale (speech-dispatcher, Kokoro, eSpeak NG)
- Lettore di schermo (Orca, AT-SPI)
- Estensioni GNOME Shell
- Risorse di sistema (RAM, CPU, disco)
- Rete

Ogni controllo restituisce: OK, WARNING, ERROR o SKIPPED.
"""

import os
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Status(Enum):
    """Stato di un controllo diagnostico."""
    OK = "OK"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"


@dataclass
class CheckResult:
    """Risultato di un controllo diagnostico."""
    name: str
    status: Status
    message: str
    details: Optional[str] = None
    fix_command: Optional[str] = None


class Doctor:
    """Sistema di diagnostica di VabaxOS."""

    def __init__(self):
        self.results = []
        self.is_live = self._check_live_system()

    def _check_live_system(self):
        """Verifica se siamo in modalità live."""
        return os.path.exists("/lib/live/mount/medium")

    def _run(self, command, timeout=5):
        """Esegue un comando e restituisce (returncode, stdout, stderr)."""
        try:
            result = subprocess.run(
                command,
                shell=isinstance(command, str),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "timeout"
        except Exception as e:
            return -1, "", str(e)

    def check_audio_device(self):
        """Controlla che esista almeno una scheda audio."""
        code, out, _ = self._run(["aplay", "-l"])
        if code == 0 and "card" in out.lower():
            cards = [line for line in out.split("\n") if line.startswith("card")]
            return CheckResult(
                "Scheda audio",
                Status.OK,
                f"Trovate {len(cards)} schede audio",
                details=out.strip()
            )
        return CheckResult(
            "Scheda audio",
            Status.ERROR,
            "Nessuna scheda audio trovata",
            fix_command="Verifica che i driver audio siano caricati: lsmod | grep snd"
        )

    def check_pipewire(self):
        """Controlla che PipeWire sia attivo."""
        code, out, _ = self._run(["systemctl", "--user", "is-active", "pipewire.service"])
        if code == 0 and "active" in out:
            # Controlla anche wireplumber
            code2, out2, _ = self._run(["systemctl", "--user", "is-active", "wireplumber.service"])
            if code2 == 0 and "active" in out2:
                return CheckResult(
                    "PipeWire",
                    Status.OK,
                    "PipeWire e WirePlumber attivi"
                )
            return CheckResult(
                "PipeWire",
                Status.WARNING,
                "PipeWire attivo ma WirePlumber non risponde",
                fix_command="systemctl --user restart wireplumber.service"
            )
        return CheckResult(
            "PipeWire",
            Status.ERROR,
            "PipeWire non attivo",
            fix_command="systemctl --user start pipewire.service"
        )

    def check_pulseaudio_socket(self):
        """Controlla che PipeWire esponga il socket PulseAudio."""
        pulse_socket = os.path.expanduser("~/.pulse/native")
        runtime_dir = os.environ.get("XDG_RUNTIME_DIR", "/run/user/1000")
        pipewire_pulse = f"{runtime_dir}/pulse/native"

        if os.path.exists(pipewire_pulse) or os.path.exists(pulse_socket):
            return CheckResult(
                "Socket PulseAudio",
                Status.OK,
                "Socket PulseAudio disponibile"
            )
        return CheckResult(
            "Socket PulseAudio",
            Status.ERROR,
            "Socket PulseAudio non trovato",
            details="La sintesi vocale potrebbe non funzionare",
            fix_command="systemctl --user restart pipewire-pulse.service"
        )

    def check_speech_dispatcher(self):
        """Controlla che speech-dispatcher sia attivo."""
        code, out, _ = self._run(["systemctl", "--user", "is-active", "speech-dispatcher.service"])
        if code == 0 and "active" in out:
            # Prova a mandare un messaggio di test
            test_code, _, _ = self._run(
                'echo "speak\n test \n." | spd-say -w',
                timeout=3
            )
            if test_code == 0:
                return CheckResult(
                    "Speech Dispatcher",
                    Status.OK,
                    "Speech Dispatcher attivo e funzionante"
                )
            return CheckResult(
                "Speech Dispatcher",
                Status.WARNING,
                "Speech Dispatcher attivo ma non risponde",
                fix_command="systemctl --user restart speech-dispatcher.service"
            )
        return CheckResult(
            "Speech Dispatcher",
            Status.ERROR,
            "Speech Dispatcher non attivo",
            fix_command="systemctl --user start speech-dispatcher.service"
        )

    def check_kokoro(self):
        """Controlla se Kokoro è disponibile e funzionante."""
        # Verifica se il modulo è installato
        code, _, _ = self._run(["python3", "-c", "import vabaxos_voice.engine"])
        if code != 0:
            return CheckResult(
                "Kokoro",
                Status.SKIPPED,
                "Modulo vabaxos-voice non installato"
            )

        # Verifica se i file del modello esistono
        data_dir = "/usr/share/vabaxos-voice"
        model_file = os.path.join(data_dir, "kokoro-v1.0.onnx")
        if not os.path.exists(model_file):
            return CheckResult(
                "Kokoro",
                Status.ERROR,
                "File del modello Kokoro non trovato",
                details=f"Manca: {model_file}",
                fix_command="sudo apt install --reinstall vabaxos-voice"
            )

        # Controlla RAM disponibile
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemAvailable:"):
                        mem_kb = int(line.split()[1])
                        mem_mb = mem_kb / 1024
                        if mem_mb < 2048:  # Kokoro richiede ~600 MB + sistema
                            return CheckResult(
                                "Kokoro",
                                Status.WARNING,
                                f"RAM disponibile bassa: {mem_mb:.0f} MB",
                                details="Kokoro potrebbe non caricarsi"
                            )
                        break
        except Exception:
            pass

        return CheckResult(
            "Kokoro",
            Status.OK,
            "Kokoro installato correttamente"
        )

    def check_espeak(self):
        """Controlla che eSpeak NG funzioni."""
        code, _, _ = self._run(["espeak-ng", "--version"])
        if code == 0:
            # Prova a sintetizzare
            test_code, _, _ = self._run(
                ['espeak-ng', '-v', 'it', 'test'],
                timeout=2
            )
            if test_code == 0:
                return CheckResult(
                    "eSpeak NG",
                    Status.OK,
                    "eSpeak NG funzionante"
                )
            return CheckResult(
                "eSpeak NG",
                Status.WARNING,
                "eSpeak NG installato ma la sintesi fallisce"
            )
        return CheckResult(
            "eSpeak NG",
            Status.ERROR,
            "eSpeak NG non installato",
            fix_command="sudo apt install espeak-ng"
        )

    def check_orca(self):
        """Controlla che Orca sia attivo."""
        code, out, _ = self._run(["pgrep", "-u", os.getenv("USER"), "-x", "orca"])
        if code == 0 and out.strip():
            # Orca è in esecuzione
            return CheckResult(
                "Orca",
                Status.OK,
                f"Orca attivo (PID: {out.strip()})"
            )

        # Controlla se è abilitato all'avvio
        code, out, _ = self._run([
            "gsettings", "get",
            "org.gnome.desktop.a11y.applications", "screen-reader-enabled"
        ])
        if code == 0 and "true" in out:
            return CheckResult(
                "Orca",
                Status.WARNING,
                "Orca abilitato ma non in esecuzione",
                fix_command="Riavvia la sessione o esegui: orca --replace &"
            )

        return CheckResult(
            "Orca",
            Status.WARNING,
            "Orca non abilitato",
            details="Il lettore di schermo non si avvierà automaticamente",
            fix_command="gsettings set org.gnome.desktop.a11y.applications screen-reader-enabled true"
        )

    def check_atspi(self):
        """Controlla che il bus AT-SPI funzioni."""
        code, out, _ = self._run([
            "dbus-send", "--session", "--print-reply",
            "--dest=org.a11y.Bus", "/org/a11y/bus",
            "org.freedesktop.DBus.Properties.Get",
            "string:org.a11y.Bus", "string:IsEnabled"
        ])
        if code == 0:
            return CheckResult(
                "AT-SPI",
                Status.OK,
                "Bus AT-SPI disponibile"
            )
        return CheckResult(
            "AT-SPI",
            Status.ERROR,
            "Bus AT-SPI non disponibile",
            details="Orca non potrà leggere le applicazioni"
        )

    def check_gnome_extensions(self):
        """Controlla le estensioni GNOME Shell di VabaxOS."""
        extensions = [
            "button-names@vabaxos.org",
            "vabaxos-keys@vabaxos.org"
        ]

        errors = []
        warnings = []

        for ext in extensions:
            code, out, _ = self._run([
                "gnome-extensions", "info", ext
            ])
            if code != 0:
                warnings.append(f"{ext}: non installata")
                continue

            # Controlla se è abilitata
            code, out, _ = self._run([
                "gnome-extensions", "list", "--enabled"
            ])
            if code == 0 and ext not in out:
                warnings.append(f"{ext}: disabilitata")

        if errors:
            return CheckResult(
                "Estensioni GNOME",
                Status.ERROR,
                f"{len(errors)} estensioni con errori",
                details="\n".join(errors)
            )
        if warnings:
            return CheckResult(
                "Estensioni GNOME",
                Status.WARNING,
                f"{len(warnings)} estensioni non attive",
                details="\n".join(warnings),
                fix_command="Riavvia GNOME Shell: Alt+F2, r, Invio"
            )

        return CheckResult(
            "Estensioni GNOME",
            Status.OK,
            f"{len(extensions)} estensioni attive"
        )

    def check_memory(self):
        """Controlla la RAM disponibile."""
        try:
            with open("/proc/meminfo") as f:
                mem_total = mem_available = 0
                for line in f:
                    if line.startswith("MemTotal:"):
                        mem_total = int(line.split()[1]) / 1024  # MB
                    elif line.startswith("MemAvailable:"):
                        mem_available = int(line.split()[1]) / 1024  # MB

                percent = (mem_available / mem_total * 100) if mem_total > 0 else 0

                if mem_available < 512:
                    return CheckResult(
                        "Memoria RAM",
                        Status.ERROR,
                        f"RAM critica: {mem_available:.0f} MB liberi su {mem_total:.0f} MB",
                        details="Il sistema potrebbe rallentare o crashare"
                    )
                elif mem_available < 1024:
                    return CheckResult(
                        "Memoria RAM",
                        Status.WARNING,
                        f"RAM bassa: {mem_available:.0f} MB liberi su {mem_total:.0f} MB",
                        details="Considera di chiudere programmi non necessari"
                    )

                return CheckResult(
                    "Memoria RAM",
                    Status.OK,
                    f"{mem_available:.0f} MB liberi su {mem_total:.0f} MB ({percent:.0f}%)"
                )
        except Exception as e:
            return CheckResult(
                "Memoria RAM",
                Status.ERROR,
                f"Impossibile leggere /proc/meminfo: {e}"
            )

    def check_disk(self):
        """Controlla lo spazio su disco."""
        code, out, _ = self._run(["df", "-h", "/"])
        if code == 0:
            lines = out.strip().split("\n")
            if len(lines) >= 2:
                fields = lines[1].split()
                if len(fields) >= 5:
                    use_percent = fields[4].rstrip("%")
                    available = fields[3]

                    try:
                        percent = int(use_percent)
                        if percent >= 95:
                            return CheckResult(
                                "Spazio disco",
                                Status.ERROR,
                                f"Disco quasi pieno: {percent}% usato ({available} liberi)"
                            )
                        elif percent >= 85:
                            return CheckResult(
                                "Spazio disco",
                                Status.WARNING,
                                f"Spazio disco basso: {percent}% usato ({available} liberi)"
                            )

                        return CheckResult(
                            "Spazio disco",
                            Status.OK,
                            f"{percent}% usato ({available} liberi)"
                        )
                    except ValueError:
                        pass

        return CheckResult(
            "Spazio disco",
            Status.WARNING,
            "Impossibile determinare lo spazio disco"
        )

    def check_network(self):
        """Controlla la connessione di rete."""
        # Ping a 1.1.1.1 (Cloudflare DNS)
        code, _, _ = self._run(["ping", "-c", "1", "-W", "2", "1.1.1.1"])
        if code == 0:
            # Prova anche un hostname
            code2, _, _ = self._run(["ping", "-c", "1", "-W", "3", "deb.debian.org"])
            if code2 == 0:
                return CheckResult(
                    "Rete",
                    Status.OK,
                    "Connessione Internet funzionante"
                )
            return CheckResult(
                "Rete",
                Status.WARNING,
                "Connessione presente ma DNS potrebbero non funzionare"
            )

        return CheckResult(
            "Rete",
            Status.WARNING,
            "Nessuna connessione Internet",
            details="Gli aggiornamenti non saranno disponibili"
        )

    def run_all_checks(self):
        """Esegue tutti i controlli diagnostici."""
        checks = [
            self.check_audio_device,
            self.check_pipewire,
            self.check_pulseaudio_socket,
            self.check_speech_dispatcher,
            self.check_espeak,
            self.check_kokoro,
            self.check_orca,
            self.check_atspi,
            self.check_gnome_extensions,
            self.check_memory,
            self.check_disk,
            self.check_network,
        ]

        self.results = []
        for check in checks:
            try:
                result = check()
                self.results.append(result)
            except Exception as e:
                self.results.append(CheckResult(
                    check.__name__.replace("check_", "").replace("_", " ").title(),
                    Status.ERROR,
                    f"Errore durante il controllo: {e}"
                ))

        return self.results

    def get_summary(self):
        """Restituisce un riepilogo dei risultati."""
        ok = sum(1 for r in self.results if r.status == Status.OK)
        warnings = sum(1 for r in self.results if r.status == Status.WARNING)
        errors = sum(1 for r in self.results if r.status == Status.ERROR)
        skipped = sum(1 for r in self.results if r.status == Status.SKIPPED)

        return {
            "total": len(self.results),
            "ok": ok,
            "warnings": warnings,
            "errors": errors,
            "skipped": skipped
        }
