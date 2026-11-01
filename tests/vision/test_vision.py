#!/usr/bin/env python3
"""Tests for vabaxos-vision: zoom, contrast, text, pointer and colours on
GNOME's real settings kept in memory, the keys in dconf, and the window
on Broadway.

    python3 tests/vision/test_vision.py
"""

import configparser
import os
import shutil
import socket
import subprocess
import sys
import time
import unittest

os.environ["GSETTINGS_BACKEND"] = "memory"

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ROOT = os.path.join(REPO, "packages", "vabaxos-vision", "root")
LIB = os.path.join(ROOT, "usr", "lib", "python3", "dist-packages")
PROGRAM = os.path.join(ROOT, "usr", "bin", "vabaxos-vision")
SHORTCUTS = os.path.join(REPO, "packages", "vabaxos-settings", "root", "etc", "dconf", "db", "vabaxos.d",
                         "20-shortcuts")
sys.path.insert(0, LIB)

import vabaxos_vision as vv  # noqa: E402


def have_schemas():
    try:
        from gi.repository import Gio
        source = Gio.SettingsSchemaSource.get_default()
        return all(source.lookup(s, True) for s in (vv.MAGNIFIER, vv.APPLICATIONS, vv.INTERFACE))
    except Exception:  # noqa: BLE001
        return False


class StepsTest(unittest.TestCase):

    def test_zoom_steps(self):
        self.assertEqual([vv.zoom_steps(f, True) for f in (1.5, 3.5, 4.0, 15.5, 16.0)], [2.0, 4.0, 5.0, 16.0, 16.0])
        self.assertEqual([vv.zoom_steps(f, False) for f in (5.0, 4.0, 1.5, 1.0)], [4.0, 3.5, 1.0, 1.0])
        self.assertEqual(vv.number(2.0), "2")
        self.assertEqual(vv.number(1.25), "1.25")


@unittest.skipUnless(have_schemas(), "gsettings-desktop-schemas is not installed")
class VisionTest(unittest.TestCase):

    def setUp(self):
        from gi.repository import Gio
        for schema in (vv.MAGNIFIER, vv.APPLICATIONS, vv.INTERFACE, vv.A11Y):
            settings = Gio.Settings.new(schema)
            for key in settings.list_keys():
                settings.reset(key)
        self.v = vv.Vision()

    def test_zoom(self):
        self.assertEqual(self.v.zoom_out(), "Zoom is off.")
        self.assertEqual(self.v.zoom_in(), "Zoom 2 times.")
        self.assertTrue(self.v.zoom_on())
        self.assertEqual(self.v.zoom_in(), "Zoom 2.5 times.")
        for _ in range(4):
            self.v.zoom_out()
        self.assertFalse(self.v.zoom_on(), "zooming out at 1 turns the zoom off")
        self.assertEqual(self.v.zoom_toggle(), "Zoom 1.5 times.")
        self.assertEqual(self.v.zoom_toggle(), "Zoom off.")

    def test_contrast_text_pointer(self):
        self.assertEqual(self.v.contrast(), "High contrast on.")
        self.assertEqual(self.v.contrast(), "High contrast off.")
        self.assertEqual(self.v.text(True), "Text 1.25 times bigger.")
        self.assertEqual(self.v.text(False), "Text of normal size.")
        self.assertEqual(self.v.text(False), "Text of normal size.")
        self.assertEqual([self.v.pointer() for _ in range(4)],
                         ["Pointer 2 times bigger.", "Pointer 2.67 times bigger.", "Pointer 4 times bigger.",
                          "Normal pointer."])

    def test_colours_turn_the_zoom_on_at_one(self):
        self.assertEqual(self.v.invert(), "Colours inverted.")
        self.assertTrue(self.v.zoom_on())
        self.assertEqual(self.v.get(vv.MAGNIFIER, "mag-factor"), 1.0)
        self.assertEqual(self.v.greyscale(), "Black and white.")
        self.assertEqual(self.v.greyscale(), "Colours back.")
        self.assertEqual(self.v.status(), "Zoom 1 times. High contrast off. Text of normal size.")

    def test_missing_setting(self):
        v = vv.Vision(settings=lambda schema: None)
        self.assertEqual(v.contrast(), "This setting is not on this system.")


class KeysTest(unittest.TestCase):

    def test_keys_in_dconf(self):
        config = configparser.ConfigParser(interpolation=None)
        config.read(SHORTCUTS, encoding="utf-8")
        listed = config["org/gnome/settings-daemon/plugins/media-keys"]["custom-keybindings"]
        bindings = {}
        for section in config.sections():
            if "/custom-keybindings/" in section:
                self.assertIn(f"/{section}/", listed, section)
                bindings[config[section]["binding"].strip("'")] = config[section]["command"].strip("'")
        self.assertEqual(len(bindings), len([s for s in config.sections() if "/custom-keybindings/" in s]),
                         "no key twice")
        self.assertEqual(bindings["<Super>plus"], "vabaxos-vision zoom-in")
        self.assertEqual(bindings["<Super>KP_Subtract"], "vabaxos-vision zoom-out")
        self.assertEqual(bindings["<Super><Control>c"], "vabaxos-vision contrast")
        for command in bindings.values():
            if command.startswith("vabaxos-vision "):
                program = __import__("importlib.machinery").machinery.SourceFileLoader("v", PROGRAM).load_module()
                self.assertIn(command.split()[1], program.COMMANDS)


CHILD = r'''
import importlib.machinery, importlib.util, sys
loader = importlib.machinery.SourceFileLoader("visionprog", sys.argv[1])
spec = importlib.util.spec_from_loader("visionprog", loader)
program = importlib.util.module_from_spec(spec)
loader.exec_module(program)
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk
import vabaxos_vision as vv

said = []
v = vv.Vision()
App, Window = program.window_classes(speak=said.append, vision=v)
app = Adw.Application(application_id="org.vabaxos.VisionTest")

def walk(widget):
    child = widget.get_first_child()
    while child:
        yield child
        yield from walk(child)
        child = child.get_next_sibling()

def check(app):
    window = Window(app)
    window.present()
    def step():
        window.rows["contrast"].set_active(True)
        print("CONTRAST:" + str(v.get(vv.A11Y, "high-contrast")), flush=True)
        window.rows["invert"].set_active(True)
        print("INVERT:" + said[-1] + " " + str(v.zoom_on()), flush=True)
        window.factor.set_value(3.0)
        print("FACTOR:" + str(v.get(vv.MAGNIFIER, "mag-factor")), flush=True)
        window.follow.set_selected(0)
        print("FOLLOW:" + v.get(vv.MAGNIFIER, "focus-tracking") + " " + v.get(vv.MAGNIFIER, "caret-tracking"),
              flush=True)
        window.pointer.set_selected(1)
        print("POINTER:" + str(v.get(vv.INTERFACE, "cursor-size")), flush=True)
        def inner(w):
            while w is not None:
                if type(w).__name__ in ("SpinButton", "WindowControls", "ToastWidget", "AdwToastWidget"):
                    return True
                w = w.get_parent()
            return False
        unnamed = [type(w).__name__ + "<" + type(w.get_parent()).__name__ for w in walk(window)
                   if isinstance(w, Gtk.Button) and w.get_mapped() and not w.get_label()
                   and not w.get_tooltip_text() and not inner(w)]
        print("UNNAMED:" + ",".join(unnamed), flush=True)
        app.quit()
        return False
    GLib.timeout_add(400, step)

app.connect("activate", check)
app.hold()
app.run([])
'''


def free_display():
    for number in range(60, 100):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", 8080 + number)) != 0:
                return number
    raise RuntimeError("no free Broadway display")


@unittest.skipUnless(shutil.which("gtk4-broadwayd") and have_schemas(), "Broadway or GNOME schemas missing")
class WindowTest(unittest.TestCase):

    def test_window(self):
        display = free_display()
        broadway = subprocess.Popen(["gtk4-broadwayd", f":{display}"], stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
        time.sleep(1)
        env = dict(os.environ, GDK_BACKEND="broadway", BROADWAY_DISPLAY=f":{display}", GSETTINGS_BACKEND="memory",
                   NO_AT_BRIDGE="1", PYTHONPATH=LIB, LANGUAGE="C", LANG="C.UTF-8", PYTHONDONTWRITEBYTECODE="1")
        try:
            result = subprocess.run([sys.executable, "-c", CHILD, PROGRAM], env=env, capture_output=True, text=True,
                                    timeout=60, check=False)
        finally:
            broadway.terminate()
            broadway.wait()
        out = dict(line.split(":", 1) for line in result.stdout.splitlines() if ":" in line)
        err = result.stderr[-3000:]
        self.assertEqual(out.get("CONTRAST"), "True", err)
        self.assertEqual(out.get("INVERT"), "Colours inverted. True", err)
        self.assertEqual(out.get("FACTOR"), "3.0", err)
        self.assertEqual(out.get("FOLLOW"), "centered centered", err)
        self.assertEqual(out.get("POINTER"), "48", err)
        self.assertEqual(out.get("UNNAMED"), "", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
