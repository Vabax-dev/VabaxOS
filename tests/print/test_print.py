#!/usr/bin/env python3
"""Tests for vabaxos-print: what CUPS and SANE say, the commands, and the
window with made-up lpstat, lpoptions, lp and scanimage on Broadway.

    python3 tests/print/test_print.py
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
ROOT = os.path.join(REPO, "packages", "vabaxos-print", "root")
LIB = os.path.join(ROOT, "usr", "lib", "python3", "dist-packages")
PROGRAM = os.path.join(ROOT, "usr", "bin", "vabaxos-print")
sys.path.insert(0, LIB)

import vabaxos_print as vp  # noqa: E402


class ParseTest(unittest.TestCase):

    def test_printers(self):
        self.assertEqual(vp.parse_destinations("HP_LaserJet_M110w\nEpson_ET_2850\n\n"),
                         ["HP_LaserJet_M110w", "Epson_ET_2850"])
        self.assertEqual(vp.parse_default("system default destination: Epson_ET_2850\n"), "Epson_ET_2850")
        self.assertIsNone(vp.parse_default("no system default destination\n"))
        self.assertEqual(vp.printer_title("HP_LaserJet_M110w"), "HP LaserJet M110w")

    def test_scanners(self):
        text = ("device `airscan:e0:HP LaserJet M110w' is a eSCL HP LaserJet M110w ip=192.168.1.20\n"
                "device `escl:https://192.168.1.21:443' is a ESCL Epson ET-2850\n")
        self.assertEqual(vp.parse_scanners(text), [
            ("airscan:e0:HP LaserJet M110w", "eSCL HP LaserJet M110w ip=192.168.1.20"),
            ("escl:https://192.168.1.21:443", "ESCL Epson ET-2850")])

    def test_commands(self):
        self.assertEqual(vp.default_command("Epson"), ["lpoptions", "-d", "Epson"])
        self.assertEqual(vp.print_command("Epson", "/tmp/a.txt"), ["lp", "-d", "Epson", "/tmp/a.txt"])
        command = vp.scan_command("airscan:e0:HP", "/tmp/s.png")
        self.assertIn("--resolution=300", command)
        self.assertEqual(command[-2:], ["-o", "/tmp/s.png"])
        self.assertIn("printer works", vp.test_page_text())

    def test_no_cups_browsed(self):
        pin = os.path.join(ROOT, "etc", "apt", "preferences.d", "vabaxos-no-cups-browsed")
        text = open(pin, encoding="utf-8").read()
        self.assertIn("Package: cups-browsed", text)
        self.assertIn("Pin-Priority: -1", text)


CHILD = r'''
import importlib.machinery, importlib.util, sys
loader = importlib.machinery.SourceFileLoader("printprog", sys.argv[1])
spec = importlib.util.spec_from_loader("printprog", loader)
program = importlib.util.module_from_spec(spec)
loader.exec_module(program)
from gi.repository import Adw, GLib, Gtk
calls, opened = [], []
OUT = {"lpstat -e": "HP_LaserJet_M110w\nEpson_ET_2850\n", "lpstat -d": "system default destination: Epson_ET_2850\n",
       "scanimage -L": "device `airscan:e0:HP' is a eSCL HP LaserJet\n"}
def runner(command):
    calls.append(" ".join(command[:2]))
    return True, OUT.get(" ".join(command[:2]), "")
App, Window = program.window_classes(runner=runner, opener=opened.append)

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

app = Adw.Application(application_id="org.vabaxos.PrintTest")
def check(app):
    window = Window(app)
    window.present()
    def later():
        print("ROWS:" + "|".join(r.get_title() + "/" + (r.get_subtitle() or "") for _g, r in window.rows), flush=True)
        window.make_default("HP_LaserJet_M110w")
        window.scan("airscan:e0:HP")
        GLib.timeout_add(500, finish)
        return False
    def finish():
        print("CALLS:" + ",".join(c for c in calls if not c.startswith("lpstat") and not c.startswith("scanimage -L")),
              flush=True)
        print("OPENED:%s" % (opened and opened[-1][0]), flush=True)
        unnamed = [type(w).__name__ for w in walk(window) if isinstance(w, Gtk.Button) and w.get_mapped()
                   and not w.get_label() and not w.get_tooltip_text() and not inner(w)]
        print("UNNAMED:" + ",".join(unnamed), flush=True)
        app.quit()
        return False
    GLib.timeout_add(500, later)
app.connect("activate", check)
app.run([])
'''


def free_display():
    for number in range(60, 100):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", 8080 + number)) != 0:
                return number
    raise RuntimeError("no free Broadway display")


@unittest.skipUnless(shutil.which("gtk4-broadwayd"), "gtk4-broadwayd (libgtk-4-bin) is not installed")
class WindowTest(unittest.TestCase):

    def test_window(self):
        display = free_display()
        broadway = subprocess.Popen(["gtk4-broadwayd", f":{display}"], stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
        time.sleep(1)
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, GDK_BACKEND="broadway", BROADWAY_DISPLAY=f":{display}",
                       GSETTINGS_BACKEND="memory", NO_AT_BRIDGE="1", PYTHONPATH=LIB, LANGUAGE="C",
                       LANG="C.UTF-8", PYTHONDONTWRITEBYTECODE="1",
                       HOME=tmp, XDG_CACHE_HOME=os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache")),
                       XDG_CONFIG_HOME=os.path.join(tmp, "config"))
            try:
                result = subprocess.run([sys.executable, "-c", CHILD, PROGRAM], env=env, capture_output=True,
                                        text=True, timeout=60)
            finally:
                broadway.terminate()
                broadway.wait()
        out = dict(line.split(":", 1) for line in result.stdout.splitlines() if ":" in line)
        err = result.stderr[-2000:]
        self.assertEqual(out.get("ROWS"), "HP LaserJet M110w/|Epson ET 2850/default printer|eSCL HP LaserJet/", err)
        self.assertEqual(out.get("CALLS"), "lpoptions -d,scanimage -d", err)
        self.assertEqual(out.get("UNNAMED"), "", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
