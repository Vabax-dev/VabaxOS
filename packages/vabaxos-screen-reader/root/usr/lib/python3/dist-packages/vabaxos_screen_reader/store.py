# SPDX-FileCopyrightText: 2026 Vabax and VabaxOS contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Orca's settings, as Orca 48 keeps them (block 9, ADR-0027).

Orca 48 (Debian 13) keeps its settings in JSON files, in its folder
~/.local/share/orca:

    user-settings.conf        {"general", "profiles", "pronunciations", "keybindings"}
    app-settings/<app>.conf   {"profiles": {profile: {"general", "pronunciations",
                                                      "keybindings"}}}

"general" holds settings for every profile; a profile, "profiles"[name],
holds its own values over them and "profile": [display name, name]. A
program's file holds only the values set for that program. Settings not
written anywhere keep Orca's defaults.

The pages name every setting as Orca 50 did in dconf, (group, key);
orca48_map says which Orca 48 setting it is. The voices ("voice",
"voices/<type>") are Orca's "voices" dictionary; the keys ("keybindings",
"entries") are the profile's "keybindings".

Orca 48 reads the files when it starts, and has no service to change a
setting while it runs: Orca is started again (orca --replace) to use them,
after a change of page or when the window closes.
"""

import copy
import json
import os
import re
import subprocess

from gi.repository import GLib

from .orca48_map import SETTINGS

DEFAULT_PROFILE = "default"

# The groups of the pages (the dconf folders of Orca 50).
SCHEMAS = sorted({group for group, _key in SETTINGS} | {"voice", "keybindings", "speech"})

# Orca 48's voice defaults (orca/settings.py and acss.py).
VOICE_DEFAULTS = {"rate": 50, "average-pitch": 5.0, "gain": 10.0}
VOICE_KEYS = {"rate": "rate", "pitch": "average-pitch", "volume": "gain"}
DEFAULT_VOICES = {"default": {"established": False}, "uppercase": {"average-pitch": 7.0},
                  "hyperlink": {"established": False}, "system": {"established": False}}
KEYBOARD_LAYOUTS = {"desktop": 1, "laptop": 2}
DEFAULT_MODIFIER_KEYS = ["Insert", "KP_Insert"]
ORCA_START = "/usr/libexec/vabaxos/orca-start"


def sanitize(name):
    """A profile name as a file key: lower case letters, digits and dashes."""
    name = re.sub(r"-+", "-", re.sub(r"[^a-z0-9-]", "-", name.lower())).strip("-")
    return name or "profile"


def orca_dir():
    return os.path.join(GLib.get_user_data_dir(), "orca")


def settings_path():
    return os.path.join(orca_dir(), "user-settings.conf")


def app_path(app):
    return os.path.join(orca_dir(), "app-settings", f"{app}.conf")


def empty_settings():
    return {"general": {}, "profiles": {DEFAULT_PROFILE: {"profile": ["Default", DEFAULT_PROFILE]}},
            "pronunciations": {}, "keybindings": {}}


def write_json(path, data):
    """Writes a settings file whole (a new file, then renamed over the old)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".new", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    os.replace(path + ".new", path)


def load(path=None):
    """Orca's user settings, or empty ones when Orca never saved them."""
    path = path or settings_path()
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return empty_settings()
    if not isinstance(data, dict):
        return empty_settings()
    for key, value in empty_settings().items():
        if not isinstance(data.get(key), dict):
            data[key] = value
    data["profiles"].setdefault(DEFAULT_PROFILE, {"profile": ["Default", DEFAULT_PROFILE]})
    return data


def save(data, path=None):
    write_json(path or settings_path(), data)


def load_app(app):
    try:
        with open(app_path(app), encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {}
    if not isinstance(data, dict) or not isinstance(data.get("profiles"), dict):
        data = {"profiles": {}}
    return data


def to_page(entry, value):
    """An Orca 48 value as the pages show it."""
    _name, kind, _default, values = entry
    if kind == "enum" and values:
        for nick, number in values.items():
            if number == value:
                return nick
    return value


def to_orca(entry, value):
    """A value of the pages as Orca 48 keeps it."""
    _name, kind, _default, values = entry
    if kind == "enum" and values and isinstance(value, str):
        return values.get(value, value)
    if kind == "int":
        return int(value)
    if kind == "float":
        return float(value)
    return value


class Store:
    """Reads and writes one profile, or one program inside it."""

    def __init__(self, profile=DEFAULT_PROFILE, app=None):
        self.profile = profile
        self.app = app
        self.pending_reload = False
        self.orca = OrcaService()

    # -- where the values are -----------------------------------------------

    def _profile(self, data):
        return data["profiles"].setdefault(self.profile, {"profile": [self.profile, self.profile]})

    def _app_general(self, app_data, create=False):
        profile = app_data["profiles"].get(self.profile)
        if profile is None:
            if not create:
                return {}
            profile = app_data["profiles"][self.profile] = {"general": {}, "pronunciations": {},
                                                             "keybindings": {}}
        return profile.setdefault("general", {})

    def available(self, group, key, sub=None):
        """Whether Orca 48 has this setting (some of Orca 50 are missing)."""
        if group == "voice":
            return key in VOICE_KEYS or key == "family-name"
        if group == "speech" and key == "synthesizer":
            return True
        if group == "keybindings":
            return key in ("entries", "keyboard-layout", "desktop-modifier-keys")
        return (group, key) in SETTINGS

    def settings(self, group, sub=None, app=None):
        """Something when the group exists, else None (for the pages)."""
        return self if group in SCHEMAS else None

    def _raw(self, name, data, app_data):
        """(found, value) of an Orca 48 setting: program, profile, general."""
        if self.app:
            general = self._app_general(app_data)
            if name in general:
                return True, general[name]
        profile = data["profiles"].get(self.profile, {})
        if name in profile:
            return True, profile[name]
        if name in data["general"]:
            return True, data["general"][name]
        return False, None

    def _orca_name(self, group, key):
        if group == "voice":
            return "voices"
        if group == "speech" and key == "synthesizer":
            return "speechServerInfo"
        if group == "keybindings":
            return {"keyboard-layout": "keyboardLayout", "desktop-modifier-keys": "orcaModifierKeys"}.get(key)
        entry = SETTINGS.get((group, key))
        return entry[0] if entry else None

    # -- values ------------------------------------------------------------

    def get(self, group, key, sub=None):
        """The value in use: the program's if it has one, else the profile's."""
        data = load()
        app_data = load_app(self.app) if self.app else {"profiles": {}}
        if group == "voice":
            voice = (sub or "voices/default").split("/")[-1]
            found, voices = self._raw("voices", data, app_data)
            voices = voices if found and isinstance(voices, dict) else DEFAULT_VOICES
            if key == "family-name":
                family = voices.get(voice, {}).get("family") or {}
                return family.get("name") or ""
            orca_key = VOICE_KEYS.get(key)
            value = voices.get(voice, {}).get(orca_key)
            if value is None:
                value = DEFAULT_VOICES.get(voice, {}).get(orca_key, VOICE_DEFAULTS.get(orca_key))
            return value
        if group == "speech" and key == "synthesizer":
            found, info = self._raw("speechServerInfo", data, app_data)
            if found and isinstance(info, list) and len(info) > 1 and info[1] not in (None, "default"):
                return info[1]
            return ""
        if group == "keybindings":
            if key == "entries":
                profile = data["profiles"].get(self.profile, {})
                return profile.get("keybindings") or data.get("keybindings") or {}
            if key == "keyboard-layout":
                found, value = self._raw("keyboardLayout", data, app_data)
                return {1: "desktop", 2: "laptop"}.get(value, "desktop") if found else "desktop"
            if key == "desktop-modifier-keys":
                found, value = self._raw("orcaModifierKeys", data, app_data)
                return value if found else list(DEFAULT_MODIFIER_KEYS)
            return None
        entry = SETTINGS.get((group, key))
        if entry is None:
            return None
        found, value = self._raw(entry[0], data, app_data)
        return to_page(entry, value if found else entry[2])

    def is_program_value(self, group, key, sub=None):
        if not self.app:
            return False
        name = self._orca_name(group, key)
        return name is not None and name in self._app_general(load_app(self.app))

    def set(self, group, key, value, sub=None):
        """Saves a value; Orca uses it when it starts again (reload)."""
        if not self.available(group, key, sub):
            return False
        data = load()
        app_data = load_app(self.app) if self.app else None
        target = self._app_general(app_data, create=True) if self.app else self._profile(data)
        if group == "voice":
            voice = (sub or "voices/default").split("/")[-1]
            found, voices = self._raw("voices", data, app_data or {"profiles": {}})
            voices = copy.deepcopy(voices if found and isinstance(voices, dict) else DEFAULT_VOICES)
            if key == "family-name":
                # The voice of the speech module (Kokoro's im_nicola...);
                # empty: the module's own choice.
                if value:
                    voices.setdefault(voice, {})["family"] = {"name": value}
                else:
                    voices.setdefault(voice, {}).pop("family", None)
            else:
                orca_key = VOICE_KEYS[key]
                voices.setdefault(voice, {})[orca_key] = int(value) if orca_key == "rate" else float(value)
            if voice == "default":
                voices[voice]["established"] = True
            target["voices"] = voices
        elif group == "speech" and key == "synthesizer":
            if value:
                target["speechServerInfo"] = [value, value]
                target["speechServerFactory"] = "orca.speechdispatcherfactory"
            else:
                target["speechServerInfo"] = None
        elif group == "keybindings":
            if key == "entries":
                self._profile(data)["keybindings"] = value
            elif key == "keyboard-layout":
                target["keyboardLayout"] = KEYBOARD_LAYOUTS.get(value, 1)
            else:
                target["orcaModifierKeys"] = list(value)
        else:
            entry = SETTINGS[(group, key)]
            target[entry[0]] = to_orca(entry, value)
        if self.app and not (group == "keybindings" and key == "entries"):
            write_json(app_path(self.app), app_data)
        else:
            save(data)
        self.pending_reload = True
        return True

    def reset_program_value(self, group, key, sub=None):
        if not self.app:
            return
        name = self._orca_name(group, key)
        app_data = load_app(self.app)
        general = self._app_general(app_data)
        if name in general:
            del general[name]
            write_json(app_path(self.app), app_data)
            self.pending_reload = True

    def reload_orca_if_needed(self):
        if self.pending_reload:
            self.orca.reload()
            self.pending_reload = False


# -- VabaxOS's defaults ------------------------------------------------------------

DEFAULTS_FILE = "/usr/share/vabaxos-screen-reader/orca-defaults.json"
# The choices of the spoken welcome (the speed of the voice), written by
# vabaxos-welcome before the desktop: they win over the defaults above.
LOCAL_DEFAULTS_FILE = "/var/lib/vabaxos/orca-defaults.json"


def defaults_state_path():
    state = os.environ.get("XDG_STATE_HOME") or os.path.join(os.path.expanduser("~"), ".local", "state")
    return os.path.join(state, "vabaxos", "orca-defaults")


def read_defaults(*paths):
    """The defaults files merged, the later ones winning."""
    merged = {"general": {}}
    for path in paths:
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            continue
        if not isinstance(data, dict):
            continue
        merged["general"].update(data.get("general") or {})
        if "keybindings" in data:
            merged["keybindings"] = data["keybindings"]
    return merged


def apply_vabaxos_defaults(defaults_file=DEFAULTS_FILE, state_path=None, local_file=LOCAL_DEFAULTS_FILE):
    """Writes VabaxOS's Orca defaults (the NVDA keys, typing echo as NVDA)
    as the user's own values in the default profile, for every setting the
    user has not set, before Orca starts.

    The defaults file is JSON: {"general": {name: value}, "keybindings":
    {command: [[keysym, mask, modifiers, clicks]]}}. Each default is written
    once: Orca removes a value that equals its own default when the user
    saves it in Orca's preferences (for example key echo on again), and
    writing VabaxOS's default again at the next start would undo the
    user's choice. The defaults already given are listed in state_path,
    with their value: a default changed by a newer VabaxOS is given again,
    where the user still has the old one. Returns the number of values
    written."""
    defaults = read_defaults(defaults_file, local_file)
    if not defaults["general"] and "keybindings" not in defaults:
        return 0
    state_path = state_path or defaults_state_path()
    given = {}
    try:
        with open(state_path, encoding="utf-8") as f:
            for line in f:
                path, sep, value = line.rstrip("\n").partition("\t")
                if sep:
                    given[path] = value
    except OSError:
        pass
    before = dict(given)
    data = load()
    profile = data["profiles"].setdefault(DEFAULT_PROFILE, {"profile": ["Default", DEFAULT_PROFILE]})
    written = 0
    items = [("general/" + name, name, value) for name, value in sorted(defaults.get("general", {}).items())]
    if "keybindings" in defaults:
        items.append(("keybindings", None, defaults["keybindings"]))
    for path, name, value in items:
        text = json.dumps(value, sort_keys=True)
        old = given.get(path)
        if old == text:
            continue
        given[path] = text
        if name is None:
            mine = profile.get("keybindings") or None
        else:
            mine = profile.get(name, data["general"].get(name))
        if mine is not None:
            # Still the old default of VabaxOS, never changed by the user:
            # the new default replaces it.
            if old is None or json.dumps(mine, sort_keys=True) != old:
                continue
        if name is None:
            profile["keybindings"] = value
        else:
            profile[name] = value
        written += 1
    if written:
        save(data)
    if given != before:
        try:
            os.makedirs(os.path.dirname(state_path), exist_ok=True)
            with open(state_path + ".new", "w", encoding="utf-8") as f:
                f.writelines(f"{path}\t{value}\n" for path, value in sorted(given.items()))
            os.replace(state_path + ".new", state_path)
        except OSError:
            pass
    return written


# -- profiles -----------------------------------------------------------------


def list_profiles():
    """[(display name, internal name)], the default profile first."""
    profiles = []
    for internal, values in load()["profiles"].items():
        name = values.get("profile") if isinstance(values, dict) else None
        display = name[0] if isinstance(name, list) and name else internal
        profiles.append((display, internal))
    profiles.sort(key=lambda p: (p[1] != DEFAULT_PROFILE, p[0].lower()))
    return profiles


def create_profile(display, source=DEFAULT_PROFILE, overrides=None):
    """A new profile: a copy of source, then the overrides
    {(group, sub): {key: value}}. Returns its internal name."""
    data = load()
    internal = sanitize(display)
    base, number = internal, 2
    while internal in data["profiles"]:
        internal, number = f"{base}-{number}", number + 1
    profile = copy.deepcopy(data["profiles"].get(source, {}))
    profile["profile"] = [display, internal]
    data["profiles"][internal] = profile
    save(data)
    store = Store(internal)
    for (group, sub), values in (overrides or {}).items():
        for key, value in values.items():
            store.set(group, key, value, sub)
    return internal


def delete_profile(internal):
    if internal == DEFAULT_PROFILE:
        return False
    data = load()
    if internal not in data["profiles"]:
        return False
    del data["profiles"][internal]
    for key in ("startingProfile", "activeProfile"):
        value = data["general"].get(key)
        if isinstance(value, list) and len(value) > 1 and value[1] == internal:
            data["general"][key] = ["Default", DEFAULT_PROFILE]
    save(data)
    return True


def export_settings(path):
    """All of Orca's settings (the user's and the programs') in one file."""
    apps = {}
    folder = os.path.join(orca_dir(), "app-settings")
    try:
        names = sorted(os.listdir(folder))
    except OSError:
        names = []
    for name in names:
        if name.endswith(".conf"):
            apps[name[:-5]] = load_app(name[:-5])
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"vabaxos-screen-reader": 1, "orca": 48, "user-settings": load(), "app-settings": apps},
                  f, indent=2)
    return True


def import_settings(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return False
    if not isinstance(data, dict) or data.get("vabaxos-screen-reader") != 1 \
            or not isinstance(data.get("user-settings"), dict) \
            or not isinstance(data["user-settings"].get("profiles"), dict):
        return False
    save(data["user-settings"])
    for app, values in (data.get("app-settings") or {}).items():
        if isinstance(values, dict) and "/" not in app and not app.startswith("."):
            write_json(app_path(app), values)
    return True


# -- Orca itself ----------------------------------------------------------------


class OrcaService:
    """The running Orca. Orca 48 has no D-Bus service: it is started again
    to read its settings, and messages are spoken by speech-dispatcher."""

    @staticmethod
    def running():
        try:
            out = subprocess.run(["pgrep", "-u", str(os.getuid()), "-x", "orca"], capture_output=True,
                                 text=True, timeout=5).stdout
        except (OSError, subprocess.SubprocessError):
            return False
        return bool(out.split())

    @staticmethod
    def set_live(group, key, value, sub=None):
        return False

    @staticmethod
    def set_profile(internal):
        """Makes a profile the one Orca uses when it starts."""
        data = load()
        values = data["profiles"].get(internal)
        if values is None:
            return False
        name = list(values.get("profile") or [internal, internal])
        data["general"]["startingProfile"] = name
        data["general"]["activeProfile"] = name
        save(data)
        return True

    @staticmethod
    def present(message):
        """Says a message, as Orca would, through speech-dispatcher."""
        try:
            import speechd
            client = speechd.SSIPClient("vabaxos-screen-reader")
            client.set_priority(speechd.Priority.MESSAGE)
            client.speak(message)
            client.close()
            return True
        except Exception:  # speech-dispatcher missing or not answering
            return False

    def reload(self):
        """Starts Orca again (orca --replace), so it reads its settings."""
        if not self.running():
            return False
        command = [ORCA_START, "--replace"] if os.access(ORCA_START, os.X_OK) else ["orca", "--replace"]
        try:
            subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, start_new_session=True)
        except OSError:
            return False
        return True
