#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Vabax and VabaxOS contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for vabaxos-screen-reader (block 9): the window on a hidden
Broadway display, Orca's settings schema (a copy of Orca 50.2's, in this
folder) in a GSettings memory backend, dconf replaced by a fake: nothing on
the system changes.

    python3 tests/screen-reader/test_screen_reader.py
"""

import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
PACKAGE = os.path.join(REPO, "packages", "vabaxos-screen-reader", "root")
PROGRAM = os.path.join(PACKAGE, "usr", "bin", "vabaxos-screen-reader")
LIBRARY = os.path.join(PACKAGE, "usr", "lib", "python3", "dist-packages")

CHILD = r'''
import importlib.machinery, importlib.util, sys
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
sys.path.insert(0, sys.argv[2])
from vabaxos_screen_reader import pages, store
from gi.repository import Adw, GLib, Gtk

# Fake dconf: profiles are listed from what the test wrote.
written = {}
def fake_dconf(*args, text_input=None):
    if args[0] == "list":
        return "".join(f"{name}/\n" for name in sorted(written))
    if args[0] == "dump":
        return ""
    return ""
store.dconf = fake_dconf
original_metadata = store.write_metadata
def recording_metadata(internal, display):
    written[store.sanitize(internal)] = display
    original_metadata(internal, display)
store.write_metadata = recording_metadata

loader = importlib.machinery.SourceFileLoader("screenreader", sys.argv[1])
spec = importlib.util.spec_from_loader("screenreader", loader)
sr = importlib.util.module_from_spec(spec)
loader.exec_module(sr)
sr.running_programs = lambda: []

def walk(widget):
    yield widget
    child = widget.get_first_child()
    while child is not None:
        yield from walk(child)
        child = child.get_next_sibling()

def check(application):
    window = sr.ScreenReaderWindow(application)
    window.present()
    rows = [row for row, _u in window.rows.bound]
    print("ROWS:%d" % len(rows), flush=True)
    print("UNAVAILABLE:" + ",".join(r.setting[1] for r in rows if not r.get_sensitive()), flush=True)
    print("UNTITLED:%d" % sum(1 for r in rows if not r.get_title()), flush=True)
    print("PAGES:" + "|".join(r.get_accessible_role().value_nick + "=" + r.ident for r in walk(window.page_list)
                              if isinstance(r, Gtk.ListBoxRow)), flush=True)
    unnamed = [type(w).__name__ for w in walk(window) if isinstance(w, Gtk.Button) and w.get_mapped()
               and not w.get_label() and not w.get_tooltip_text()
               and not any(w.get_ancestor(k) for k in (Gtk.WindowControls, Gtk.MenuButton))]
    print("UNNAMED:" + ",".join(unnamed), flush=True)

    s = window.store
    s.set("voice", "rate", 70, "voices/default")
    print("RATE:%s" % s.get("voice", "rate", "voices/default"), flush=True)
    s.set("speech", "punctuation-level", "all")
    # One program: its value wins, the profile keeps its own.
    s.app = "ptyxis"
    s.set("speech", "punctuation-level", "none")
    program_value = s.get("speech", "punctuation-level")
    marked = s.is_program_value("speech", "punctuation-level")
    s.app = None
    print("LAYERS:%s,%s,%s" % (program_value, s.get("speech", "punctuation-level"), marked), flush=True)
    s.app = "ptyxis"
    s.reset_program_value("speech", "punctuation-level")
    print("RESET:%s" % s.get("speech", "punctuation-level"), flush=True)
    s.app = None
    print("PATHS:%s|%s" % (s.path("speech"), s.path("voice", "voices/default", "Ptyxis Terminal")), flush=True)

    # A ready-made profile: metadata for it and for the default profile,
    # its overrides at its own path.
    ident, title, _d, overrides = pages.PRESETS[1]
    internal = store.create_profile(title, overrides=overrides)
    fast = store.Store(internal)
    print("PRESET:%s,%s,%s" % (internal, fast.get("voice", "rate", "voices/default"),
                                fast.get("speech", "verbosity-level")), flush=True)
    print("PROFILES:" + "|".join(i for _n, i in store.list_profiles()), flush=True)
    window.fill_profiles(select=internal)
    print("SELECTED:%s" % window.store.profile, flush=True)
    print("SETTER:%s,%s,%s,%s" % (store.OrcaService.setter_name("typing-echo", "key-echo"),
                                  store.OrcaService.setter_name("speech", "enable"),
                                  store.OrcaService.setter_name("braille", "verbosity-level"),
                                  store.OrcaService.setter_name("voice", "rate", "voices/default")), flush=True)
    print("SANITIZE:%s" % store.sanitize("Studio 2!"), flush=True)
    application.quit()

app = Adw.Application(application_id="org.vabaxos.ScreenReaderTest")
app.connect("activate", check)
app.run([])
'''


COMPILER = shutil.which("glib-compile-schemas") or next(
    (p for p in ("/usr/lib/x86_64-linux-gnu/glib-2.0/glib-compile-schemas",
                 "/usr/lib/aarch64-linux-gnu/glib-2.0/glib-compile-schemas") if os.path.exists(p)), None)


def free_display():
    for number in range(140, 180):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", 8080 + number)) != 0:
                return number
    raise RuntimeError("no free Broadway display")


@unittest.skipUnless(shutil.which("gtk4-broadwayd") and COMPILER,
                     "gtk4-broadwayd (libgtk-4-bin) or glib-compile-schemas is not installed")
class ScreenReaderTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        schemas = os.path.join(cls.tmp.name, "schemas")
        os.makedirs(schemas)
        shutil.copy(os.path.join(HERE, "org.gnome.Orca.gschema.xml"), schemas)
        subprocess.run([COMPILER, schemas], check=True)
        display = free_display()
        cls.broadway = subprocess.Popen(["gtk4-broadwayd", f":{display}"], stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL)
        time.sleep(1)
        env = dict(os.environ, GDK_BACKEND="broadway", BROADWAY_DISPLAY=f":{display}",
                   GSETTINGS_BACKEND="memory", GSETTINGS_SCHEMA_DIR=schemas, NO_AT_BRIDGE="1",
                   LANGUAGE="C", LANG="C.UTF-8", DBUS_SESSION_BUS_ADDRESS="unix:path=/nonexistent",
                   XDG_CONFIG_HOME=os.path.join(cls.tmp.name, "config"), PYTHONDONTWRITEBYTECODE="1")
        result = subprocess.run([sys.executable, "-c", CHILD, PROGRAM, LIBRARY], env=env, capture_output=True,
                                text=True, timeout=90)
        cls.out = dict(line.split(":", 1) for line in result.stdout.splitlines() if ":" in line)
        cls.err = result.stderr[-3000:]

    @classmethod
    def tearDownClass(cls):
        cls.broadway.terminate()
        cls.broadway.wait()
        cls.tmp.cleanup()

    def test_every_setting_found_in_orca(self):
        self.assertGreaterEqual(int(self.out.get("ROWS", "0")), 85, self.err)
        self.assertEqual(self.out.get("UNAVAILABLE"), "", self.err)
        self.assertEqual(self.out.get("UNTITLED"), "0", self.err)

    def test_pages_listed(self):
        pages = self.out.get("PAGES", "")
        for ident in ("profile", "voice", "reading", "typing", "documents", "braille", "keyboard"):
            self.assertIn("=" + ident, pages, self.err)

    def test_every_button_has_a_name(self):
        self.assertEqual(self.out.get("UNNAMED"), "", self.err)

    def test_values_saved(self):
        self.assertEqual(self.out.get("RATE"), "70", self.err)

    def test_program_settings_win_over_the_profile(self):
        self.assertEqual(self.out.get("LAYERS"), "none,all,True", self.err)
        self.assertEqual(self.out.get("RESET"), "all", self.err)

    def test_paths_as_orca(self):
        self.assertEqual(self.out.get("PATHS"),
                         "/org/gnome/orca/default/speech/|/org/gnome/orca/default/apps/ptyxis-terminal/voices/default/",
                         self.err)

    def test_ready_made_profile(self):
        self.assertEqual(self.out.get("PRESET"), "fast,80,brief", self.err)
        self.assertEqual(self.out.get("PROFILES"), "default|fast", self.err)
        self.assertEqual(self.out.get("SELECTED"), "fast", self.err)

    def test_live_setters(self):
        self.assertEqual(self.out.get("SETTER"), "KeyEchoEnabled,SpeechIsEnabled,None,Rate", self.err)

    def test_names_as_orca(self):
        self.assertEqual(self.out.get("SANITIZE"), "studio-2", self.err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
