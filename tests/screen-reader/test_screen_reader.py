#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Vabax and VabaxOS contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for vabaxos-screen-reader (block 9, ADR-0027): the window on a
hidden Broadway display, Orca 48's settings files in a temporary data
folder: nothing on the system changes.

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
import json, os
from vabaxos_screen_reader import pages, store
from gi.repository import Adw, GLib, Gtk
store.OrcaService.running = staticmethod(lambda: False)

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
    print("HIDDEN:" + ",".join(sorted(r.setting[1] for r in rows if not r.get_visible())), flush=True)
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
    # As Orca 48 keeps them: its names and numbers, in its files.
    with open(store.settings_path()) as f:
        saved = json.load(f)["profiles"]["default"]
    print("ORCA48:%s,%s,%s" % (saved.get("verbalizePunctuationStyle"), saved["voices"]["default"]["rate"],
                               os.path.exists(store.app_path("ptyxis"))), flush=True)

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
    exported = os.path.join(os.environ["XDG_DATA_HOME"], "export.json")
    store.export_settings(exported)
    store.delete_profile(internal)
    after_delete = "|".join(i for _n, i in store.list_profiles())
    print("EXPORT:%s,%s" % (after_delete, store.import_settings(exported)), flush=True)
    print("IMPORTED:" + "|".join(i for _n, i in store.list_profiles()), flush=True)
    print("SANITIZE:%s" % store.sanitize("Studio 2!"), flush=True)

    # Keys page (block 10): every Orca command, schemes, a key already used.
    from vabaxos_screen_reader import keymaps, orca_commands
    keys = window.keys
    print("KEYROWS:%d/%d" % (len(keys.rows), len(orca_commands.COMMANDS)), flush=True)
    keys.apply_scheme("jaws")
    print("SCHEME:%s,%s" % (keys.current_scheme(), keys.entries() == keymaps.entries("jaws")), flush=True)
    key_row = Adw.EntryRow(); key_row.set_text("T")
    presses = Adw.ComboRow(); presses.set_model(Gtk.StringList.new(["1", "2", "3"])); presses.set_selected(0)
    orca_key = Adw.SwitchRow(active=True)
    keys.change_done(None, "save", "sayAllHandler", "say all", [(orca_key, keymaps.O)], key_row, presses)
    refused = keys.entries()["sayAllHandler"] == keymaps.entries("jaws")["sayAllHandler"]
    key_row.set_text("F9")
    keys.change_done(None, "save", "sayAllHandler", "say all", [(orca_key, keymaps.O)], key_row, presses)
    saved = keys.entries()["sayAllHandler"]
    keys.change_done(None, "none", "sayAllHandler", "say all", [], key_row, presses)
    unbound = keys.entries()["sayAllHandler"]
    print("CHANGE:%s,%s,%s,%s" % (refused, saved, unbound, keys.current_scheme()), flush=True)
    keys.search.set_text("clipboard")
    print("SEARCH:%d" % sum(1 for r, _n, _t in keys.rows if r.get_visible()), flush=True)
    application.quit()

app = Adw.Application(application_id="org.vabaxos.ScreenReaderTest")
app.connect("activate", check)
app.run([])
'''


# Settings of Orca 50 that Orca 48 does not have: their rows are hidden.
MISSING_IN_ORCA48 = ("auto-language-switching,auto-sticky-focus-mode,computer-braille-at-cursor,"
                     "enabled,enabled,end-of-line-indicator")


def free_display():
    for number in range(140, 180):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", 8080 + number)) != 0:
                return number
    raise RuntimeError("no free Broadway display")


@unittest.skipUnless(shutil.which("gtk4-broadwayd"), "gtk4-broadwayd (libgtk-4-bin) is not installed")
class ScreenReaderTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        display = free_display()
        cls.broadway = subprocess.Popen(["gtk4-broadwayd", f":{display}"], stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL)
        time.sleep(1)
        env = dict(os.environ, GDK_BACKEND="broadway", BROADWAY_DISPLAY=f":{display}",
                   GSETTINGS_BACKEND="memory", NO_AT_BRIDGE="1",
                   XDG_DATA_HOME=os.path.join(cls.tmp.name, "data"),
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
        self.assertEqual(self.out.get("HIDDEN"), MISSING_IN_ORCA48, self.err)
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

    def test_saved_as_orca48(self):
        # Punctuation "all" is 0 in Orca 48; the program has its own file.
        self.assertEqual(self.out.get("ORCA48"), "0,70,True", self.err)

    def test_ready_made_profile(self):
        self.assertEqual(self.out.get("PRESET"), "fast,80,brief", self.err)
        self.assertEqual(self.out.get("PROFILES"), "default|fast", self.err)
        self.assertEqual(self.out.get("SELECTED"), "fast", self.err)

    def test_export_and_import(self):
        self.assertEqual(self.out.get("EXPORT"), "default,True", self.err)
        self.assertEqual(self.out.get("IMPORTED"), "default|fast", self.err)

    def test_keys_page(self):
        self.assertEqual(self.out.get("KEYROWS"), "218/218", self.err)
        self.assertEqual(self.out.get("SCHEME"), "1,True", self.err)
        # T with the screen reader key is the title in JAWS: refused; F9 saved;
        # then no key; a changed scheme is "personalized".
        self.assertEqual(self.out.get("CHANGE"), "True,[['F9', '461', '256', '1']],[],3", self.err)
        self.assertGreaterEqual(int(self.out.get("SEARCH", "0")), 1, self.err)

    def test_names_as_orca(self):
        self.assertEqual(self.out.get("SANITIZE"), "studio-2", self.err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
