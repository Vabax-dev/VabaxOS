#!/usr/bin/env python3
"""Tests for vabaxos-apps, on a hidden Broadway display, with two made-up
programs in a temporary folder: nothing on the system changes.

    python3 tests/apps/test_apps.py
"""

import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROGRAM = os.path.join(REPO, "packages", "vabaxos-apps", "root", "usr", "bin", "vabaxos-apps")

CHILD = r'''
import importlib.machinery, importlib.util, os, sys
loader = importlib.machinery.SourceFileLoader("apps", sys.argv[1])
spec = importlib.util.spec_from_loader("apps", loader)
apps = importlib.util.module_from_spec(spec)
loader.exec_module(apps)
from gi.repository import Adw, GLib, Gtk

def walk(widget):
    yield widget
    child = widget.get_first_child()
    while child is not None:
        yield from walk(child)
        child = child.get_next_sibling()

app = apps.AppsApplication()
def check(application):
    window = apps.AppsWindow(application)
    window.present()
    titles = [row.get_title() for row, _name in window.rows]
    print("ROWS:" + "|".join(titles), flush=True)
    unnamed = [type(w).__name__ for w in walk(window) if isinstance(w, Gtk.Button) and w.get_mapped()
               and not w.get_label() and not w.get_tooltip_text()
               and not any(w.get_ancestor(k) for k in (Gtk.WindowControls, Gtk.SearchEntry))]
    print("UNNAMED:" + ",".join(unnamed), flush=True)
    switch = next(w for w in walk(window.rows[0][0]) if isinstance(w, Gtk.Switch))
    switch.set_active(True)
    target = os.path.join(os.environ["XDG_CONFIG_HOME"], "autostart", "vabaxos-test-alpha.desktop")
    print("AUTOSTART:%s" % os.path.exists(target), flush=True)
    switch.set_active(False)
    print("AUTOSTART_OFF:%s" % (not os.path.exists(target)), flush=True)
    window.search.set_text("beta")
    window.filter()
    print("VISIBLE:" + "|".join(r.get_title() for r, _n in window.rows if r.get_visible()), flush=True)
    print("PROTECTED:%s,%s" % (apps.protected(("deb", "orca")), apps.protected(("deb", "gimp"))), flush=True)
    application.quit()
app.connect("activate", check)
app.run([])
'''

DESKTOP = """[Desktop Entry]
Type=Application
Name={name}
Comment={name} test program
Exec=true
"""


def free_display():
    for number in range(100, 140):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", 8080 + number)) != 0:
                return number
    raise RuntimeError("no free Broadway display")


@unittest.skipUnless(shutil.which("gtk4-broadwayd"), "gtk4-broadwayd (libgtk-4-bin) is not installed")
class AppsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        data = os.path.join(cls.tmp.name, "data", "applications")
        os.makedirs(data)
        for ident, name in (("vabaxos-test-alpha", "Alpha"), ("vabaxos-test-beta", "Beta")):
            with open(os.path.join(data, ident + ".desktop"), "w", encoding="utf-8") as f:
                f.write(DESKTOP.format(name=name))
        display = free_display()
        cls.broadway = subprocess.Popen(["gtk4-broadwayd", f":{display}"], stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL)
        time.sleep(1)
        env = dict(os.environ, GDK_BACKEND="broadway", BROADWAY_DISPLAY=f":{display}",
                   GSETTINGS_BACKEND="memory", NO_AT_BRIDGE="1", LANGUAGE="C", LANG="C.UTF-8",
                   XDG_DATA_DIRS=os.path.join(cls.tmp.name, "data"), XDG_DATA_HOME=os.path.join(cls.tmp.name, "home"),
                   XDG_CONFIG_HOME=os.path.join(cls.tmp.name, "config"), PYTHONDONTWRITEBYTECODE="1")
        result = subprocess.run([sys.executable, "-c", CHILD, PROGRAM], env=env, capture_output=True,
                                text=True, timeout=60)
        cls.out = dict(line.split(":", 1) for line in result.stdout.splitlines() if ":" in line)
        cls.err = result.stderr[-2000:]

    @classmethod
    def tearDownClass(cls):
        cls.broadway.terminate()
        cls.broadway.wait()
        cls.tmp.cleanup()

    def test_programs_listed(self):
        self.assertEqual(self.out.get("ROWS"), "Alpha|Beta", self.err)

    def test_every_button_has_a_name(self):
        self.assertEqual(self.out.get("UNNAMED"), "", self.err)

    def test_start_at_login(self):
        self.assertEqual(self.out.get("AUTOSTART"), "True", self.err)
        self.assertEqual(self.out.get("AUTOSTART_OFF"), "True", self.err)

    def test_search(self):
        self.assertEqual(self.out.get("VISIBLE"), "Beta", self.err)

    def test_voice_and_desktop_cannot_be_removed(self):
        self.assertEqual(self.out.get("PROTECTED"), "True,False", self.err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
