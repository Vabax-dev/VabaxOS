#!/usr/bin/env python3
"""Tests for vabaxos-doctor (block 16): every check on a made-up computer
(fake_system.py), the fixes it chooses, and the window on a hidden
Broadway display, where every button must have a name.

    python3 tests/doctor/test_doctor.py
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

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
ROOT = os.path.join(REPO, "packages", "vabaxos-doctor", "root")
LIB = os.path.join(ROOT, "usr", "lib", "python3", "dist-packages")
PROGRAM = os.path.join(ROOT, "usr", "bin", "vabaxos-doctor")
sys.path[:0] = [LIB, HERE]
os.environ.setdefault("LANGUAGE", "C")

from fake_system import FakeSystem  # noqa: E402
from vabaxos_doctor import checks  # noqa: E402


def by_id(system):
    return {r.ident: r for r in checks.run_checks(system)}


class Checks(unittest.TestCase):

    def test_healthy_computer(self):
        results = checks.run_checks(FakeSystem())
        self.assertEqual([r.state for r in results if r.state != checks.OK], [],
                         "\n".join(r.line() for r in results))
        self.assertEqual(checks.summary(results), "Everything works.")
        # Sound and speech first: what a blind user needs first.
        self.assertEqual([r.ident for r in results][:4], ["sound-card", "sound", "speech", "screen-reader"])

    def test_sound(self):
        silent = by_id(FakeSystem({"wpctl get-volume @DEFAULT_AUDIO_SINK@": None}))["sound"]
        self.assertEqual((silent.state, silent.fix), (checks.PROBLEM, "sound"))
        muted = by_id(FakeSystem({"wpctl get-volume @DEFAULT_AUDIO_SINK@": "Volume: 0.70 [MUTED]\n"}))["sound"]
        self.assertEqual((muted.state, muted.fix), (checks.PROBLEM, "sound"))
        low = by_id(FakeSystem({"wpctl get-volume @DEFAULT_AUDIO_SINK@": "Volume: 0.20\n"}))["sound"]
        self.assertEqual((low.state, low.message), (checks.WARNING, "The volume is low, 20 percent."))
        none = by_id(FakeSystem(files={"/proc/asound/cards": "--- no soundcards ---\n"}))["sound-card"]
        self.assertEqual(none.state, checks.PROBLEM)

    def test_speech(self):
        result = by_id(FakeSystem({"spd-say -O": None}))["speech"]
        self.assertEqual((result.state, result.fix), (checks.PROBLEM, "speech"))
        kokoro = by_id(FakeSystem(files={"/etc/speech-dispatcher/clients/zz-vabaxos-voice.conf":
                                         "# boot\nDefaultModule kokoro\n"}))["speech"]
        self.assertIn("Kokoro", kokoro.message)

    def test_screen_reader(self):
        off = by_id(FakeSystem({"gsettings get org.gnome.desktop.a11y.applications screen-reader-enabled":
                                "false\n"}))["screen-reader"]
        self.assertEqual((off.state, off.fix), (checks.WARNING, "orca"))
        stopped = by_id(FakeSystem({"pgrep -u {uid} -x orca": None}))["screen-reader"]
        self.assertEqual((stopped.state, stopped.fix), (checks.PROBLEM, "orca"))
        mute = json.dumps({"general": {}, "profiles": {"default": {"enableSpeech": False}}})
        silent = by_id(FakeSystem(files={"/home/user/.local/share/orca/user-settings.conf": mute}))
        self.assertEqual((silent["screen-reader"].state, silent["screen-reader"].fix),
                         (checks.PROBLEM, "orca-speech"))

    def test_system_services(self):
        results = by_id(FakeSystem({"systemctl is-active espeakup.service": None,
                                    "systemctl is-active triggerhappy.service vabaxos-voice-rescue.path": None,
                                    "systemctl is-active ufw.service": None,
                                    "systemctl --failed --no-legend --plain":
                                        "cups.service loaded failed failed CUPS\n"}))
        self.assertEqual(results["console-speech"].fix, "console-speech")
        self.assertEqual(results["emergency-key"].fix, "emergency-key")
        self.assertEqual(results["firewall"].fix, "firewall")
        self.assertIn("cups", results["services"].message)
        self.assertEqual(results["services"].fix, "")

    def test_network_disk_memory_updates(self):
        results = by_id(FakeSystem({"nmcli -t -f CONNECTIVITY general": "portal\n"},
                                   files={"/run/reboot-required": "",
                                          "/proc/meminfo": "MemAvailable: 200000 kB\n"},
                                   disks={"/": (500, 100000)}))
        self.assertEqual(results["network"].state, checks.WARNING)
        self.assertEqual(results["updates"].state, checks.WARNING)
        self.assertEqual(results["memory"].state, checks.WARNING)
        self.assertEqual((results["disk"].state, results["disk"].fix), (checks.PROBLEM, "trash"))
        home = by_id(FakeSystem(disks={"/": (50000, 100000), "/home/user": (3000, 100000)}))["disk"]
        self.assertEqual((home.title, home.state), ("Home folder", checks.WARNING))

    def test_summary(self):
        results = checks.run_checks(FakeSystem({"spd-say -O": None, "systemctl is-active ufw.service": None}))
        self.assertEqual(checks.summary(results), "1 problem, 1 warning.")

    def test_fixes(self):
        system = FakeSystem({"wpctl get-volume @DEFAULT_AUDIO_SINK@": "Volume: 0.10\n"})
        self.assertTrue(checks.fix("sound", system))
        self.assertIn("wpctl set-volume @DEFAULT_AUDIO_SINK@ 0.5", system.ran)
        system = FakeSystem()
        checks.fix("orca-speech", system)
        self.assertEqual(system.ran[0], "/usr/libexec/vabaxos/voice-rescue --orca-settings")
        system = FakeSystem()
        checks.fix("firewall", system)
        self.assertEqual(system.ran, ["pkexec ufw --force enable"])
        # Never pkill -f: it would find the doctor itself.
        system = FakeSystem()
        checks.fix("speech", system)
        self.assertFalse([c for c in system.ran if "-f" in c.split()])
        self.assertFalse(checks.fix("unknown", FakeSystem()))


CHILD = r'''
import importlib.machinery, importlib.util, sys
sys.path[:0] = sys.argv[2:4]
from fake_system import FakeSystem
loader = importlib.machinery.SourceFileLoader("doctor", sys.argv[1])
spec = importlib.util.spec_from_loader("doctor", loader)
doctor = importlib.util.module_from_spec(spec)
loader.exec_module(doctor)
from gi.repository import GLib, Gtk
Application, Window = doctor.window()

def walk(widget):
    yield widget
    child = widget.get_first_child()
    while child is not None:
        yield from walk(child)
        child = child.get_next_sibling()

def check(application):
    window = Window(application, FakeSystem({"spd-say -O": None}))
    window.present()
    context = GLib.MainContext.default()
    end = GLib.get_monotonic_time() + 20 * 10**6
    while not window.rows and GLib.get_monotonic_time() < end:
        context.iteration(True)
    print("ROWS:" + "|".join(r.get_title() for r in window.rows), flush=True)
    print("SPEECH:" + window.rows[2].get_subtitle(), flush=True)
    unnamed = [type(w).__name__ for w in walk(window) if isinstance(w, Gtk.Button) and w.get_mapped()
               and not w.get_label() and not w.get_tooltip_text()
               and not any(w.get_ancestor(k) for k in (Gtk.WindowControls,))]
    print("UNNAMED:" + ",".join(unnamed), flush=True)
    fixes = [w for w in walk(window) if isinstance(w, Gtk.Button) and w.get_label() == "Fix"]
    print("FIXES:%d" % len(fixes), flush=True)
    print("FIXALL:%s" % window.fix_all.get_sensitive(), flush=True)
    application.quit()

app = Application()
app.connect("activate", check)
app.run([])
'''


def free_display():
    for number in range(140, 180):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", 8080 + number)) != 0:
                return number
    raise RuntimeError("no free Broadway display")


@unittest.skipUnless(shutil.which("gtk4-broadwayd"), "gtk4-broadwayd (libgtk-4-bin) is not installed")
class Window(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        display = free_display()
        cls.broadway = subprocess.Popen(["gtk4-broadwayd", f":{display}"], stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL)
        time.sleep(1)
        cls.tmp = tempfile.TemporaryDirectory()
        env = dict(os.environ, GDK_BACKEND="broadway", BROADWAY_DISPLAY=f":{display}",
                   GSETTINGS_BACKEND="memory", NO_AT_BRIDGE="1", LANGUAGE="C", LANG="C.UTF-8",
                   XDG_DATA_HOME=os.path.join(cls.tmp.name, "data"), PYTHONDONTWRITEBYTECODE="1")
        result = subprocess.run([sys.executable, "-c", CHILD, PROGRAM, LIB, HERE], env=env,
                                capture_output=True, text=True, timeout=60)
        cls.out = dict(line.split(":", 1) for line in result.stdout.splitlines() if ":" in line)
        cls.err = result.stderr[-2000:]

    @classmethod
    def tearDownClass(cls):
        cls.broadway.terminate()
        cls.broadway.wait()
        cls.tmp.cleanup()

    def test_rows(self):
        self.assertTrue(self.out.get("ROWS", "").startswith("Sound card|Sound|Speech|Screen reader"), self.err)
        self.assertEqual(self.out.get("SPEECH"), "Problem: The speech service does not answer.", self.err)

    def test_every_button_has_a_name(self):
        self.assertEqual(self.out.get("UNNAMED"), "", self.err)

    def test_fix_buttons(self):
        self.assertEqual(self.out.get("FIXES"), "1", self.err)
        self.assertEqual(self.out.get("FIXALL"), "True", self.err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
