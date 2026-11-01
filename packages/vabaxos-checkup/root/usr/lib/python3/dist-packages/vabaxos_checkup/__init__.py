"""The check of the computer: what it has and whether it works for VabaxOS,
in sentences (Vabax, 2026-11-02: at the first start, the sound card, the
Wi-Fi, the battery, the Braille display, said aloud).

Every check reads through Probe, so the tests give made-up answers.

    run_checks(probe)    [Item], in the order of importance for a blind user
    summary(items)       one sentence for the voice
"""

import gettext
import glob
import json
import os
import shutil
import subprocess
from dataclasses import dataclass

_translation = gettext.translation("vabaxos-checkup", fallback=True)
_ = _translation.gettext
ngettext = _translation.ngettext

OK, NOTE, WARN, PROBLEM = "ok", "note", "warn", "problem"
LOW_MEMORY_MB = 4000          # below: the desktop and Orca become slow
NATURAL_MEMORY_MB = 8000      # the natural voice and the descriptions want this
LOW_DISK = 5 * 1000 ** 3
WORN_BATTERY = 60             # percent of the original capacity


@dataclass
class Item:
    key: str
    area: str
    state: str
    sentence: str

    def text(self):
        return f"{self.area}: {self.sentence}"


class Probe:
    """Reads the computer. The tests replace run(), read() and the paths."""

    def __init__(self, root="/"):
        self.root = root

    def path(self, *parts):
        return os.path.join(self.root, *[p.lstrip("/") for p in parts])

    def run(self, *command, timeout=10):
        try:
            done = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False,
                                  env=dict(os.environ, LC_ALL="C.UTF-8"))
        except (OSError, subprocess.TimeoutExpired):
            return None
        return done.stdout if done.returncode == 0 else None

    def read(self, *parts):
        try:
            with open(self.path(*parts), encoding="utf-8", errors="replace") as f:
                return f.read().strip()
        except OSError:
            return None

    def glob(self, pattern):
        """Paths matching pattern, relative to the root, for read()."""
        return sorted(os.path.relpath(p, self.root) for p in glob.glob(self.path(pattern)))

    def disk(self, path="/"):
        try:
            usage = shutil.disk_usage(path)
        except OSError:
            return None
        return usage.free, usage.total

    def braille_display(self):
        """(driver, cells) through BrlAPI, or None."""
        try:
            import brlapi
            connection = brlapi.Connection()
        except Exception:  # noqa: BLE001 - no daemon, no key, no display
            return None
        try:
            return connection.driverName, connection.displaySize[0]
        finally:
            connection.closeConnection()


def _json(text):
    try:
        return json.loads(text) if text else None
    except ValueError:
        return None


def _volume(sink):
    levels = []
    for channel in (sink.get("volume") or {}).values():
        try:
            levels.append(int(str(channel.get("value_percent", "0")).rstrip("%")))
        except (ValueError, AttributeError):
            pass
    return max(levels) if levels else None


def check_audio(probe):
    sinks = _json(probe.run("pactl", "-f", "json", "list", "sinks"))
    if sinks is None:
        return Item("audio", _("Sound"), PROBLEM, _("the sound server does not answer: speech may be silent."))
    real = [s for s in sinks if "auto_null" not in s.get("name", "")]
    if not real:
        return Item("audio", _("Sound"), PROBLEM, _("no sound card found: VabaxOS cannot speak from the desktop."))
    default = (probe.run("pactl", "get-default-sink") or "").strip()
    sink = next((s for s in real if s.get("name") == default), real[0])
    name = sink.get("description") or sink.get("name")
    volume = _volume(sink)
    if sink.get("mute"):
        return Item("audio", _("Sound"), WARN, _("{card}, but muted.").format(card=name))
    if volume is not None and volume < 20:
        return Item("audio", _("Sound"), WARN, _("{card}, volume very low: {volume} percent.").format(
            card=name, volume=volume))
    return Item("audio", _("Sound"), OK, _("{card}, it works.").format(card=name))


def check_microphone(probe):
    sources = _json(probe.run("pactl", "-f", "json", "list", "sources"))
    if sources is None:
        return Item("microphone", _("Microphone"), NOTE, _("cannot be read."))
    real = [s for s in sources if not s.get("name", "").endswith(".monitor")
            and (s.get("properties") or {}).get("device.class") != "monitor"]
    if not real:
        return Item("microphone", _("Microphone"), NOTE, _("none: dictation and video calls need one."))
    return Item("microphone", _("Microphone"), OK, real[0].get("description") or real[0].get("name"))


def check_network(probe):
    out = probe.run("nmcli", "-t", "-f", "TYPE,STATE,CONNECTION", "device")
    if out is None:
        return Item("network", _("Network"), NOTE, _("NetworkManager does not answer."))
    devices = [line.replace("\\:", "\x00").split(":") for line in out.splitlines() if line]
    devices = [[part.replace("\x00", ":") for part in d] for d in devices]
    wifi = [d for d in devices if d[0] == "wifi"]
    cable = [d for d in devices if d[0] == "ethernet"]
    connected = [d for d in wifi + cable if len(d) > 2 and d[1].startswith("connected")]
    if wifi and connected and connected[0][0] == "wifi":
        return Item("network", _("Network"), OK, _("Wi-Fi connected to {network}.").format(network=connected[0][2]))
    if connected:
        extra = _(" There is Wi-Fi too.") if wifi else ""
        return Item("network", _("Network"), OK, _("connected by cable.") + extra)
    if wifi:
        return Item("network", _("Network"), NOTE, _("Wi-Fi present, not connected: open Wi-Fi and Bluetooth "
                                                      "in the Start menu."))
    if cable:
        return Item("network", _("Network"), WARN, _("only a cable socket, no Wi-Fi card: connect the cable."))
    return Item("network", _("Network"), WARN, _("no network card found."))


def check_bluetooth(probe):
    if not probe.glob("sys/class/bluetooth/hci*"):
        return Item("bluetooth", _("Bluetooth"), NOTE, _("none."))
    show = probe.run("bluetoothctl", "show") or ""
    if "Powered: yes" in show:
        return Item("bluetooth", _("Bluetooth"), OK, _("present and on: Super+K pairs headphones and Braille "
                                                       "displays."))
    return Item("bluetooth", _("Bluetooth"), OK, _("present, off: Super+K turns it on."))


def check_battery(probe):
    batteries = probe.glob("sys/class/power_supply/BAT*")
    if not batteries:
        return Item("battery", _("Battery"), NOTE, _("none: a desktop computer, on mains power."))
    battery = batteries[0]
    level = probe.read(battery, "capacity") or "?"
    status = probe.read(battery, "status") or ""
    state = {"Charging": _("charging"), "Discharging": _("on battery"), "Full": _("full"),
             "Not charging": _("plugged in, not charging")}.get(status, status.lower())
    sentence = _("{level} percent, {state}.").format(level=level, state=state)
    full = probe.read(battery, "energy_full") or probe.read(battery, "charge_full")
    design = probe.read(battery, "energy_full_design") or probe.read(battery, "charge_full_design")
    try:
        health = round(int(full) * 100 / int(design))
    except (TypeError, ValueError, ZeroDivisionError):
        health = None
    if health is not None and health < WORN_BATTERY:
        return Item("battery", _("Battery"), WARN, sentence + " " + _(
            "It is worn: it holds {health} percent of the charge it held when new.").format(health=health))
    if health is not None:
        sentence += " " + _("It holds {health} percent of the charge it held when new.").format(health=min(health, 100))
    return Item("battery", _("Battery"), OK, sentence)


def check_braille(probe):
    found = probe.braille_display()
    if found:
        driver, cells = found
        return Item("braille", _("Braille"), OK, _("display connected, {cells} cells ({driver}).").format(
            cells=cells, driver=driver))
    return Item("braille", _("Braille"), NOTE, _("no display connected. If you have one: connect it by USB, or "
                                                 "pair it with Super+K; then the command vabaxos-braille-check."))


def check_camera(probe):
    names = []
    for device in probe.glob("sys/class/video4linux/video*"):
        name = probe.read(device, "name")
        index = probe.read(device, "index")
        if name and index in (None, "0") and name not in names:
            names.append(name)
    if not names:
        return Item("camera", _("Camera"), NOTE, _("none: reading with the camera needs a webcam."))
    return Item("camera", _("Camera"), OK, ", ".join(names) + ".")


def check_memory(probe):
    meminfo = probe.read("proc/meminfo") or ""
    total = next((int(line.split()[1]) // 1024 for line in meminfo.splitlines() if line.startswith("MemTotal:")), 0)
    gigabytes = round(total / 1024)
    if total and total < LOW_MEMORY_MB:
        return Item("memory", _("Memory"), WARN, _("{gb} GB: few, the desktop may be slow.").format(gb=gigabytes))
    if total and total < NATURAL_MEMORY_MB:
        return Item("memory", _("Memory"), OK, _("{gb} GB: enough; the natural voice and the descriptions of "
                                                 "pictures want 8.").format(gb=gigabytes))
    return Item("memory", _("Memory"), OK, _("{gb} GB.").format(gb=gigabytes))


def check_disk(probe):
    usage = probe.disk("/")
    if usage is None:
        return Item("disk", _("Disk"), NOTE, _("cannot be read."))
    free, _total = usage
    gb = round(free / 1000 ** 3)
    if free < LOW_DISK:
        return Item("disk", _("Disk"), WARN, _("only {gb} GB free.").format(gb=gb))
    return Item("disk", _("Disk"), OK, _("{gb} GB free.").format(gb=gb))


CHECKS = (check_audio, check_network, check_battery, check_braille, check_bluetooth, check_microphone,
          check_camera, check_memory, check_disk)


def run_checks(probe=None):
    probe = probe or Probe()
    items = []
    for check in CHECKS:
        try:
            items.append(check(probe))
        except Exception as error:  # noqa: BLE001 - one check never stops the others
            items.append(Item(check.__name__[6:], check.__name__[6:], NOTE, str(error)))
    return items


def problems(items):
    return [i for i in items if i.state in (WARN, PROBLEM)]


def summary(items):
    """One sentence: what works, then what to look at."""
    bad = problems(items)
    if not bad:
        return _("Check of the computer: everything is fine.") + " " + " ".join(
            i.text() for i in items if i.key in ("audio", "network", "battery", "braille"))
    return ngettext("Check of the computer: one thing to look at.", "Check of the computer: {count} things to "
                    "look at.", len(bad)).format(count=len(bad)) + " " + " ".join(i.text() for i in bad)
