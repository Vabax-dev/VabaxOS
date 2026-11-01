"""The updates of every kind, in one list: system packages (PackageKit),
applications (Flatpak) and firmware (fwupd).

Pure functions here, so they are tested without PackageKit, Flatpak or
fwupd (tests/update).
"""

import json
import shutil
import subprocess

SECURITY, SYSTEM, APPS, FIRMWARE = "security", "system", "apps", "firmware"
KINDS = (SECURITY, SYSTEM, APPS, FIRMWARE)

# Packages whose update changes the desktop or the voice while they run:
# installed during the session they can leave the user without speech
# until the next start. For these the update at the next start is advised.
CRITICAL = ("gnome-shell", "mutter", "orca", "speech-dispatcher", "espeak-ng", "libespeak-ng",
            "espeakup", "pipewire", "wireplumber", "gdm3", "at-spi2", "libatk", "libgtk-4",
            "libgtk-3", "linux-image", "systemd", "brltty", "libpulse", "dbus", "vabaxos-")


class Update:
    """One thing to update."""

    def __init__(self, name, version="", kind=SYSTEM, summary="", ident=""):
        self.name = name
        self.version = version
        self.kind = kind
        self.summary = summary
        self.ident = ident or name

    def __repr__(self):
        return f"Update({self.kind}, {self.name} {self.version})"

    @property
    def critical(self):
        return self.kind in (SECURITY, SYSTEM) and any(self.name.startswith(c) for c in CRITICAL)


def package_name(package_id):
    """'openssl;3.5.1-1;amd64;debian' -> 'openssl'."""
    return package_id.split(";", 1)[0]


def package_version(package_id):
    parts = package_id.split(";")
    return parts[1] if len(parts) > 1 else ""


def from_packagekit(packages, security_info):
    """PackageKit packages as updates; security ones apart."""
    updates = []
    for package in packages:
        ident = package.get_id()
        kind = SECURITY if package.get_info() == security_info else SYSTEM
        summary = package.get_summary() if hasattr(package, "get_summary") else ""
        updates.append(Update(package_name(ident), package_version(ident), kind, summary or "", ident))
    return updates


def run_text(command):
    if not shutil.which(command[0]):
        return ""
    try:
        return subprocess.run(command, capture_output=True, text=True, check=False, timeout=120).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def parse_flatpak(text):
    """Lines 'application<TAB>name<TAB>version' of flatpak remote-ls."""
    updates = []
    for line in text.splitlines():
        cells = line.split("\t")
        if not cells or not cells[0].strip():
            continue
        app = cells[0].strip()
        name = cells[1].strip() if len(cells) > 1 and cells[1].strip() else app
        version = cells[2].strip() if len(cells) > 2 else ""
        updates.append(Update(name, version, APPS, app, app))
    return updates


def flatpak_updates(run=run_text):
    return parse_flatpak(run(["flatpak", "remote-ls", "--updates", "--columns=application,name,version"]))


def parse_fwupd(text):
    """fwupdmgr get-updates --json: one update for each device."""
    try:
        data = json.loads(text) if text.strip() else {}
    except ValueError:
        return []
    updates = []
    for device in data.get("Devices", []):
        releases = device.get("Releases") or []
        if not releases:
            continue
        name = device.get("Name") or device.get("DeviceId", "")
        release = releases[0]
        updates.append(Update(name, release.get("Version", ""), FIRMWARE,
                              release.get("Summary", ""), device.get("DeviceId", name)))
    return updates


def firmware_updates(run=run_text):
    return parse_fwupd(run(["fwupdmgr", "get-updates", "--json", "--no-unreported-check",
                            "--no-metadata-check"]))


def count(updates, kind):
    return sum(1 for u in updates if u.kind == kind)


def critical(updates):
    """The names of the updates that change the desktop or the voice."""
    return sorted({u.name for u in updates if u.critical})
