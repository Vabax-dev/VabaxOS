#!/usr/bin/env python3
"""Tests for vabaxos-trouble ("Something is wrong"): the first checks with
made-up commands, personal data hidden, the report, and the window on
Broadway (made-up checks and report).

    python3 tests/trouble/test_trouble.py
"""

import datetime
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ROOT = os.path.join(REPO, "packages", "vabaxos-trouble", "root")
LIB = os.path.join(ROOT, "usr", "lib", "python3", "dist-packages")
PROGRAM = os.path.join(ROOT, "usr", "bin", "vabaxos-trouble")
REPORT = os.path.join(REPO, "packages", "vabaxos-accessibility", "root", "usr", "bin", "vabaxos-report")
sys.path.insert(0, LIB)
os.environ["LANGUAGE"] = "C"

import vabaxos_trouble as vt  # noqa: E402


def fake(answers):
    """A run() answering from a table: first words of the command -> (code, output)."""
    calls = []

    def run(command, timeout=60):
        calls.append(command)
        for words, answer in answers.items():
            if tuple(command[:len(words)]) == words:
                return answer
        return 0, ""
    run.calls = calls
    return run


HEALTHY = {
    ("pactl", "list"): (0, "56\talsa_output.pci-0000_00_1f.3.analog-stereo\tPipeWire\ts32le 2ch 48000Hz\tRUNNING\n"),
    ("pactl", "get-sink-mute"): (0, "Mute: no\n"),
    ("pactl", "get-sink-volume"): (0, "Volume: front-left: 45875 /  70% / -9,29 dB,   front-right: 45875 /  70%\n"),
    ("pgrep",): (0, "1234\n"),
    ("nmcli", "-t", "-f", "STATE"): (0, "connected\n"),
}


class FindingsTest(unittest.TestCase):

    def test_healthy(self):
        self.assertEqual(vt.findings(fake(HEALTHY), space=lambda p: (50e9, 100e9)), [])

    def test_problems(self):
        answers = dict(HEALTHY)
        answers[("systemctl", "--failed")] = (0, "cups.service loaded failed failed CUPS\n"
                                                 "bluetooth.service loaded failed failed Bluetooth\n")
        answers[("systemctl", "--user")] = (0, "vabaxos-announce.service loaded failed failed x\n")
        answers[("pactl", "get-sink-mute")] = (0, "Mute: yes\n")
        answers[("pgrep",)] = (1, "")
        answers[("nmcli", "-t", "-f", "STATE")] = (0, "disconnected\n")
        answers[("dpkg", "--audit")] = (0, "The following packages are only half configured\n")
        found = dict(vt.findings(fake(answers), space=lambda p: (300e6, 100e9)))
        self.assertEqual(found["system-services"],
                         "Some system services did not start: cups.service, bluetooth.service.")
        self.assertEqual(found["user-services"], "A service of your session did not start: vabaxos-announce.service.")
        self.assertEqual(found["muted"], "The sound is muted.")
        self.assertIn("Super+Alt+S", found["orca"])
        self.assertIn("not connected", found["network"])
        self.assertEqual(found["space"], "Little free space for the system: 300 MB.")
        self.assertIn("packages", found)

    def test_sound(self):
        answers = dict(HEALTHY)
        answers[("pactl", "list")] = (0, "")
        self.assertEqual(vt.findings(fake(answers), space=lambda p: None)[0][0], "no-output")
        answers = dict(HEALTHY)
        answers[("pactl", "get-sink-volume")] = (0, "Volume: front-left: 3000 /   5% / -70 dB\n")
        self.assertEqual(vt.findings(fake(answers), space=lambda p: None),
                         [("quiet", "The volume is very low: 5%.")])
        answers = dict(HEALTHY)
        answers[("pactl", "list")] = (1, "Connection failure: Connection refused\n")
        self.assertEqual(vt.findings(fake(answers), space=lambda p: None)[0][0], "no-sound-server")
        answers[("pactl", "list")] = (127, "")
        self.assertEqual(vt.findings(fake(answers), space=lambda p: None), [], "no pactl: nothing to say")


class HideTest(unittest.TestCase):

    def test_hide(self):
        text = ("Nov 01 casa-rossi NetworkManager: Wi-Fi Rossi Home 5G, 192.168.1.20 fe80::1c2b:3cff:fe4d:5e6f "
                "dev aa:bb:cc:dd:ee:ff user mario.rossi@example.org at 12:34:56 on 127.0.0.1 ::1 "
                "std::string 2001:db8::7 user@1000.service")
        hidden = vt.hide(text, {"casa-rossi", "Rossi Home 5G"})
        self.assertNotIn("Rossi", hidden)
        self.assertNotIn("192.168", hidden)
        self.assertNotIn("fe80", hidden)
        self.assertNotIn("2001:db8", hidden)
        self.assertNotIn("aa:bb", hidden)
        self.assertNotIn("example.org", hidden)
        for kept in ("12:34:56", "127.0.0.1", "::1", "std::string", "user@1000.service", "NetworkManager"):
            self.assertIn(kept, hidden)

    def test_personal(self):
        words = vt.personal(fake({("nmcli",): (0, "Rossi Home 5G\nlo\nWired connection 1\n")}))
        self.assertIn("Rossi Home 5G", words)
        self.assertIn(socket.gethostname(), words | {socket.gethostname()} if len(socket.gethostname()) < 3
                      or socket.gethostname().lower() in vt.COMMON else words)
        self.assertNotIn("lo", words)
        self.assertFalse(words & vt.COMMON)


class ReportTest(unittest.TestCase):

    def test_collect(self):
        answers = {(vt.REPORT, "-"): (0, "VabaxOS report\n===== Network =====\nwlan0 192.168.1.20\n"),
                   ("journalctl",): (0, "Nov 01 gnome-shell: warning\n"), ("nmcli",): (0, "")}
        run = fake(answers)
        text = vt.collect("Orca tace", "Sound", run=run, found=[("muted", "The sound is muted.")],
                          now=datetime.datetime(2026, 11, 1, 10, 0))
        self.assertIn("Area: Sound", text)
        self.assertIn("Orca tace", text)
        self.assertIn("- The sound is muted.", text)
        self.assertIn("===== Network =====", text)
        self.assertIn("[address]", text)
        self.assertIn("gnome-shell: warning", text)
        self.assertNotIn(["pkexec", vt.REPORT, "-"], run.calls)

    def test_system_log(self):
        answers = {("pkexec",): (126, ""), (vt.REPORT, "-"): (0, "user part\n")}
        run = fake(answers)
        text = vt.collect("", "Sound", system_log=True, hide_personal=False, run=run, found=[])
        self.assertEqual(run.calls[0], ["pkexec", vt.REPORT, "-"])
        self.assertIn("password was not given", text)
        self.assertIn("user part", text)
        self.assertIn("- No problem found.", text)

    def test_save(self):
        with tempfile.TemporaryDirectory() as folder:
            path = vt.save("text\n", folder, now=datetime.datetime(2026, 11, 1, 10, 0, 5))
            self.assertEqual(os.path.basename(path), "vabaxos-report-20261101-100005.txt")
            with open(path, encoding="utf-8") as f:
                self.assertEqual(f.read(), "text\n")

    def test_report_on_stdout(self):
        """vabaxos-report - writes on the standard output, no file."""
        with tempfile.TemporaryDirectory() as home:
            done = subprocess.run(["bash", REPORT, "-"], capture_output=True, text=True, timeout=120,
                                  env=dict(os.environ, HOME=home, DBUS_SESSION_BUS_ADDRESS=""), check=False)
            self.assertEqual(done.returncode, 0)
            self.assertTrue(done.stdout.startswith("VabaxOS report"))
            self.assertFalse([n for n in os.listdir(home) if n.startswith("vabaxos-report")])


CHILD = r'''
import importlib.machinery, importlib.util, sys
loader = importlib.machinery.SourceFileLoader("troubleprog", sys.argv[1])
spec = importlib.util.spec_from_loader("troubleprog", loader)
program = importlib.util.module_from_spec(spec)
loader.exec_module(program)
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk
said, asked = [], []
def collector(description, area, system_log, hide_personal, found):
    asked.append((description, area, system_log, hide_personal, len(found)))
    return "REPORT " + description
App, Window = program.window_classes(
    speak=said.append, checker=lambda: [("muted", "The sound is muted."), ("orca", "Orca is off.")],
    collector=collector, saver=lambda text: "/tmp/vabaxos-report-test.txt")
app = Adw.Application(application_id="org.vabaxos.TroubleTest")
def inner(w):
    while w is not None:
        if type(w).__name__ in ("AdwToastWidget", "WindowControls", "AdwBackButton"):
            return True
        w = w.get_parent()
    return False
def unnamed(widget, out):
    child = widget.get_first_child()
    while child:
        if isinstance(child, Gtk.Button) and child.get_mapped() and not child.get_label() \
                and not child.get_tooltip_text() and not inner(child):
            out.append(type(child).__name__)
        unnamed(child, out)
        child = child.get_next_sibling()
    return out
def check(app):
    window = Window(app)
    window.present()
    def later():
        print("CHECKS:" + said[0], flush=True)
        window.description.get_buffer().set_text("Orca tace dopo la sospensione")
        window.area.set_selected(1)
        window.system.set_active(True)
        window.make()
        GLib.timeout_add(500, finish)
        return False
    def finish():
        print("ASKED:" + repr(asked[0]), flush=True)
        print("SAID:" + said[-1], flush=True)
        print("VISIBLE:" + str(window.done.get_visible()), flush=True)
        print("UNNAMED:" + ",".join(unnamed(window, [])), flush=True)
        app.quit()
        return False
    GLib.timeout_add(800, later)
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
        err = result.stderr[-2000:]
        self.assertEqual(out.get("CHECKS"), "2 problems found: The sound is muted. Orca is off.", err)
        self.assertEqual(out.get("ASKED"), "('Orca tace dopo la sospensione', 'Sound', True, True, 2)", err)
        self.assertEqual(out.get("SAID"), "Report saved in /tmp/vabaxos-report-test.txt. Attach it to a message "
                                          "or to a bug report.", err)
        self.assertEqual(out.get("VISIBLE"), "True", err)
        self.assertEqual(out.get("UNNAMED"), "", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
