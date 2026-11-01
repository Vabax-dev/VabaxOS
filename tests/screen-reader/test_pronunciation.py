#!/usr/bin/env python3
"""Tests for the pronunciation dictionary of the screen reader: the words
VabaxOS starts with, add and remove, the dconf defaults, and the window
on Broadway with Orca's schema in memory.

    python3 tests/screen-reader/test_pronunciation.py
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
ROOT = os.path.join(REPO, "packages", "vabaxos-screen-reader", "root")
LIB = os.path.join(ROOT, "usr", "lib", "python3", "dist-packages")
PROGRAM = os.path.join(ROOT, "usr", "bin", "vabaxos-pronunciation")
sys.path.insert(0, LIB)

from vabaxos_screen_reader import pronunciation as pr  # noqa: E402


class DictionaryTest(unittest.TestCase):

    def test_defaults(self):
        entries = pr.defaults()
        self.assertEqual(entries["txt"], "T X T")
        self.assertEqual(entries["pdf"], "P D F")
        self.assertEqual(entries["vabaxos"], "Vabax O S")
        for word in ("iva", "spid", "iso", "zip", "pin"):
            self.assertNotIn(word, entries, "said as a word in Italian")
        self.assertTrue(all(k == k.lower() for k in entries))

    def test_add_and_remove(self):
        entries = pr.add({}, "  Nvidia ", "envidia")
        self.assertEqual(entries, {"nvidia": "envidia"})
        self.assertEqual(pr.remove(entries, "NVIDIA"), {})
        with self.assertRaises(ValueError):
            pr.add({}, "two words", "x")
        with self.assertRaises(ValueError):
            pr.add({}, "word", "  ")

    def test_dconf_file(self):
        from gi.repository import GLib
        text = pr.dconf_defaults()
        self.assertIn("[org/gnome/orca/default/pronunciations]", text)
        line = next(l for l in text.splitlines() if l.startswith("entries="))
        value = GLib.Variant.parse(GLib.VariantType("a{ss}"), line[len("entries="):], None, None)
        self.assertEqual(dict(value.unpack()), pr.defaults())
        tricky = pr.variant_text({"l'uomo": "lo 'uomo'"})
        self.assertEqual(dict(GLib.Variant.parse(GLib.VariantType("a{ss}"), tricky, None, None).unpack()),
                         {"l'uomo": "lo 'uomo'"})


CHILD = r'''
import importlib.machinery, importlib.util, sys
loader = importlib.machinery.SourceFileLoader("pron", sys.argv[1])
spec = importlib.util.spec_from_loader("pron", loader)
program = importlib.util.module_from_spec(spec)
loader.exec_module(program)
from gi.repository import Adw, GLib, Gtk
from vabaxos_screen_reader import store

class FakeOrca:
    reloads, said = 0, []
    def reload(self): FakeOrca.reloads += 1
    def present(self, text): FakeOrca.said.append(text)

def walk(widget):
    yield widget
    child = widget.get_first_child()
    while child is not None:
        yield from walk(child)
        child = child.get_next_sibling()

def inner(w):
    while w is not None:
        if type(w).__name__ in ("AdwToastWidget", "WindowControls"):
            return True
        w = w.get_parent()
    return False

app = Adw.Application(application_id="org.vabaxos.PronunciationTest")
def check(app):
    window = program.PronunciationWindow(app, store.Store(), FakeOrca())
    window.present()
    window.settings.set_value("entries", GLib.Variant("a{ss}", {"txt": "T X T"}))
    window.fill()
    print("ROWS:" + "|".join(r.get_title() + "=" + r.get_subtitle() for r in window.rows), flush=True)
    window.word.set_text("Nvidia")
    window.saying.set_text("envidia")
    window.add()
    print("AFTER:" + ",".join(sorted(window.entries())), flush=True)
    print("RELOADS:%d" % FakeOrca.reloads, flush=True)
    window.delete("txt")
    print("LEFT:" + ",".join(sorted(window.entries())), flush=True)
    unnamed = [type(w).__name__ for w in walk(window) if isinstance(w, Gtk.Button) and w.get_mapped()
               and not w.get_label() and not w.get_tooltip_text() and not inner(w)]
    print("UNNAMED:" + ",".join(unnamed), flush=True)
    app.quit()
app.connect("activate", check)
app.run([])
'''


def free_display():
    for number in range(60, 100):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", 8080 + number)) != 0:
                return number
    raise RuntimeError("no free Broadway display")


@unittest.skipUnless(shutil.which("gtk4-broadwayd") and shutil.which("glib-compile-schemas"),
                     "gtk4-broadwayd or glib-compile-schemas is missing")
class WindowTest(unittest.TestCase):

    def test_window(self):
        with tempfile.TemporaryDirectory() as schemas:
            shutil.copy(os.path.join(HERE, "org.gnome.Orca.gschema.xml"), schemas)
            subprocess.run(["glib-compile-schemas", schemas], check=True)
            display = free_display()
            broadway = subprocess.Popen(["gtk4-broadwayd", f":{display}"], stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL)
            time.sleep(1)
            env = dict(os.environ, GDK_BACKEND="broadway", BROADWAY_DISPLAY=f":{display}",
                       GSETTINGS_BACKEND="memory", GSETTINGS_SCHEMA_DIR=schemas, NO_AT_BRIDGE="1",
                       PYTHONPATH=LIB, LANGUAGE="C", LANG="C.UTF-8", PYTHONDONTWRITEBYTECODE="1")
            try:
                result = subprocess.run([sys.executable, "-c", CHILD, PROGRAM], env=env, capture_output=True,
                                        text=True, timeout=60)
            finally:
                broadway.terminate()
                broadway.wait()
        out = dict(line.split(":", 1) for line in result.stdout.splitlines() if ":" in line)
        err = result.stderr[-2000:]
        self.assertEqual(out.get("ROWS"), "txt=said: T X T", err)
        self.assertEqual(out.get("AFTER"), "nvidia,txt", err)
        self.assertEqual(out.get("RELOADS"), "1", err)
        self.assertEqual(out.get("LEFT"), "nvidia", err)
        self.assertEqual(out.get("UNNAMED"), "", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
