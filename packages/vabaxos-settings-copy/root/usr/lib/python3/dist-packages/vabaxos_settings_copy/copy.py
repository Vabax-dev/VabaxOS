"""A copy of a user's VabaxOS in one file (block 16), to put back on another
computer or after a new installation, and saved by itself every day.

The file is JSON, readable with any text editor, with up to four parts:

- voice: Orca's settings (profiles, keys, programs, pronunciations) and the
  user's speech-dispatcher settings, as files;
- desktop: the user's GNOME settings (dconf dump /), without the ones that
  only describe this computer (window sizes, last folders);
- wifi: the saved Wi-Fi networks, with their passwords;
- programs: the Flatpak applications and the Debian packages the user
  installed, to install again.

The computer is read through a System object, which the tests replace.
"""

import gettext
import glob
import gzip
import json
import os
import re
import subprocess
import time

gettext.textdomain("vabaxos-settings-copy")
_ = gettext.gettext

FORMAT = 1
PARTS = ("voice", "desktop", "wifi", "programs")
# dconf folders that describe only this computer or this moment.
DCONF_SKIP = ("/org/gnome/evolution-data-server/", "/org/gtk/settings/file-chooser/",
              "/org/gtk/gtk4/settings/file-chooser/", "/org/gnome/nautilus/window-state/",
              "/org/gnome/control-center/", "/org/gnome/portal/", "/org/gnome/software/",
              "/org/gnome/shell/extensions/gpaste/", "/org/gnome/desktop/notifications/application/")
DCONF_SKIP_KEYS = ("window-size", "window-width", "window-height", "window-position", "window-state",
                   "window-maximized", "is-maximized", "geometry", "last-folder", "last-panel", "sidebar-width")
FLATHUB = "https://dl.flathub.org/repo/flathub.flatpakrepo"
AUTO_KEPT = 7


class System:

    def output(self, command, timeout=30, stdin=None):
        try:
            result = subprocess.run(command, input=stdin, capture_output=True, text=True, timeout=timeout,
                                    check=False)
        except (OSError, subprocess.TimeoutExpired):
            return None
        return result.stdout if result.returncode == 0 else None

    def run(self, command, timeout=600, stdin=None):
        return self.output(command, timeout, stdin) is not None

    def home(self):
        return os.path.expanduser("~")

    def data_home(self):
        return os.environ.get("XDG_DATA_HOME") or os.path.join(self.home(), ".local", "share")

    def config_home(self):
        return os.environ.get("XDG_CONFIG_HOME") or os.path.join(self.home(), ".config")

    def read_files(self, folder):
        """{relative path: text} of the text files in a folder."""
        files = {}
        for path in sorted(glob.glob(os.path.join(folder, "**", "*"), recursive=True)):
            if not os.path.isfile(path) or os.path.islink(path):
                continue
            try:
                with open(path, encoding="utf-8") as f:
                    files[os.path.relpath(path, folder)] = f.read()
            except (OSError, UnicodeDecodeError):
                continue
        return files

    def write_files(self, folder, files):
        for name, text in files.items():
            path = os.path.normpath(os.path.join(folder, name))
            if not path.startswith(os.path.normpath(folder) + os.sep):
                continue  # never outside the folder (../ in a copy)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path + ".new", "w", encoding="utf-8") as f:
                f.write(text)
            os.replace(path + ".new", path)

    def apt_history(self):
        """The text of APT's history, the old rotated files included."""
        texts = []
        for path in sorted(glob.glob("/var/log/apt/history.log*")):
            try:
                if path.endswith(".gz"):
                    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
                        texts.append(f.read())
                else:
                    with open(path, encoding="utf-8", errors="replace") as f:
                        texts.append(f.read())
            except OSError:
                continue
        return "\n".join(texts)


# -- voice ------------------------------------------------------------------------


def orca_dir(system):
    return os.path.join(system.data_home(), "orca")


def speechd_dir(system):
    return os.path.join(system.config_home(), "speech-dispatcher")


def save_voice(system):
    return {"orca": system.read_files(orca_dir(system)), "speech-dispatcher": system.read_files(speechd_dir(system))}


def restore_voice(system, part):
    system.write_files(orca_dir(system), part.get("orca") or {})
    system.write_files(speechd_dir(system), part.get("speech-dispatcher") or {})
    # Orca reads its settings when it starts.
    if system.output(["pgrep", "-u", str(os.getuid()), "-x", "orca"]) is not None:
        start = "/usr/libexec/vabaxos/orca-start"
        system.run(["systemd-run", "--user", "--collect", "--quiet",
                    start if os.path.exists(start) else "orca", "--replace"])
    return _("Voice and screen reader put back.")


# -- desktop ----------------------------------------------------------------------


def keep_dconf(dump):
    """dconf dump / without the folders and keys of this computer only."""
    kept, folder, keys = [], None, []

    def flush():
        if folder is not None and keys:
            kept.append(f"[{folder}]")
            kept.extend(keys)
            kept.append("")

    for line in dump.splitlines():
        match = re.match(r"^\[(.*)\]$", line)
        if match:
            flush()
            folder, keys = match.group(1), []
            path = "/" + folder.strip("/") + "/"
            if path == "//":
                path = "/"
            if any(path.startswith(skip) for skip in DCONF_SKIP):
                folder = None
            continue
        if folder is None or not line.strip():
            continue
        key = line.split("=", 1)[0]
        if any(part in key for part in DCONF_SKIP_KEYS):
            continue
        keys.append(line)
    flush()
    return "\n".join(kept)


def save_desktop(system):
    dump = system.output(["dconf", "dump", "/"])
    return {"dconf": keep_dconf(dump or "")}


def restore_desktop(system, part):
    if system.run(["dconf", "load", "/"], stdin=part.get("dconf", "")):
        return _("Desktop settings and keys put back.")
    return _("The desktop settings could not be put back.")


# -- Wi-Fi ------------------------------------------------------------------------


def save_wifi(system):
    networks = []
    listing = system.output(["nmcli", "-t", "-e", "no", "-f", "NAME,TYPE", "connection", "show"]) or ""
    for line in listing.splitlines():
        name, _sep, kind = line.rpartition(":")
        if kind != "802-11-wireless" or not name:
            continue
        values = system.output(["nmcli", "-s", "-e", "no", "-g",
                                "802-11-wireless.ssid,802-11-wireless-security.key-mgmt,"
                                "802-11-wireless-security.psk", "connection", "show", name])
        if values is None:
            continue
        fields = (values.splitlines() + ["", "", ""])[:3]
        networks.append({"name": name, "ssid": fields[0], "key-mgmt": fields[1], "psk": fields[2]})
    return {"networks": networks}


def restore_wifi(system, part):
    existing = system.output(["nmcli", "-t", "-e", "no", "-f", "NAME", "connection", "show"]) or ""
    names = set(existing.splitlines())
    added = 0
    for network in part.get("networks") or []:
        if not network.get("ssid") or network.get("name") in names:
            continue
        command = ["nmcli", "connection", "add", "type", "wifi", "con-name", network.get("name") or network["ssid"],
                   "ssid", network["ssid"]]
        if network.get("psk") and network.get("key-mgmt") in ("wpa-psk", "sae"):
            command += ["wifi-sec.key-mgmt", network["key-mgmt"], "wifi-sec.psk", network["psk"]]
        if system.run(command, timeout=60):
            added += 1
    return gettext.ngettext("{n} Wi-Fi network added.", "{n} Wi-Fi networks added.", added).format(n=added)


# -- programs ---------------------------------------------------------------------


def user_packages(history, manual):
    """The Debian packages a person installed (apt with sudo, or PackageKit
    from Software and VabaxOS Programs), still installed and chosen by
    hand: the installer's work has no Requested-By and no PackageKit."""
    found = []
    for entry in history.split("\n\n"):
        if "Requested-By:" not in entry and "packagekit" not in entry.lower():
            continue
        for line in entry.splitlines():
            if not line.startswith("Install:"):
                continue
            # "Install: name:amd64 (1.0), other:amd64 (2.0, automatic)"
            for item in re.findall(r"([a-z0-9][a-z0-9+.-]*)(?::[a-z0-9]+)? \(([^)]*)\)", line[8:]):
                if "automatic" not in item[1] and item[0] in manual and item[0] not in found:
                    found.append(item[0])
    return found


def save_programs(system):
    flatpaks = (system.output(["flatpak", "list", "--app", "--columns=application"]) or "").split()
    manual = set((system.output(["apt-mark", "showmanual"]) or "").split())
    return {"flatpak": sorted(set(flatpaks)), "debian": user_packages(system.apt_history(), manual)}


def restore_programs(system, part):
    installed = set((system.output(["dpkg-query", "-W", "-f=${Package}\\n"]) or "").split())
    debian = [p for p in part.get("debian") or [] if p not in installed and re.fullmatch(r"[a-z0-9][a-z0-9+.-]*", p)]
    have = set((system.output(["flatpak", "list", "--app", "--columns=application"]) or "").split())
    flatpaks = [a for a in part.get("flatpak") or [] if a not in have and re.fullmatch(r"[A-Za-z0-9_.-]+", a)]
    done, failed = 0, 0
    if debian:
        command = (["pkgcli", "--yes", "install", *debian] if system.output(["sh", "-c", "command -v pkgcli"])
                   else ["pkcon", "--noninteractive", "install", *debian])
        if system.run(command, timeout=3600):
            done += len(debian)
        else:
            failed += len(debian)
    if flatpaks:
        system.run(["flatpak", "remote-add", "--user", "--if-not-exists", "flathub", FLATHUB])
        for app in flatpaks:
            if system.run(["flatpak", "install", "--user", "-y", "--noninteractive", "flathub", app], timeout=3600):
                done += 1
            else:
                failed += 1
    if failed:
        return _("{done} programs installed, {failed} not installed.").format(done=done, failed=failed)
    return gettext.ngettext("{n} program installed.", "{n} programs installed.", done).format(n=done)


# -- the copy ---------------------------------------------------------------------

SAVE = {"voice": save_voice, "desktop": save_desktop, "wifi": save_wifi, "programs": save_programs}
RESTORE = {"voice": restore_voice, "desktop": restore_desktop, "wifi": restore_wifi,
           "programs": restore_programs}


def make(parts=PARTS, system=None):
    system = system or System()
    copy = {"vabaxos-settings-copy": FORMAT, "created": time.strftime("%Y-%m-%d %H:%M"),
            "computer": (system.output(["hostname"]) or "").strip()}
    for part in parts:
        copy[part] = SAVE[part](system)
    return copy


def write(path, copy):
    """Writes the copy readable only by its owner: it may hold Wi-Fi
    passwords."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    fd = os.open(path + ".new", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(copy, f, indent=1, ensure_ascii=False)
    os.replace(path + ".new", path)


def read(path):
    """The copy in a file, or None when it is not a VabaxOS copy."""
    try:
        with open(path, encoding="utf-8") as f:
            copy = json.load(f)
    except (OSError, ValueError):
        return None
    if not isinstance(copy, dict) or copy.get("vabaxos-settings-copy") != FORMAT:
        return None
    return copy


def parts_in(copy):
    return [part for part in PARTS if isinstance(copy.get(part), dict)]


def restore(copy, parts=PARTS, system=None):
    """Puts the chosen parts back; one sentence for each."""
    system = system or System()
    return [RESTORE[part](system, copy[part]) for part in parts if isinstance(copy.get(part), dict)]


def auto_dir(system=None):
    system = system or System()
    return os.path.join(system.data_home(), "vabaxos", "settings-copies")


def auto_copies(system=None):
    """The automatic copies, newest first."""
    return sorted(glob.glob(os.path.join(auto_dir(system), "*.json")), reverse=True)


def auto_save(system=None):
    """The daily copy (vabaxos-settings-copy.timer): voice, desktop and
    programs, without Wi-Fi passwords; the last few are kept."""
    system = system or System()
    path = os.path.join(auto_dir(system), time.strftime("%Y-%m-%d") + ".json")
    write(path, make(("voice", "desktop", "programs"), system))
    for old in auto_copies(system)[AUTO_KEPT:]:
        os.remove(old)
    return path
