#!/usr/bin/env python3
"""Tests for vabaxos-checkup: each check with a made-up computer (files in
a temporary folder, made-up answers of pactl, nmcli and bluetoothctl), the
summary, and the window on Broadway.

    python3 tests/checkup/test_checkup.py
"""

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ROOT = os.path.join(REPO, "packages", "vabaxos-checkup", "root")
LIB = os.path.join(ROOT, "usr", "lib", "python3", "dist-packages")
PROGRAM = os.path.join(ROOT, "usr", "bin", "vabaxos-checkup")
sys.path.insert(0, LIB)

import vabaxos_checkup as vc  # noqa: E402

SINKS = [{"name": "alsa_output.pci-0000_00_1f.3.analog-stereo", "description": "Built-in Audio Analog Stereo",
          "mute": False, "volume": {"front-left": {"value_percent": "65%"}, "front-right": {"value_percent": "65%"}}}]
SOURCES = [{"name": "alsa_output.pci-0000_00_1f.3.analog-stereo.monitor", "description": "Monitor"},
           {"name": "alsa_input.pci-0000_00_1f.3.analog-stereo", "description": "Built-in Audio Microphone"}]


class FakeProbe(vc.Probe):

    def __init__(self, root, answers, display=None, disk=(80e9, 250e9)):
        super().__init__(root)
        self.answers = answers
        self.display = display
        self.free = disk

    def run(self, *command, timeout=10):
        for words, answer in self.answers.items():
            if command[:len(words)] == words:
                return answer
        return None

    def braille_display(self):
        return self.display

    def disk(self, path="/"):
        return self.free


def computer(files):
    root = tempfile.mkdtemp()
    for path, text in files.items():
        full = os.path.join(root, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(text)
    return root


LAPTOP = {
    "proc/meminfo": "MemTotal:       16303216 kB\n",
    "sys/class/power_supply/BAT0/capacity": "80\n",
    "sys/class/power_supply/BAT0/status": "Discharging\n",
    "sys/class/power_supply/BAT0/energy_full": "45000000\n",
    "sys/class/power_supply/BAT0/energy_full_design": "50000000\n",
    "sys/class/video4linux/video0/name": "Integrated Camera\n",
    "sys/class/video4linux/video0/index": "0\n",
    "sys/class/video4linux/video1/name": "Integrated Camera\n",
    "sys/class/video4linux/video1/index": "1\n",
    "sys/class/bluetooth/hci0/name": "hci0\n",
}
GOOD = {
    ("pactl", "-f", "json", "list", "sinks"): json.dumps(SINKS),
    ("pactl", "get-default-sink"): SINKS[0]["name"] + "\n",
    ("pactl", "-f", "json", "list", "sources"): json.dumps(SOURCES),
    ("nmcli",): "wifi:connected:Casa Rossi\nethernet:unavailable:\nloopback:connected (externally):lo\n",
    ("bluetoothctl", "show"): "Controller 11:22:33:44:55:66\n\tPowered: yes\n",
}


class ChecksTest(unittest.TestCase):

    def setUp(self):
        self.root = computer(LAPTOP)
        self.addCleanup(shutil.rmtree, self.root)

    def items(self, answers=GOOD, **kwargs):
        return {i.key: i for i in vc.run_checks(FakeProbe(self.root, answers, **kwargs))}

    def test_good_laptop(self):
        items = self.items(display=("fs", 40))
        self.assertEqual(items["audio"].text(), "Sound: Built-in Audio Analog Stereo, it works.")
        self.assertEqual(items["network"].text(), "Network: Wi-Fi connected to Casa Rossi.")
        self.assertEqual(items["battery"].text(), "Battery: 80 percent, on battery. It holds 90 percent of the "
                                                  "charge it held when new.")
        self.assertEqual(items["braille"].text(), "Braille: display connected, 40 cells (fs).")
        self.assertEqual(items["microphone"].sentence, "Built-in Audio Microphone")
        self.assertEqual(items["camera"].sentence, "Integrated Camera.")
        self.assertEqual(items["memory"].sentence, "16 GB.")
        self.assertEqual(items["disk"].sentence, "80 GB free.")
        self.assertEqual(vc.problems(list(items.values())), [])
        self.assertTrue(vc.summary(list(items.values())).startswith("Check of the computer: everything is fine. "
                                                                     "Sound: Built-in Audio"))

    def test_problems(self):
        answers = dict(GOOD)
        answers[("pactl", "-f", "json", "list", "sinks")] = json.dumps(
            [dict(SINKS[0], mute=True)])
        answers[("nmcli",)] = "ethernet:disconnected:\n"
        with open(os.path.join(self.root, "sys/class/power_supply/BAT0/energy_full"), "w") as f:
            f.write("20000000\n")
        items = self.items(answers, disk=(2e9, 250e9))
        self.assertEqual(items["audio"].state, vc.WARN)
        self.assertEqual(items["audio"].sentence, "Built-in Audio Analog Stereo, but muted.")
        self.assertEqual(items["network"].sentence, "only a cable socket, no Wi-Fi card: connect the cable.")
        self.assertIn("worn: it holds 40 percent", items["battery"].sentence)
        self.assertEqual(items["disk"].sentence, "only 2 GB free.")
        summary = vc.summary(list(items.values()))
        self.assertTrue(summary.startswith("Check of the computer: 4 things to look at. Sound:"), summary)

    def test_nothing_there(self):
        root = computer({"proc/meminfo": "MemTotal: 3000000 kB\n"})
        self.addCleanup(shutil.rmtree, root)
        items = {i.key: i for i in vc.run_checks(FakeProbe(root, {("pactl", "-f", "json", "list", "sinks"): "[]"}))}
        self.assertEqual(items["audio"].state, vc.PROBLEM)
        self.assertEqual(items["battery"].sentence, "none: a desktop computer, on mains power.")
        self.assertEqual(items["bluetooth"].sentence, "none.")
        self.assertEqual(items["camera"].state, vc.NOTE)
        self.assertEqual(items["memory"].state, vc.WARN)
        self.assertEqual(items["network"].sentence, "NetworkManager does not answer.")

    def test_a_broken_check_does_not_stop_the_others(self):
        class Broken(FakeProbe):
            def braille_display(self):
                raise RuntimeError("boom")
        items = vc.run_checks(Broken(self.root, GOOD))
        self.assertEqual(len(items), len(vc.CHECKS))
        self.assertEqual([i.sentence for i in items if i.key == "braille"], ["boom"])


CHILD = r'''
import importlib.machinery, importlib.util, sys
loader = importlib.machinery.SourceFileLoader("checkprog", sys.argv[1])
spec = importlib.util.spec_from_loader("checkprog", loader)
program = importlib.util.module_from_spec(spec)
loader.exec_module(program)
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk
import vabaxos_checkup as vc

said, closed = [], []
items = [vc.Item("audio", "Sound", vc.WARN, "Speakers, but muted."),
         vc.Item("network", "Network", vc.OK, "Wi-Fi connected to Casa."),
         vc.Item("braille", "Braille", vc.NOTE, "no display connected.")]
App, Window = program.window_classes(speak=said.append, checker=lambda: items, after_close=lambda: closed.append(1))
app = Adw.Application(application_id="org.vabaxos.CheckupTest")

def check(app):
    window = Window(app)
    window.present()
    def step():
        print("SAID:" + "|".join(said), flush=True)
        print("ROWS:" + "|".join(g.get_title() + ": " + r.get_title() + " - " + r.get_subtitle()
                                 for g, r in window.rows), flush=True)
        print("FOCUS:" + str(window.rows[0][1].has_focus()), flush=True)
        window.copy()
        print("COPIED:" + said[-1], flush=True)
        window.close()
        print("CLOSED:" + str(closed), flush=True)
        app.quit()
        return False
    GLib.timeout_add(600, step)

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


@unittest.skipUnless(shutil.which("gtk4-broadwayd"), "gtk4-broadwayd (libgtk-4-bin) is not installed")
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
        self.assertEqual(out.get("SAID"), "Checking the computer.|Check of the computer: one thing to look at. "
                                          "Sound: Speakers, but muted.", err)
        self.assertEqual(out.get("ROWS"), "To look at: Sound - Speakers, but muted.|What the computer has: Network - "
                                          "Wi-Fi connected to Casa.|What the computer has: Braille - no display "
                                          "connected.", err)
        self.assertEqual(out.get("FOCUS"), "True", err)
        self.assertEqual(out.get("COPIED"), "Result copied: paste it with Ctrl+V.", err)
        self.assertEqual(out.get("CLOSED"), "[1]", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
