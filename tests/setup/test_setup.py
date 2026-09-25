#!/usr/bin/env python3
"""Tests for vabaxos-setup (ADR-0010), without a visible window and without
changing the real settings.

GTK runs on a Broadway display (gtk4-broadwayd), which shows nothing on the
screen, and GSettings keeps its values in memory. The tests check that every
row and button has a name the screen reader can read, that settings change,
and that Back and Next update the title.

    python3 tests/setup/test_setup.py
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
PROGRAM = os.path.join(REPO, "packages", "vabaxos-setup", "root", "usr", "bin", "vabaxos-setup")

CHILD = r'''
import importlib.machinery, importlib.util, sys
loader = importlib.machinery.SourceFileLoader("vabaxos_setup", sys.argv[1])
spec = importlib.util.spec_from_loader("vabaxos_setup", loader)
setup = importlib.util.module_from_spec(spec)
loader.exec_module(setup)
from gi.repository import Adw, Gio, GLib, Gtk

problems = []
app = setup.SetupApp()

def walk(widget):
    yield widget
    child = widget.get_first_child()
    while child is not None:
        yield from walk(child)
        child = child.get_next_sibling()

def inside(widget, kind):
    parent = widget.get_parent()
    while parent is not None:
        if isinstance(parent, kind):
            return True
        parent = parent.get_parent()
    return False

def check(app):
    window = setup.SetupWindow(app)
    window.present()
    titles = []
    for index in range(len(window.pages)):
        window.show_page(index)
        titles.append(window.get_title())
        page = window.stack.get_visible_child()
        for widget in walk(page):
            if isinstance(widget, Adw.PreferencesRow) and not widget.get_title():
                problems.append(f"row without title on page {index}")
            # Our own buttons need a visible label; the + and - buttons inside
            # a Gtk.SpinButton are labelled by GTK itself.
            if isinstance(widget, Gtk.Button) and not inside(widget, Gtk.SpinButton):
                if not widget.get_label() and not widget.get_tooltip_text():
                    problems.append(f"button without label on page {index}: {type(widget).__name__}")
    for widget in (window.back, window.next):
        if not widget.get_label():
            problems.append("navigation button without label")
    print("TITLES:" + "|".join(titles))
    # A switch changes its setting at once.
    window.show_page(0)
    rows = [w for w in walk(window.stack.get_visible_child()) if isinstance(w, Adw.SwitchRow)]
    contrast = next(r for r in rows if r.get_title() == "High contrast")
    contrast.set_active(True)
    value = Gio.Settings.new("org.gnome.desktop.a11y.interface").get_boolean("high-contrast")
    print(f"CONTRAST:{value}")
    # Next and Back.
    window.next.emit("clicked")
    print("AFTER_NEXT:" + window.get_title())
    window.back.emit("clicked")
    print("AFTER_BACK:" + window.get_title())
    print("PROBLEMS:" + "|".join(problems))
    app.quit()

app.connect("activate", check)
app.run([])
'''


def free_display():
    for number in range(20, 60):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", 8080 + number)) != 0:
                return number
    raise RuntimeError("no free Broadway display")


@unittest.skipUnless(shutil.which("gtk4-broadwayd"), "gtk4-broadwayd (libgtk-4-bin) is not installed")
class SetupTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.display = free_display()
        cls.broadway = subprocess.Popen(["gtk4-broadwayd", f":{cls.display}"],
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
        cls.config = tempfile.TemporaryDirectory()
        env = dict(os.environ, GDK_BACKEND="broadway", BROADWAY_DISPLAY=f":{cls.display}",
                   GSETTINGS_BACKEND="memory", XDG_CONFIG_HOME=cls.config.name,
                   LANGUAGE="C", LANG="C.UTF-8", PYTHONDONTWRITEBYTECODE="1", NO_AT_BRIDGE="1")
        result = subprocess.run([sys.executable, "-c", CHILD, PROGRAM], env=env,
                                capture_output=True, text=True, timeout=60)
        cls.output = {}
        for line in result.stdout.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                cls.output[key] = value
        cls.stderr = result.stderr

    @classmethod
    def tearDownClass(cls):
        cls.broadway.terminate()
        cls.broadway.wait()
        cls.config.cleanup()

    def test_every_page_has_a_numbered_title(self):
        titles = self.output.get("TITLES", "").split("|")
        self.assertEqual(len(titles), 5, self.stderr)
        self.assertEqual(titles[0], "VabaxOS setup: View, step 1 of 5")
        self.assertEqual(titles[4], "VabaxOS setup: Finish, step 5 of 5")

    def test_rows_and_buttons_have_names(self):
        self.assertEqual(self.output.get("PROBLEMS", "missing"), "", self.stderr)

    def test_a_switch_changes_the_setting(self):
        self.assertEqual(self.output.get("CONTRAST"), "True", self.stderr)

    def test_next_and_back(self):
        self.assertEqual(self.output.get("AFTER_NEXT"), "VabaxOS setup: Voice, step 2 of 5")
        self.assertEqual(self.output.get("AFTER_BACK"), "VabaxOS setup: View, step 1 of 5")


if __name__ == "__main__":
    unittest.main(verbosity=2)
