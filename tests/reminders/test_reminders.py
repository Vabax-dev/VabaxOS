#!/usr/bin/env python3
"""Tests for vabaxos-reminders: sentences as one would say them, the list
on disk, what fires and when, the timekeeper with a made-up bus, and the
window on Broadway.

    python3 tests/reminders/test_reminders.py
"""

import datetime
import importlib.machinery
import importlib.util
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ROOT = os.path.join(REPO, "packages", "vabaxos-reminders", "root")
LIB = os.path.join(ROOT, "usr", "lib", "python3", "dist-packages")
PROGRAM = os.path.join(ROOT, "usr", "bin", "vabaxos-reminders")
sys.path.insert(0, LIB)

import vabaxos_reminders as vr  # noqa: E402

NOW = datetime.datetime(2026, 11, 2, 10, 0)  # a Monday


def at(day, hour, minute=0):
    return datetime.datetime(2026, 11, day, hour, minute)


class ParseTest(unittest.TestCase):

    def check(self, sentence, when, text, alarm=False, daily=False):
        reminder = vr.parse(sentence, NOW)
        self.assertIsNotNone(reminder, sentence)
        self.assertEqual((reminder.when, reminder.text, reminder.alarm, reminder.daily),
                         (when, text, alarm, daily), sentence)

    def test_italian(self):
        self.check("alle 15 chiama Marco", at(2, 15), "Chiama Marco")
        self.check("tra 10 minuti scola la pasta", at(2, 10, 10), "Scola la pasta")
        self.check("domani alle 7.30 sveglia", at(3, 7, 30), "", alarm=True)
        self.check("lunedì alle 9 dentista", at(9, 9), "Dentista")
        self.check("venerdì alle 18:45 cena", at(6, 18, 45), "Cena")
        self.check("ogni giorno alle 8 medicine", at(3, 8), "Medicine", daily=True)
        self.check("ricordami di comprare il pane alle 9", at(3, 9), "Comprare il pane")
        self.check("fra mezz'ora riunione", at(2, 10, 30), "Riunione")
        self.check("tra due ore uscire", at(2, 12), "Uscire")
        self.check("alle 8 di sera film", at(2, 20), "Film")

    def test_english(self):
        self.check("remind me at 6 pm to call Anna", at(2, 18), "Call Anna")
        self.check("in 5 minutes tea", at(2, 10, 5), "Tea")
        self.check("tomorrow at 7 wake me", at(3, 7), "", alarm=True)

    def test_past_time_is_tomorrow(self):
        self.check("alle 9 caffè", at(3, 9), "Caffè")

    def test_no_time(self):
        self.assertIsNone(vr.parse("chiama Marco", NOW))
        self.assertIsNone(vr.parse("alle 25 niente", NOW))


class ListTest(unittest.TestCase):

    def test_describe(self):
        self.assertEqual(vr.Reminder(at(2, 15), "Chiama Marco").describe(NOW), "Today at 15:00: Chiama Marco")
        self.assertEqual(vr.Reminder(at(3, 7), "", alarm=True).describe(NOW), "Tomorrow at 07:00: alarm")
        self.assertEqual(vr.Reminder(at(3, 8), "Medicine", daily=True).describe(NOW),
                         "Every day at 08:00: Medicine")
        self.assertEqual(vr.Reminder(at(20, 9), "Dentista").describe(NOW), "20/11/2026 at 09:00: Dentista")

    def test_due_and_daily(self):
        once = vr.Reminder(at(2, 9), "a")
        later = vr.Reminder(at(2, 11), "b")
        daily = vr.Reminder(at(2, 8), "c", daily=True)
        self.assertEqual(vr.due([once, later, daily], NOW), [once, daily])
        self.assertIsNone(vr.after_firing(once))
        self.assertEqual(vr.after_firing(daily).when, at(3, 8))

    def test_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "r.json")
            vr.save([vr.Reminder(at(3, 8), "Medicine", daily=True), vr.Reminder(at(2, 15), "Marco")], path)
            loaded = vr.load(path)
            self.assertEqual([(r.when, r.text, r.daily) for r in loaded],
                             [(at(2, 15), "Marco", False), (at(3, 8), "Medicine", True)])
            with open(path, "w") as f:
                f.write("broken")
            self.assertEqual(vr.load(path), [])


def load_program():
    loader = importlib.machinery.SourceFileLoader("reminders_program", PROGRAM)
    spec = importlib.util.spec_from_loader("reminders_program", loader)
    program = importlib.util.module_from_spec(spec)
    loader.exec_module(program)
    return program


class DaemonTest(unittest.TestCase):

    def test_tick_fires_and_keeps_daily(self):
        program = load_program()
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["XDG_DATA_HOME"] = tmp
            try:
                vr.save([vr.Reminder(at(2, 9), "Pane"), vr.Reminder(at(2, 8), "Medicine", daily=True),
                         vr.Reminder(at(2, 11), "Dopo")])
                daemon = program.Daemon.__new__(program.Daemon)
                fired = []
                daemon.fire = fired.append
                program.now = lambda: NOW
                daemon.tick()
                left = vr.load()
            finally:
                del os.environ["XDG_DATA_HOME"]
        self.assertEqual(sorted(r.text for r in fired), ["Medicine", "Pane"])
        self.assertEqual([(r.text, r.when) for r in left], [("Dopo", at(2, 11)), ("Medicine", at(3, 8))])

    def test_alarm_rings_until_stopped(self):
        program = load_program()
        daemon = program.Daemon.__new__(program.Daemon)
        played = []
        program.play = played.append
        daemon.ringing = {7: 6}
        daemon.ring()
        self.assertEqual(len(played), 1)
        daemon.ring()
        self.assertEqual(daemon.ringing, {}, "a minute, then it stops")


CHILD = r'''
import importlib.machinery, importlib.util, sys
loader = importlib.machinery.SourceFileLoader("rem", sys.argv[1])
spec = importlib.util.spec_from_loader("rem", loader)
program = importlib.util.module_from_spec(spec)
loader.exec_module(program)
from gi.repository import Adw, Gtk
App, Window = program.window_classes()
said = []

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

app = Adw.Application(application_id="org.vabaxos.RemindersTest")
def check(app):
    window = Window(app, store=sys.argv[2], speak=said.append)
    window.present()
    print("EMPTY:" + window.rows[0].get_title(), flush=True)
    window.entry.set_text("tra 10 minuti scola la pasta")
    window.add()
    window.entry.set_text("quando vuoi")
    window.add()
    print("SAID:" + "|".join(said), flush=True)
    print("ROWS:%d" % len(window.rows), flush=True)
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
                       LANG="C.UTF-8", PYTHONDONTWRITEBYTECODE="1")
            try:
                result = subprocess.run([sys.executable, "-c", CHILD, PROGRAM, os.path.join(tmp, "r.json")],
                                        env=env, capture_output=True, text=True, timeout=60)
            finally:
                broadway.terminate()
                broadway.wait()
        out = dict(line.split(":", 1) for line in result.stdout.splitlines() if ":" in line)
        err = result.stderr[-2000:]
        self.assertEqual(out.get("EMPTY"), "Nothing planned.", err)
        said = out.get("SAID", "").split("|")
        self.assertTrue(said[0].startswith("Added: Today at "), said)
        self.assertTrue(said[0].endswith(": Scola la pasta."), said)
        self.assertTrue(said[1].startswith("When?"), said)
        self.assertEqual(out.get("ROWS"), "1", err)
        self.assertEqual(out.get("UNNAMED"), "", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
