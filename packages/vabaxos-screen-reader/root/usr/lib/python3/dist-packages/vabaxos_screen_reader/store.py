# SPDX-FileCopyrightText: 2026 Vabax and VabaxOS contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Orca's settings in dconf, as Orca 50 keeps them (block 9).

Orca 50 stores every setting in dconf, one relocatable schema per group:

    /org/gnome/orca/<profile>/<group>/                    a profile
    /org/gnome/orca/<profile>/voices/<type>/              its voices
    /org/gnome/orca/<profile>/apps/<app>/<group>/         one program

A program's settings are only the keys set there; the others come from the
profile. Orca reads dconf when it loads its settings; most speech and typing
settings can also be changed while it runs, through its D-Bus service
(org.gnome.Orca.Service), and a SIGHUP makes it reload the rest.
"""

import os
import re
import signal
import subprocess

from gi.repository import Gio, GLib

PREFIX = "/org/gnome/orca/"
DEFAULT_PROFILE = "default"

# Group name in the dconf path -> schema id.
SCHEMAS = {
    "speech": "org.gnome.Orca.Speech",
    "voice": "org.gnome.Orca.Voice",
    "typing-echo": "org.gnome.Orca.TypingEcho",
    "say-all": "org.gnome.Orca.SayAll",
    "document": "org.gnome.Orca.Document",
    "sound": "org.gnome.Orca.Sound",
    "braille": "org.gnome.Orca.Braille",
    "structural-navigation": "org.gnome.Orca.StructuralNavigation",
    "caret-navigation": "org.gnome.Orca.CaretNavigation",
    "table-navigation": "org.gnome.Orca.TableNavigation",
    "live-regions": "org.gnome.Orca.LiveRegions",
    "mouse-review": "org.gnome.Orca.MouseReview",
    "system-information": "org.gnome.Orca.SystemInformation",
    "keybindings": "org.gnome.Orca.Keybindings",
    "spellcheck": "org.gnome.Orca.Spellcheck",
    "flat-review": "org.gnome.Orca.FlatReview",
    "metadata": "org.gnome.Orca.ProfileMetadata",
}


def sanitize(name):
    """A profile or program name as Orca writes it in a dconf path (the same
    rule as Orca's gsettings_migrator.sanitize_gsettings_path)."""
    name = re.sub(r"-+", "-", re.sub(r"[^a-z0-9-]", "-", name.lower())).strip("-")
    return name or "profile"


def schema_installed(schema_id):
    source = Gio.SettingsSchemaSource.get_default()
    return source is not None and source.lookup(schema_id, True) is not None


def dconf(*args, text_input=None):
    """Runs the dconf command; its output, or None if it failed."""
    try:
        result = subprocess.run(["dconf", *args], input=text_input, capture_output=True, text=True,
                                check=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout


class Store:
    """Reads and writes one profile, or one program inside it."""

    def __init__(self, profile=DEFAULT_PROFILE, app=None):
        self.profile = profile
        self.app = app
        self._settings = {}
        self.pending_reload = False
        self.orca = OrcaService()

    # -- paths -----------------------------------------------------------

    def path(self, group, sub=None, app=None):
        base = f"{PREFIX}{sanitize(self.profile)}/"
        if app:
            base += f"apps/{sanitize(app)}/"
        return base + (sub or group) + "/"

    def settings(self, group, sub=None, app=None):
        path = self.path(group, sub, app)
        if path not in self._settings:
            schema_id = SCHEMAS[group]
            if not schema_installed(schema_id):
                return None
            self._settings[path] = Gio.Settings.new_with_path(schema_id, path)
        return self._settings[path]

    # -- values ------------------------------------------------------------

    def get(self, group, key, sub=None):
        """The value in use: the program's if it has one, else the profile's."""
        if self.app:
            gs = self.settings(group, sub, self.app)
            if gs is not None and gs.get_user_value(key) is not None:
                return gs.get_value(key).unpack()
        gs = self.settings(group, sub)
        return None if gs is None else gs.get_value(key).unpack()

    def is_program_value(self, group, key, sub=None):
        gs = self.settings(group, sub, self.app) if self.app else None
        return gs is not None and gs.get_user_value(key) is not None

    def set(self, group, key, value, sub=None):
        """Saves a value, then tells Orca: at once if it can, else later."""
        gs = self.settings(group, sub, self.app)
        if gs is None:
            return False
        current = gs.get_value(key)
        gs.set_value(key, GLib.Variant(current.get_type_string(), value))
        Gio.Settings.sync()
        if self.app or not self.orca.set_live(group, key, value, sub):
            self.pending_reload = True
        return True

    def reset_program_value(self, group, key, sub=None):
        if self.app:
            gs = self.settings(group, sub, self.app)
            if gs is not None:
                gs.reset(key)
                self.pending_reload = True

    def reload_orca_if_needed(self):
        if self.pending_reload:
            self.orca.reload()
            self.pending_reload = False


# -- profiles -----------------------------------------------------------------

DEFAULTS_DIR = "/etc/dconf/db/vabaxos.d"


def apply_vabaxos_defaults(directory=DEFAULTS_DIR):
    """Writes VabaxOS's Orca defaults (the Orca groups of the dconf keyfiles
    in directory, such as 40-orca-keys and 41-orca-typing) as the user's
    own values, for every key the user has not set.

    Orca 50 reads its settings and keys only from values the user set
    (get_user_value): the system dconf defaults of VabaxOS were ignored, so
    the NVDA keys and the typing echo never applied (found in QEMU,
    2026-09-26). Run before Orca starts (orca.service.d); the number of
    values written is returned."""
    written = 0
    try:
        names = sorted(os.listdir(directory))
    except OSError:
        return 0
    for name in names:
        keyfile = GLib.KeyFile()
        try:
            keyfile.load_from_file(os.path.join(directory, name), GLib.KeyFileFlags.NONE)
        except GLib.Error:
            continue
        for group_path in keyfile.get_groups()[0]:
            parts = group_path.strip("/").split("/")
            if parts[:3] != ["org", "gnome", "orca"] or len(parts) != 5:
                continue
            group = parts[4]
            schema_id = SCHEMAS.get(group)
            if schema_id is None or not schema_installed(schema_id):
                continue
            settings = Gio.Settings.new_with_path(schema_id, "/" + "/".join(parts) + "/")
            for key in keyfile.get_keys(group_path)[0]:
                if settings.get_user_value(key) is not None:
                    continue
                try:
                    value = GLib.Variant.parse(settings.get_value(key).get_type(),
                                               keyfile.get_value(group_path, key), None, None)
                except GLib.Error:
                    continue
                settings.set_value(key, value)
                written += 1
    Gio.Settings.sync()
    return written


def list_profiles():
    """[(display name, internal name)], the default profile first."""
    profiles = []
    listing = dconf("list", PREFIX) or ""
    for entry in listing.split():
        if not entry.endswith("/"):
            continue
        name = entry.rstrip("/")
        path = f"{PREFIX}{name}/metadata/"
        if not schema_installed(SCHEMAS["metadata"]):
            continue
        meta = Gio.Settings.new_with_path(SCHEMAS["metadata"], path)
        display, internal = meta.get_user_value("display-name"), meta.get_user_value("internal-name")
        if display is None or internal is None:
            continue
        profiles.append((display.get_string(), internal.get_string()))
    profiles.sort(key=lambda p: (p[1] != DEFAULT_PROFILE, p[0].lower()))
    if not any(internal == DEFAULT_PROFILE for _, internal in profiles):
        profiles.insert(0, ("Default", DEFAULT_PROFILE))
    return profiles


def write_metadata(internal, display):
    meta = Gio.Settings.new_with_path(SCHEMAS["metadata"], f"{PREFIX}{sanitize(internal)}/metadata/")
    meta.set_string("display-name", display)
    meta.set_string("internal-name", internal)
    Gio.Settings.sync()


def create_profile(display, source=DEFAULT_PROFILE, overrides=None):
    """A new profile: a copy of source, then the overrides
    {(group, sub): {key: value}}. Returns its internal name."""
    internal = sanitize(display)
    existing = {i for _, i in list_profiles()}
    base, number = internal, 2
    while internal in existing:
        internal, number = f"{base}-{number}", number + 1
    # Orca lists only profiles with metadata: the default one needs it too.
    write_metadata(DEFAULT_PROFILE, "Default") if DEFAULT_PROFILE not in existing else None
    dump = dconf("dump", f"{PREFIX}{sanitize(source)}/")
    if dump:
        dconf("load", f"{PREFIX}{internal}/", text_input=dump)
    write_metadata(internal, display)
    store = Store(internal)
    for (group, sub), values in (overrides or {}).items():
        gs = store.settings(group, sub)
        if gs is None:
            continue
        for key, value in values.items():
            gs.set_value(key, GLib.Variant(gs.get_value(key).get_type_string(), value))
    Gio.Settings.sync()
    return internal


def delete_profile(internal):
    if internal == DEFAULT_PROFILE:
        return False
    return dconf("reset", "-f", f"{PREFIX}{sanitize(internal)}/") is not None


def export_settings(path):
    dump = dconf("dump", PREFIX)
    if dump is None:
        return False
    with open(path, "w", encoding="utf-8") as f:
        f.write("# VabaxOS: screen reader settings (Orca), from dconf dump /org/gnome/orca/\n")
        f.write(dump)
    return True


def import_settings(path):
    with open(path, encoding="utf-8") as f:
        text = "".join(line for line in f if not line.startswith("#"))
    if not text.strip().startswith("["):
        return False
    return dconf("load", PREFIX, text_input=text) is not None


# -- Orca itself ----------------------------------------------------------------

# Speech keys whose runtime setter takes another type (an int for an enum)
# or another name: Orca reloads them instead.
LIVE_EXCLUDED = {"progress-bar-speech-verbosity", "synthesizer", "speech-server", "speech-server-factory"}


def camel(name):
    return "".join(part.capitalize() for part in re.split(r"[-_]", name))


class OrcaService:
    """Orca's D-Bus service: settings changed while it runs, profiles."""

    NAME = "org.gnome.Orca.Service"
    PATH = "/org/gnome/Orca/Service"

    def __init__(self):
        self._setters = None
        self._bus = None

    def _call(self, path, interface, method, args=None, reply=None):
        try:
            if self._bus is None:
                self._bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
            result = self._bus.call_sync(self.NAME, path, interface, method, args,
                                         GLib.VariantType.new(reply) if reply else None,
                                         Gio.DBusCallFlags.NONE, 2000, None)
            return result.unpack() if result is not None else ()
        except GLib.Error:
            return None

    def setters(self):
        """{camel setter name: [module paths]} of the running Orca, or {}."""
        if self._setters is None:
            self._setters = {}
            modules = self._call(self.PATH, self.NAME, "ListModules", reply="(as)")
            for module in (modules or ([],))[0]:
                path = f"{self.PATH}/{module}"
                found = self._call(path, "org.gnome.Orca.Module", "ListRuntimeSetters", reply="(a(ss))")
                for name, _description in (found or ([],))[0]:
                    self._setters.setdefault(name, []).append(path)
        return self._setters

    @staticmethod
    def setter_name(group, key, sub=None):
        """Orca's runtime setter for a setting, or None: only speech, the
        default voice and typing echo (other groups share key names with
        different meanings, such as braille's verbosity-level)."""
        if group == "voice" and sub in (None, "voices/default"):
            return camel(key)
        if group == "speech":
            if key == "enable":
                return "SpeechIsEnabled"
            if key in LIVE_EXCLUDED:
                return None
            return camel(key)
        if group == "typing-echo":
            return camel(key) + "Enabled"
        return None

    def set_live(self, group, key, value, sub=None):
        """Changes a setting in the running Orca; False if it cannot."""
        name = self.setter_name(group, key, sub)
        if name is None:
            return False
        paths = self.setters().get(name, [])
        wanted = "Typing" if group == "typing-echo" else "Speech"
        path = next((p for p in paths if wanted in p.rsplit("/", 1)[-1]), paths[0] if len(paths) == 1 else None)
        if path is None:
            return False
        variant = GLib.Variant("b", value) if isinstance(value, bool) else \
            GLib.Variant("i", value) if isinstance(value, int) else \
            GLib.Variant("d", value) if isinstance(value, float) else GLib.Variant("s", str(value))
        done = self._call(path, "org.gnome.Orca.Module", "ExecuteRuntimeSetter",
                          GLib.Variant("(sv)", (name, variant)), reply="(b)")
        return bool(done and done[0])

    def set_profile(self, internal):
        paths = self.setters().get("ActiveProfile", [])
        if not paths:
            return False
        path = paths[0]
        done = self._call(path, "org.gnome.Orca.Module", "ExecuteRuntimeSetter",
                          GLib.Variant("(sv)", ("ActiveProfile", GLib.Variant("s", internal))), reply="(b)")
        return bool(done and done[0])

    def present(self, message):
        return self._call(self.PATH, self.NAME, "PresentMessage", GLib.Variant("(s)", (message,)), "(b)")

    @staticmethod
    def reload():
        """SIGHUP: Orca reloads every setting from dconf."""
        uid = str(os.getuid())
        try:
            pids = subprocess.run(["pgrep", "-u", uid, "-x", "orca"], capture_output=True, text=True).stdout.split()
        except OSError:
            return False
        for pid in pids:
            try:
                os.kill(int(pid), signal.SIGHUP)
            except (OSError, ValueError):
                pass
        return bool(pids)
