#!/usr/bin/env python3
"""Tests for vabaxos-lessons: every exercise is well made, key presses are
checked, and a lesson goes on in the window (key presses simulated, made-up
voice) on Broadway.

    python3 tests/lessons/test_lessons.py
"""

import os
import shutil
import socket
import subprocess
import sys
import time
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ROOT = os.path.join(REPO, "packages", "vabaxos-lessons", "root")
LIB = os.path.join(ROOT, "usr", "lib", "python3", "dist-packages")
PROGRAM = os.path.join(ROOT, "usr", "bin", "vabaxos-lessons")
sys.path.insert(0, LIB)

import vabaxos_lessons as lessons  # noqa: E402


class DataTest(unittest.TestCase):

    def test_exercises(self):
        self.assertGreaterEqual(len(lessons.LESSONS), 5)
        for title, exercises in lessons.LESSONS:
            self.assertTrue(exercises, title)
            for exercise in exercises:
                self.assertIn(exercise.kind, ("press", "try"))
                self.assertEqual(bool(exercise.key), exercise.kind == "press", exercise.name)
                self.assertTrue(exercise.instruction())

    def test_press_keys_are_valid_accelerators(self):
        try:
            import gi
            gi.require_version("Gtk", "4.0")
            from gi.repository import Gtk
        except (ImportError, ValueError):
            self.skipTest("GTK 4 is missing")
        for _title, exercises in lessons.LESSONS:
            for exercise in exercises:
                if exercise.kind == "press":
                    ok, keyval, _mods = Gtk.accelerator_parse(exercise.key)
                    self.assertTrue(ok and keyval, exercise.key)

    def test_matching(self):
        tab = lessons.Exercise("<Shift>Tab", "Shift+Tab", "")
        self.assertTrue(lessons.matches(tab, "ISO_Left_Tab", {"Shift"}))
        self.assertFalse(lessons.matches(tab, "Tab", set()))
        copy = lessons.Exercise("<Control>c", "Ctrl+C", "")
        self.assertTrue(lessons.matches(copy, "c", {"Control"}))
        self.assertTrue(lessons.matches(copy, "C", {"Control"}))
        self.assertFalse(lessons.matches(copy, "c", {"Control", "Shift"}))
        self.assertFalse(lessons.matches(lessons.Exercise("", "Super", "", "try"), "Super_L", set()))

    def test_said(self):
        self.assertEqual(lessons.said("c", {"Control"}), "Ctrl+C")
        self.assertEqual(lessons.said("Return", set()), "Enter")
        self.assertEqual(lessons.said("ISO_Left_Tab", {"Shift"}), "Shift+Tab")


CHILD = r'''
import importlib.machinery, importlib.util, sys
loader = importlib.machinery.SourceFileLoader("lessons_program", sys.argv[1])
spec = importlib.util.spec_from_loader("lessons_program", loader)
program = importlib.util.module_from_spec(spec)
loader.exec_module(program)
from gi.repository import Adw, GLib, Gtk
said = []
def speak(text):
    said.append(text)
    return True

def walk(widget):
    yield widget
    child = widget.get_first_child()
    while child is not None:
        yield from walk(child)
        child = child.get_next_sibling()

app = Adw.Application(application_id="org.vabaxos.LessonsTest")
def check(app):
    window = program.LessonsWindow(app, speak=speak)
    window.present()
    window.start(0)
    print("FIRST:" + window.instruction.get_text(), flush=True)
    window.answer("Return", set())          # wrong: the first exercise is Tab
    window.answer("Return", set())          # wrong again: the key is said
    print("WRONG:" + said[-1], flush=True)
    window.answer("Tab", set())
    print("AFTER:%d" % window.index, flush=True)
    window.answer("Escape", set())          # not the Escape exercise: back to the list
    print("PAGE:" + window.stack.get_visible_child_name(), flush=True)
    window.start(3)                         # windows and desktop: tried keys
    window.answer("Super_L", {"Super"})
    window.answer("Return", set())
    print("TRY:%d" % window.index, flush=True)
    unnamed = [type(w).__name__ for w in walk(window) if isinstance(w, Gtk.Button) and w.get_mapped()
               and not w.get_label() and not w.get_tooltip_text() and not w.get_ancestor(Gtk.WindowControls)]
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

    def test_a_lesson(self):
        display = free_display()
        broadway = subprocess.Popen(["gtk4-broadwayd", f":{display}"], stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
        time.sleep(1)
        env = dict(os.environ, GDK_BACKEND="broadway", BROADWAY_DISPLAY=f":{display}", GSETTINGS_BACKEND="memory",
                   NO_AT_BRIDGE="1", PYTHONPATH=LIB, LANGUAGE="C", LANG="C.UTF-8", PYTHONDONTWRITEBYTECODE="1")
        try:
            result = subprocess.run([sys.executable, "-c", CHILD, PROGRAM], env=env, capture_output=True,
                                    text=True, timeout=60)
        finally:
            broadway.terminate()
            broadway.wait()
        out = dict(line.split(":", 1) for line in result.stdout.splitlines() if ":" in line)
        err = result.stderr[-2000:]
        self.assertEqual(out.get("FIRST"), "Press Tab: goes to the next control.", err)
        self.assertEqual(out.get("WRONG"), "That was Enter. The key is Tab.", err)
        self.assertEqual(out.get("AFTER"), "1", err)
        self.assertEqual(out.get("PAGE"), "list", err)
        self.assertEqual(out.get("TRY"), "1", err)
        self.assertEqual(out.get("UNNAMED"), "", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
