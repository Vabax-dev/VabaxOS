"""The program store of VabaxOS: search, install, open and remove programs
from Debian (AppStream and PackageKit, the same pieces as GNOME Software)
and, when the user turns it on, from Flathub (ADR-0008: Flathub can be
activated by the user; installed for the user only, no password).

Pure functions here (the answers of appstreamcli and flatpak read as
text), so they are tested without those programs.

    search(query, flathub)      [App], Debian first, then Flathub
    installed(app)              True or False
"""

import gettext
import json
import os
import re
import subprocess
from dataclasses import dataclass, field

_ = gettext.translation("vabaxos-store", fallback=True).gettext

FLATHUB = "https://dl.flathub.org/repo/flathub.flatpakrepo"
# Removing these would leave the computer without voice, desktop or updates
# (the same list as vabaxos-apps).
PROTECTED = ("orca", "gnome-shell", "gnome-control-center", "gnome-session", "nautilus", "gdm3",
             "speech-dispatcher", "espeak-ng", "espeakup", "brltty", "packagekit", "gnome-software",
             "network-manager", "pipewire", "wireplumber", "at-spi2-core", "vabaxos-")
KINDS = ("desktop-application", "console-application", "web-application")


@dataclass
class App:
    id: str
    name: str
    summary: str = ""
    source: str = "debian"      # "debian" or "flathub"
    package: str = ""           # the Debian package, or the Flatpak application
    kind: str = "desktop-application"
    homepage: str = ""
    installed: bool = False
    extra: dict = field(default_factory=dict)

    def describe(self):
        """'Audacity, records and edits sounds, from Debian, installed'."""
        parts = [self.name]
        if self.summary:
            parts.append(self.summary.rstrip("."))
        parts.append(_("from Flathub") if self.source == "flathub" else _("from Debian"))
        if self.installed:
            parts.append(_("installed"))
        return ", ".join(parts)

    @property
    def protected(self):
        return self.source == "debian" and self.package.startswith(PROTECTED)


def run_text(command, timeout=120):
    """The output of a command, in the user's language: appstreamcli and
    flatpak give names and descriptions translated (their keys stay in
    English)."""
    try:
        done = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""
    return done.stdout


# -- Debian, through AppStream ----------------------------------------------

def parse_appstream(text, owner=None):
    """The text of 'appstreamcli search --details': blocks separated by
    '---', lines 'Key: value', long values on the following indented lines.
    Programs already installed come from their own metainfo, without
    'Package': owner(desktop id) finds their package, or they are left out."""
    apps = []
    for block in re.split(r"^---\s*$", text, flags=re.M):
        fields, key = {}, None
        for line in block.splitlines():
            if not line.strip():
                continue
            if line.startswith((" ", "\t")) and key:
                fields[key] = (fields[key] + " " + line.strip()).strip()
                continue
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                fields[key] = value.strip()
        identifier = fields.get("Identifier", "")
        match = re.match(r"(\S+)(?:\s+\[([\w-]+)\])?", identifier)
        if not match:
            continue
        ident, kind = match.group(1), match.group(2) or "desktop-application"
        if kind not in KINDS:
            continue    # add-ons, fonts, drivers
        package = fields.get("Package", "").split()[:1]
        if not package and owner and kind == "desktop-application":
            package = [owner(ident)] if owner(ident) else []
        if not package:
            continue    # the web apps of GNOME Software have no package
        description = fields.get("Description", "")
        apps.append(App(ident, fields.get("Name") or ident, fields.get("Summary", ""), "debian", package[0],
                        kind, fields.get("Homepage", ""),
                        extra={"description": description, "license": fields.get("License", "")}))
    return apps


def desktop_owner(ident, run=run_text):
    """The Debian package of an installed program, from its desktop file."""
    name = ident if ident.endswith(".desktop") else ident + ".desktop"
    path = os.path.join("/usr/share/applications", name)
    if not os.path.exists(path):
        return None
    out = run(["dpkg-query", "-S", path])
    return out.split(":", 1)[0].split(",")[0].strip() if ":" in out else None


CATALOGS = ("/var/lib/swcatalog/yaml", "/var/lib/app-info/yaml")


def catalog_ready(folders=CATALOGS):
    """Debian's catalog of applications comes with the package lists (apt
    update); without it only the installed programs are found."""
    return any(os.path.isdir(f) and os.listdir(f) for f in folders)


def search_debian(query, run=run_text):
    return parse_appstream(run(["appstreamcli", "search", "--details", query]),
                           owner=lambda ident: desktop_owner(ident, run))


def deb_installed(package, run=run_text):
    return run(["dpkg-query", "-W", "-f=${db:Status-Abbrev}", package]).startswith("ii")


# -- Flathub, through flatpak -------------------------------------------------

def parse_flatpak_search(text):
    """Lines 'application<TAB>name<TAB>description<TAB>version<TAB>remotes'."""
    apps = []
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) < 2 or "." not in parts[0]:
            continue    # "No matches found"
        remotes = parts[4] if len(parts) > 4 else "flathub"
        if "flathub" not in remotes:
            continue
        apps.append(App(parts[0], parts[1] or parts[0], parts[2] if len(parts) > 2 else "", "flathub",
                        parts[0], extra={"version": parts[3] if len(parts) > 3 else ""}))
    return apps


def search_flathub(query, run=run_text):
    return parse_flatpak_search(run(["flatpak", "search", "--columns=application,name,description,version,remotes",
                                     query]))


def flatpak_installed_ids(run=run_text):
    return {line.strip() for line in run(["flatpak", "list", "--app", "--columns=application"]).splitlines()
            if line.strip()}


def flathub_ready(run=run_text):
    return "flathub" in run(["flatpak", "remotes", "--columns=name"]).split()


def enable_flathub(run=subprocess.run):
    """Flathub for this user (no password): the remote and its catalog."""
    for command in (["flatpak", "remote-add", "--user", "--if-not-exists", "flathub", FLATHUB],
                    ["flatpak", "update", "--user", "--appstream", "flathub"]):
        result = run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "flatpak")


# -- together ------------------------------------------------------------------

def rank(app, query):
    """Exact name first, then names starting with the words, then the rest."""
    name, query = app.name.lower(), query.lower().strip()
    if name == query:
        return 0
    if name.startswith(query):
        return 1
    if query in name:
        return 2
    return 3


def search(query, flathub=False, run=run_text, limit=40):
    query = query.strip()
    if len(query) < 2:
        return []
    found = search_debian(query, run)
    seen, unique = set(), []
    for app in found:
        if app.package not in seen:
            seen.add(app.package)
            unique.append(app)
    debian = sorted(unique, key=lambda a: (rank(a, query), a.name.lower()))
    for app in debian:
        app.installed = deb_installed(app.package, run)
    others = []
    if flathub:
        installed = flatpak_installed_ids(run)
        others = sorted(search_flathub(query, run), key=lambda a: (rank(a, query), a.name.lower()))
        for app in others:
            app.installed = app.package in installed
    return (debian + others)[:limit]


# -- settings ------------------------------------------------------------------

def settings_path():
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "vabaxos", "store.json")


def load_settings(path=None):
    try:
        with open(path or settings_path(), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"flathub": False}


def save_settings(settings, path=None):
    path = path or settings_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(settings, f)
