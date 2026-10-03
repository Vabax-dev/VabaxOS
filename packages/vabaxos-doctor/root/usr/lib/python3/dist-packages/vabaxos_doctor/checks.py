"""The checks of VabaxOS Doctor (block 16): what a blind user needs, in the
order it is needed: sound, speech, the screen reader, console speech, the
emergency key, then network, firewall, disk, memory, updates, services.

Every check returns a Result: a state (ok, warning, problem), one short
sentence for the screen reader and, when VabaxOS can put it right, the name
of a fix. The computer is read through a System object, which the tests
replace (tests/doctor/test_doctor.py).
"""

import gettext
import json
import os
import shutil
import subprocess
from dataclasses import dataclass

gettext.textdomain("vabaxos-doctor")
_ = gettext.gettext

OK, WARNING, PROBLEM = "ok", "warning", "problem"
VOLUME_LOW = 0.4
DISK_PROBLEM_MB = 1024
DISK_WARNING_RATIO = 0.10
MEMORY_WARNING_MB = 300
RESCUE = "/usr/libexec/vabaxos/voice-rescue"
ORCA_START = "/usr/libexec/vabaxos/orca-start"


@dataclass
class Result:
    ident: str
    title: str
    state: str
    message: str
    fix: str = ""

    def line(self):
        word = {OK: _("OK"), WARNING: _("Warning"), PROBLEM: _("Problem")}[self.state]
        return f"{word}: {self.title}: {self.message}"


class System:
    """The computer, as the checks and fixes see it."""

    def output(self, command, timeout=5):
        """The output of a command, or None when it fails or takes too long."""
        try:
            result = subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                                    timeout=timeout, check=False)
        except (OSError, subprocess.TimeoutExpired):
            return None
        return result.stdout if result.returncode == 0 else None

    def run(self, command, timeout=60):
        return self.output(command, timeout) is not None

    def read(self, path):
        try:
            with open(path, encoding="utf-8") as f:
                return f.read()
        except OSError:
            return None

    def exists(self, path):
        return os.path.exists(path)

    def disk(self, path):
        """(free MB, total MB) of the file system of path."""
        usage = shutil.disk_usage(path)
        return usage.free // 2**20, usage.total // 2**20

    def home(self):
        return os.path.expanduser("~")


def setting(text, key):
    for line in (text or "").splitlines():
        if line.startswith(key + ":"):
            return line.split(":", 1)[1].strip()
    return ""


# -- the checks -------------------------------------------------------------------


def sound_card(system):
    cards = system.read("/proc/asound/cards") or ""
    if "no soundcards" in cards or not cards.strip():
        return Result("sound-card", _("Sound card"), PROBLEM,
                      _("No sound card found: the computer cannot speak. Try headphones or another USB "
                        "sound card."))
    count = sum(1 for line in cards.splitlines() if line[:3].strip().isdigit())
    return Result("sound-card", _("Sound card"), OK,
                  gettext.ngettext("{count} sound card.", "{count} sound cards.", count).format(count=count))


def sound(system):
    volume = system.output(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"], timeout=4)
    if volume is None:
        return Result("sound", _("Sound"), PROBLEM, _("The sound server does not answer."), "sound")
    try:
        level = float(volume.split()[1])
    except (IndexError, ValueError):
        return Result("sound", _("Sound"), WARNING, _("No sound output."), "sound")
    percent = round(level * 100)
    if "MUTED" in volume:
        return Result("sound", _("Sound"), PROBLEM, _("The sound is muted."), "sound")
    if level < VOLUME_LOW:
        return Result("sound", _("Sound"), WARNING,
                      _("The volume is low, {percent} percent.").format(percent=percent), "sound")
    return Result("sound", _("Sound"), OK, _("Volume {percent} percent.").format(percent=percent))


def speech(system):
    modules = system.output(["spd-say", "-O"], timeout=6)
    if modules is None:
        return Result("speech", _("Speech"), PROBLEM, _("The speech service does not answer."), "speech")
    names = [line.strip() for line in modules.splitlines()[1:] if line.strip()]
    if "espeak-ng" not in names:
        return Result("speech", _("Speech"), PROBLEM, _("eSpeak NG is missing from the speech service."))
    module = "espeak-ng"
    for line in (system.read("/etc/speech-dispatcher/clients/zz-vabaxos-voice.conf") or "").splitlines():
        if line.startswith("DefaultModule"):
            module = line.split()[-1]
    voice = _("Natural voice (Kokoro)") if module == "kokoro" else "eSpeak NG"
    return Result("speech", _("Speech"), OK, _("The speech service answers; voice: {voice}.").format(voice=voice))


def orca_settings(system):
    text = system.read(os.path.join(system.home(), ".local", "share", "orca", "user-settings.conf"))
    try:
        data = json.loads(text) if text else {}
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def screen_reader(system):
    enabled = (system.output(["gsettings", "get", "org.gnome.desktop.a11y.applications",
                              "screen-reader-enabled"]) or "").strip()
    if enabled != "true":
        return Result("screen-reader", _("Screen reader"), WARNING,
                      _("Orca is off. Super+Alt+S turns it on."), "orca")
    if system.output(["pgrep", "-u", str(os.getuid()), "-x", "orca"]) is None:
        return Result("screen-reader", _("Screen reader"), PROBLEM, _("Orca is on but not running."), "orca")
    data = orca_settings(system)
    groups = [data.get("general") or {}] + list((data.get("profiles") or {}).values())
    if any(isinstance(g, dict) and g.get("enableSpeech") is False for g in groups):
        return Result("screen-reader", _("Screen reader"), PROBLEM,
                      _("Orca's speech is turned off in its settings."), "orca-speech")
    return Result("screen-reader", _("Screen reader"), OK, _("Orca is running."))


def console_speech(system):
    if system.output(["systemctl", "is-active", "espeakup.service"]) is None:
        return Result("console-speech", _("Console speech"), WARNING,
                      _("The text console does not speak."), "console-speech")
    return Result("console-speech", _("Console speech"), OK, _("The text console speaks."))


def emergency_key(system):
    if system.output(["systemctl", "is-active", "triggerhappy.service", "vabaxos-voice-rescue.path"]) is None:
        return Result("emergency-key", _("Emergency key"), WARNING,
                      _("Ctrl+Super+Enter would not bring the voice back."), "emergency-key")
    return Result("emergency-key", _("Emergency key"), OK, _("Ctrl+Super+Enter brings the voice back."))


def network(system):
    state = (system.output(["nmcli", "-t", "-f", "CONNECTIVITY", "general"]) or "").strip()
    if state == "full":
        return Result("network", _("Network"), OK, _("Connected to the Internet."))
    if state == "portal":
        return Result("network", _("Network"), WARNING,
                      _("The network asks to sign in, as in a hotel: open the web browser."))
    if state in ("limited", "none"):
        return Result("network", _("Network"), WARNING,
                      _("No Internet. Connect from the system menu, or with nmtui in the terminal."))
    return Result("network", _("Network"), WARNING, _("The network state is unknown."))


def firewall(system):
    if system.output(["systemctl", "is-active", "ufw.service"]) is None:
        return Result("firewall", _("Firewall"), WARNING, _("The firewall is off."), "firewall")
    return Result("firewall", _("Firewall"), OK, _("The firewall is on."))


def disk(system):
    """The system disk and the home folder, when it is on another disk:
    the fuller of the two."""
    places = [("/", _("Disk"))]
    try:
        if system.disk(system.home()) != system.disk("/"):
            places.append((system.home(), _("Home folder")))
    except OSError:
        pass
    results = []
    for path, title in places:
        try:
            free, total = system.disk(path)
        except OSError:
            continue
        free_gb = f"{free / 1024:.1f}"
        if free < DISK_PROBLEM_MB:
            results.append(Result("disk", title, PROBLEM, _("Almost full: {free} GB free.").format(free=free_gb),
                                  "trash"))
        elif total and free < total * DISK_WARNING_RATIO:
            results.append(Result("disk", title, WARNING, _("Little space: {free} GB free.").format(free=free_gb),
                                  "trash"))
        else:
            results.append(Result("disk", title, OK, _("{free} GB free.").format(free=free_gb)))
    if not results:
        return Result("disk", _("Disk"), WARNING, _("The free space is unknown."))
    return min(results, key=lambda r: {PROBLEM: 0, WARNING: 1, OK: 2}[r.state])


def memory(system):
    for line in (system.read("/proc/meminfo") or "").splitlines():
        if line.startswith("MemAvailable:"):
            available = int(line.split()[1]) // 1024
            if available < MEMORY_WARNING_MB:
                return Result("memory", _("Memory"), WARNING,
                              _("Little free memory, {mb} MB: close some programs.").format(mb=available))
            return Result("memory", _("Memory"), OK, _("{mb} MB free.").format(mb=available))
    return Result("memory", _("Memory"), WARNING, _("The free memory is unknown."))


def updates(system):
    if system.exists("/run/reboot-required"):
        return Result("updates", _("Updates"), WARNING,
                      _("Updates were installed: restart the computer to use them."))
    return Result("updates", _("Updates"), OK, _("No restart needed."))


def services(system):
    failed = []
    for command in (["systemctl", "--failed", "--no-legend", "--plain"],
                    ["systemctl", "--user", "--failed", "--no-legend", "--plain"]):
        for line in (system.output(command) or "").splitlines():
            if line.split():
                failed.append(line.split()[0].removesuffix(".service"))
    if failed:
        return Result("services", _("Services"), WARNING,
                      _("Stopped with an error: {names}. vabaxctl report saves the details.")
                      .format(names=", ".join(failed)))
    return Result("services", _("Services"), OK, _("No service stopped with an error."))


CHECKS = (sound_card, sound, speech, screen_reader, console_speech, emergency_key, network, firewall,
          disk, memory, updates, services)


def run_checks(system=None):
    system = system or System()
    return [check(system) for check in CHECKS]


def summary(results):
    problems = sum(1 for r in results if r.state == PROBLEM)
    warnings = sum(1 for r in results if r.state == WARNING)
    if not problems and not warnings:
        return _("Everything works.")
    parts = []
    if problems:
        parts.append(gettext.ngettext("{n} problem", "{n} problems", problems).format(n=problems))
    if warnings:
        parts.append(gettext.ngettext("{n} warning", "{n} warnings", warnings).format(n=warnings))
    return ", ".join(parts) + "."


# -- the fixes --------------------------------------------------------------------


def fix(name, system=None):
    """Puts one thing right; True when the command worked. The user's own
    services are started again directly, the system's through pkexec,
    which asks the administrator password in a window Orca reads."""
    system = system or System()
    uid = str(os.getuid())
    if name == "sound":
        system.run(["systemctl", "--user", "restart", "pipewire.socket", "pipewire.service",
                    "pipewire-pulse.socket", "pipewire-pulse.service", "wireplumber.service"], timeout=20)
        system.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "0"])
        volume = system.output(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"]) or ""
        try:
            low = float(volume.split()[1]) < VOLUME_LOW
        except (IndexError, ValueError):
            low = False
        return not low or system.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "0.5"])
    if name == "speech":
        system.run(["pkill", "-u", uid, "-x", "speech-dispatcher"])
        system.run(["pkill", "-u", uid, "^sd_"])
        return system.run(["spd-say", "-w", _("Speech is back.")], timeout=20)
    if name == "orca":
        system.run(["gsettings", "set", "org.gnome.desktop.a11y.applications", "screen-reader-enabled",
                    "true"])
        if system.output(["pgrep", "-u", uid, "-x", "orca"]) is not None:
            return True
        return system.run(["systemd-run", "--user", "--collect", "--quiet", ORCA_START, "--replace"])
    if name == "orca-speech":
        return system.run([RESCUE, "--orca-settings"]) and \
            system.run(["systemd-run", "--user", "--collect", "--quiet", ORCA_START, "--replace"])
    if name == "console-speech":
        return system.run(["pkexec", "systemctl", "restart", "espeakup.service"], timeout=120)
    if name == "emergency-key":
        return system.run(["pkexec", "systemctl", "enable", "--now", "triggerhappy.service",
                           "vabaxos-voice-rescue.path"], timeout=120)
    if name == "firewall":
        return system.run(["pkexec", "ufw", "--force", "enable"], timeout=120)
    if name == "trash":
        return system.run(["gio", "trash", "--empty"], timeout=60)
    return False
