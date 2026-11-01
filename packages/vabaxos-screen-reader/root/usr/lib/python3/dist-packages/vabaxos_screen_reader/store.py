# SPDX-FileCopyrightText: 2026 Vabax and VabaxOS contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Orca's settings in dconf, as Orca 50 and 51 keep them (block 9).

Orca stores every setting in dconf, one relocatable schema per group:

    /org/gnome/orca/<profile>/<group>/                    a profile
    /org/gnome/orca/<profile>/voices/<type>/              its voices
    /org/gnome/orca/<profile>/apps/<app>/<group>/         one program

A program's settings are only the keys set there; the others come from the
profile. Orca reads dconf when it loads its settings; most speech and typing
settings can also be changed while it runs, through its D-Bus service
(Orca 51: org.gnome.Orca1.Service, each module an object whose settings are
D-Bus properties), and a SIGHUP makes it reload the rest.
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
    "pronunciations": "org.gnome.Orca.Pronunciations",
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
    """Orca's D-Bus service (Orca 51): settings changed while it runs,
    profiles, messages. Each module (SpeechManager, TypingEchoPresenter,
    ProfileManager...) is an object under PATH with the interface
    org.gnome.Orca1.<module>; its settings are writable D-Bus properties
    named like Orca's setters (set_rate: Rate)."""

    NAME = "org.gnome.Orca1.Service"
    PATH = "/org/gnome/Orca1/Service"
    PROPERTIES = "org.freedesktop.DBus.Properties"

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

    def _introspect(self, path):
        reply = self._call(path, "org.freedesktop.DBus.Introspectable", "Introspect", reply="(s)")
        if not reply:
            return None
        try:
            return Gio.DBusNodeInfo.new_for_xml(reply[0])
        except GLib.Error:
            return None

    def setters(self):
        """{property name: [(module path, interface, D-Bus type)]} of the
        writable settings of the running Orca, or {}."""
        if self._setters is None:
            self._setters = {}
            root = self._introspect(self.PATH)
            for child in (root.nodes if root else []):
                path = f"{self.PATH}/{child.path}"
                node = self._introspect(path)
                for interface in (node.interfaces if node else []):
                    if not interface.name.startswith("org.gnome.Orca1."):
                        continue
                    for prop in interface.properties:
                        if prop.flags & Gio.DBusPropertyInfoFlags.WRITABLE:
                            self._setters.setdefault(prop.name, []).append((path, interface.name,
                                                                            prop.signature))
        return self._setters

    @staticmethod
    def variant(signature, value):
        """value as the D-Bus type Orca's property wants."""
        if signature == "b":
            return GLib.Variant("b", bool(value))
        if signature in ("u", "i", "x", "t", "n", "q", "y"):
            return GLib.Variant(signature, int(round(value)) if isinstance(value, float) else int(value))
        if signature == "d":
            return GLib.Variant("d", float(value))
        return GLib.Variant("s", str(value))

    def _choose(self, name, wanted=None):
        found = self.setters().get(name, [])
        if wanted:
            for entry in found:
                if wanted in entry[1].rsplit(".", 1)[-1]:
                    return entry
        return found[0] if len(found) == 1 else None

    def set_property(self, name, value, wanted=None):
        entry = self._choose(name, wanted)
        if entry is None:
            return False
        path, interface, signature = entry
        done = self._call(path, self.PROPERTIES, "Set",
                          GLib.Variant("(ssv)", (interface, name, self.variant(signature, value))))
        return done is not None

    def get_property(self, name, wanted=None):
        entry = self._choose(name, wanted)
        if entry is None:
            return None
        path, interface, _signature = entry
        reply = self._call(path, self.PROPERTIES, "Get", GLib.Variant("(ss)", (interface, name)), "(v)")
        return reply[0] if reply else None

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
        return self.set_property(name, value, "Typing" if group == "typing-echo" else "Speech")

    def set_profile(self, internal):
        return self.set_property("ActiveProfile", internal)

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
