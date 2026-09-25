#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Vabax and VabaxOS contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for the VabaxOS Start menu (block 12), on a hidden Broadway display
with made-up programs in a temporary folder: categories, search, the keys
of the tree (Right expands, Left goes back, letters jump).

    python3 tests/start/test_start.py
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
ROOT = os.path.join(REPO, "packages", "vabaxos-start", "root")
PROGRAM = os.path.join(ROOT, "usr", "bin", "vabaxos-start")
LIBRARY = os.path.join(ROOT, "usr", "lib", "python3", "dist-packages")

CHILD = r'''
import importlib.machinery, importlib.util, sys
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
sys.path.insert(0, sys.argv[2])
from gi.repository import Adw, Gdk, GLib, Gtk
from vabaxos_start import menu
menu.recent_files = lambda limit=15: []
loader = importlib.machinery.SourceFileLoader("start", sys.argv[1])
spec = importlib.util.spec_from_loader("start", loader)
start = importlib.util.module_from_spec(spec)
loader.exec_module(start)

cats = menu.build()
print("CATEGORIES:" + "|".join(c.ident for c in cats), flush=True)
programs = next(c for c in cats if c.ident == "programs")
print("GROUPS:" + "|".join(g.ident for g in programs.children), flush=True)
print("SEARCH:" + "|".join(e.name for e in menu.search(cats, "wri")), flush=True)
print("KEYWORD:" + "|".join(e.name for e in menu.search(cats, "posta")), flush=True)
print("ACCENT:" + "|".join(e.name for e in menu.search(cats, "citta")), flush=True)
print("POWER:" + "|".join(e.name for e in menu.search(cats, "power off")), flush=True)

def check(application):
    try:
        window = start.StartWindow(application)
        window.show_menu()
    except Exception:  # noqa: BLE001 - shown in the test failure
        import traceback
        traceback.print_exc()
        application.quit()
        return
    def steps():
        try:
            run_steps()
        except Exception:  # noqa: BLE001 - shown in the test failure
            import traceback
            traceback.print_exc()
        application.quit()
        return False

    def run_steps():
        model = window.tree_model
        names = lambda: [model.get_item(i).get_item().entry.name for i in range(model.get_n_items())]
        print("TOP:" + "|".join(names()), flush=True)
        position = names().index("Programs")
        window.focus_position(position)
        window.tree_key(None, Gdk.KEY_Right, 0, 0)          # expands Programs
        expanded = model.get_item(position).get_expanded()
        window.tree_key(None, Gdk.KEY_Right, 0, 0)          # into its first group
        inside = window.selection.get_selected() == position + 1
        window.tree_key(None, Gdk.KEY_Left, 0, 0)           # back to Programs
        back = window.selection.get_selected() == position
        window.tree_key(None, Gdk.KEY_Left, 0, 0)           # collapses it
        collapsed = not model.get_item(position).get_expanded()
        print("TREE:%s,%s,%s,%s" % (expanded, inside, back, collapsed), flush=True)
        window.tree_key(None, Gdk.KEY_f, 0, 0)
        print("JUMP:%s" % model.get_item(window.selection.get_selected()).get_item().entry.name, flush=True)
        window.search.set_text("wri")
        window.update_results()
        rows = [window.results.get_row_at_index(i) for i in range(20)]
        print("RESULTS:%s,%d" % (window.stack.get_visible_child_name(), len([r for r in rows if r])), flush=True)
        window.search.set_text("zzzz")
        window.update_results()
        print("NONE:%s" % window.stack.get_visible_child_name(), flush=True)
        window.window_key(None, Gdk.KEY_Escape, 0, 0)       # clears the search
        cleared = window.search.get_text() == ""
        window.window_key(None, Gdk.KEY_Escape, 0, 0)       # closes the menu
        print("ESCAPE:%s,%s" % (cleared, window.get_visible()), flush=True)
    GLib.timeout_add(500, steps)
    GLib.timeout_add_seconds(40, lambda: (print("TIMEOUT: the steps did not finish", flush=True),
                                          application.quit()))

app = Adw.Application(application_id="org.vabaxos.StartTest")
app.connect("activate", check)
app.hold()
app.run([])
'''

DESKTOP = """[Desktop Entry]
Type=Application
Name={name}
Keywords={keywords}
Categories={categories}
Exec=true
"""
PROGRAMS = [
    ("writer", "Writer", "document;word;", "Office;WordProcessor;"),
    ("mail", "Mail", "posta;email;", "Network;Email;"),
    ("citta", "Città", "", "Education;"),
    ("sound", "Sound Recorder", "", "AudioVideo;Audio;"),
    ("orca", "Screen Reader", "", "Accessibility;Utility;"),
    ("org.vabaxos.Apps", "VabaxOS programs", "", "System;"),
]


def free_display():
    for number in range(180, 220):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", 8080 + number)) != 0:
                return number
    raise RuntimeError("no free Broadway display")


@unittest.skipUnless(shutil.which("gtk4-broadwayd"), "gtk4-broadwayd (libgtk-4-bin) is not installed")
class StartTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        data = os.path.join(cls.tmp.name, "data", "applications")
        os.makedirs(data)
        for ident, name, keywords, categories in PROGRAMS:
            with open(os.path.join(data, ident + ".desktop"), "w", encoding="utf-8") as f:
                f.write(DESKTOP.format(name=name, keywords=keywords, categories=categories))
        home = os.path.join(cls.tmp.name, "home")
        os.makedirs(os.path.join(home, "Documents"))
        display = free_display()
        cls.broadway = subprocess.Popen(["gtk4-broadwayd", f":{display}"], stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL)
        time.sleep(1)
        env = dict(os.environ, GDK_BACKEND="broadway", BROADWAY_DISPLAY=f":{display}",
                   GSETTINGS_BACKEND="memory", NO_AT_BRIDGE="1", LANGUAGE="C", LANG="C.UTF-8", HOME=home,
                   XDG_DATA_DIRS=os.path.join(cls.tmp.name, "data"), XDG_DATA_HOME=os.path.join(home, ".local"),
                   XDG_CONFIG_HOME=os.path.join(home, ".config"), PYTHONDONTWRITEBYTECODE="1")
        result = subprocess.run([sys.executable, "-c", CHILD, PROGRAM, LIBRARY], env=env, capture_output=True,
                                text=True, timeout=90)
        cls.out = dict(line.split(":", 1) for line in result.stdout.splitlines() if ":" in line)
        cls.err = result.stderr[-3000:]

    @classmethod
    def tearDownClass(cls):
        cls.broadway.terminate()
        cls.broadway.wait()
        cls.tmp.cleanup()

    def test_categories(self):
        categories = self.out.get("CATEGORIES", "")
        for ident in ("programs", "vabaxos", "folders", "power"):
            self.assertIn(ident, categories, self.err)

    def test_programs_divided_as_in_windows(self):
        groups = self.out.get("GROUPS", "")
        for ident in ("office", "internet", "media", "accessibility", "education", "system"):
            self.assertIn(ident, groups, self.err)

    def test_search(self):
        self.assertEqual(self.out.get("SEARCH", "").split("|")[0], "Writer", self.err)
        self.assertIn("Mail", self.out.get("KEYWORD", ""), self.err)
        self.assertIn("Città", self.out.get("ACCENT", ""), self.err)
        self.assertEqual(self.out.get("POWER"), "Power off", self.err)

    def test_tree_keys(self):
        self.assertEqual(self.out.get("TREE"), "True,True,True,True", self.err)
        self.assertEqual(self.out.get("JUMP"), "Folders", self.err)

    def test_results_and_escape(self):
        self.assertTrue(self.out.get("RESULTS", "").startswith("results,"), self.err)
        self.assertEqual(self.out.get("NONE"), "none", self.err)
        self.assertEqual(self.out.get("ESCAPE"), "True,False", self.err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
