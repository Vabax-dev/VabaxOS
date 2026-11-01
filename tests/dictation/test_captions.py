#!/usr/bin/env python3
"""Tests for the live captions of vabaxos-dictation: the audio cut into
phrases, and the capture command.

    python3 tests/dictation/test_captions.py
"""

import math
import os
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LIB = os.path.join(REPO, "packages", "vabaxos-dictation", "root", "usr", "lib", "python3", "dist-packages")
PROGRAM = os.path.join(REPO, "packages", "vabaxos-dictation", "root", "usr", "bin", "vabaxos-captions")
sys.path.insert(0, LIB)

from vabaxos_dictation import captions  # noqa: E402

RATE = 16000


def raw(seconds, volume):
    count = int(RATE * seconds)
    return struct.pack(f"<{count}h", *(int(32767 * volume * math.sin(2 * math.pi * 200 * i / RATE))
                                       for i in range(count)))


class SegmenterTest(unittest.TestCase):

    def test_a_pause_ends_a_phrase(self):
        segmenter = captions.Segmenter()
        audio = raw(0.5, 0) + raw(1.5, 0.2) + raw(1.0, 0)
        phrases = []
        for start in range(0, len(audio), 3333):  # pieces of odd size, as from a pipe
            phrases += segmenter.feed(audio[start:start + 3333])
        self.assertEqual(len(phrases), 1)
        seconds = len(phrases[0]) / 2 / RATE
        self.assertGreater(seconds, 1.5)
        self.assertLess(seconds, 2.3)

    def test_silence_and_clicks_give_nothing(self):
        segmenter = captions.Segmenter()
        self.assertEqual(segmenter.feed(raw(3, 0)), [])
        self.assertEqual(segmenter.feed(raw(0.1, 0.3) + raw(1, 0)), [])
        self.assertEqual(segmenter.flush(), [])

    def test_long_speech_is_cut(self):
        segmenter = captions.Segmenter()
        phrases = segmenter.feed(raw(20, 0.2))
        self.assertEqual(len(phrases), 2)
        self.assertAlmostEqual(len(phrases[0]) / 2 / RATE, captions.MAX_PHRASE, delta=0.05)
        self.assertEqual(len(segmenter.flush()), 1, "the last four seconds")

    def test_two_phrases(self):
        segmenter = captions.Segmenter()
        phrases = segmenter.feed(raw(1, 0.2) + raw(1, 0) + raw(1, 0.2) + raw(1, 0))
        self.assertEqual(len(phrases), 2)

    def test_capture(self):
        self.assertIn("--device=@DEFAULT_MONITOR@", captions.capture_command("computer"))
        self.assertIn("--device=@DEFAULT_SOURCE@", captions.capture_command("microphone"))
        self.assertIn("--rate=16000", captions.capture_command("computer"))



CHILD = r'''
import importlib.machinery, importlib.util, os, sys
loader = importlib.machinery.SourceFileLoader("captions_program", sys.argv[1])
spec = importlib.util.spec_from_loader("captions_program", loader)
program = importlib.util.module_from_spec(spec)
loader.exec_module(program)
program.core.available = lambda: True
from gi.repository import Adw, GLib, Gtk

class FakeListener:
    def __init__(self, on_text, on_error):
        self.on_text, self.started, self.stopped = on_text, [], 0
    def start(self, source):
        self.started.append(source)
        GLib.idle_add(self.on_text, "Buongiorno a tutti.")
        GLib.idle_add(self.on_text, "Oggi parliamo di VabaxOS.")
    def stop(self):
        self.stopped += 1

def walk(widget):
    yield widget
    child = widget.get_first_child()
    while child is not None:
        yield from walk(child)
        child = child.get_next_sibling()

app = Adw.Application(application_id="org.vabaxos.CaptionsTest")
def check(app):
    window = program.CaptionsWindow(app, listener_class=FakeListener)
    window.present()
    def later():
        print("TEXT:" + window.text().replace(chr(10), "|"), flush=True)
        window.next_source()
        window.toggle_pause()
        print("SOURCES:" + ",".join(window.listener.started), flush=True)
        print("STOPPED:%d" % window.listener.stopped, flush=True)
        print("PAUSE:" + window.pause_button.get_label(), flush=True)
        path = window.save()
        print("SAVED:%s" % open(path, encoding="utf-8").read().count("VabaxOS"), flush=True)
        # The close button of a toast is named by libadwaita itself.
        def inner(w):
            while w is not None:
                if type(w).__name__ in ("AdwToastWidget", "WindowControls"):
                    return True
                w = w.get_parent()
            return False
        unnamed = [type(w).__name__ for w in walk(window) if isinstance(w, Gtk.Button) and w.get_mapped()
                   and not w.get_label() and not w.get_tooltip_text() and not inner(w)]
        print("UNNAMED:" + ",".join(unnamed), flush=True)
        app.quit()
        return False
    GLib.timeout_add(400, later)
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
                       GSETTINGS_BACKEND="memory", NO_AT_BRIDGE="1", PYTHONPATH=LIB,
                       # A home of its own, for the saved text; the Broadway socket
                       # stays where gtk4-broadwayd put it.
                       HOME=tmp, XDG_CACHE_HOME=os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache")),
                       XDG_CONFIG_HOME=os.path.join(tmp, "config"), LANGUAGE="C", LANG="C.UTF-8", PYTHONDONTWRITEBYTECODE="1")
            try:
                result = subprocess.run([sys.executable, "-c", CHILD, PROGRAM], env=env,
                                        capture_output=True, text=True, timeout=60)
            finally:
                broadway.terminate()
                broadway.wait()
            out = dict(line.split(":", 1) for line in result.stdout.splitlines() if ":" in line)
            err = result.stderr[-2000:]
            self.assertEqual(out.get("TEXT"), "Buongiorno a tutti.|Oggi parliamo di VabaxOS.", err)
            self.assertEqual(out.get("SOURCES"), "computer,microphone", err)
            self.assertEqual(out.get("STOPPED"), "1", err)
            self.assertEqual(out.get("PAUSE"), "Resume", err)
            self.assertEqual(out.get("SAVED"), "1", err)
            self.assertEqual(out.get("UNNAMED"), "", err)
            self.assertEqual(len([n for n in os.listdir(tmp) if n.endswith(".txt")]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
