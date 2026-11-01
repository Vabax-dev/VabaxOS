#!/usr/bin/env python3
"""Tests for vabaxos-restore (ADR-0027): Timeshift's list, which copies are
kept, the configuration, the copy before installing (with a made-up
Timeshift), the menu of the console, and the window on Broadway. Nothing
is copied or restored.

    python3 tests/restore/test_restore.py
"""

import json
import os
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import time
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ROOT = os.path.join(REPO, "packages", "vabaxos-restore", "root")
LIB = os.path.join(ROOT, "usr", "lib", "python3", "dist-packages")
HELPER = os.path.join(ROOT, "usr", "lib", "vabaxos", "restore", "helper")
PROGRAM = os.path.join(ROOT, "usr", "bin", "vabaxos-restore")
sys.path.insert(0, LIB)

import vabaxos_restore as vr  # noqa: E402
from vabaxos_restore import console  # noqa: E402

LIST = """Mounted '/dev/sda2' at '/run/timeshift/1234/backup'
Device : /dev/sda2
UUID   : 0b2f-test
Path   : /run/timeshift/1234/backup
Mode   : RSYNC
Status : OK
4 snapshots, 196.6 GB free

Num     Name                 Tags  Description
------------------------------------------------------------------------------
0    >  2026-10-20_09-00-01  W
1    >  2026-10-27_09-00-01  W
2    >  2026-10-30_10-00-01  O     Prima di installare 12 pacchetti: gnome-shell, orca, mutter…
3    >  2026-11-01_18-30-12  O     Made by hand
"""


def executable(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR)


class ListTest(unittest.TestCase):

    def test_parse(self):
        copies = vr.parse_list(LIST)
        self.assertEqual([c.name for c in copies], ["2026-10-20_09-00-01", "2026-10-27_09-00-01",
                                                    "2026-10-30_10-00-01", "2026-11-01_18-30-12"])
        self.assertEqual(copies[2].tags, "O")
        self.assertTrue(copies[2].comment.startswith("Prima di installare 12"))
        self.assertEqual(copies[3].when(), ("2026-11-01", "18:30"))
        self.assertEqual(copies[3].title(), "01/11/2026 at 18:30: Made by hand")
        self.assertEqual(copies[0].description(), "weekly copy")

    def test_keep_the_newest(self):
        copies = vr.parse_list(LIST)
        self.assertEqual(vr.to_delete(copies), [])
        more = copies + [vr.Copy(f"2026-11-0{d}_10-00-00", "O", "") for d in (2, 3, 4)] + \
            [vr.Copy("2026-11-05_09-00-01", "W", "")]
        self.assertEqual([c.name for c in vr.to_delete(more)],
                         ["2026-10-20_09-00-01", "2026-10-30_10-00-01", "2026-11-01_18-30-12"])


class ConfigTest(unittest.TestCase):

    def test_config_for_vabaxos(self):
        data = vr.config("1234", {"exclude": ["/var/tmp/**"], "count_daily": "5"})
        self.assertEqual(data["backup_device_uuid"], "1234")
        self.assertEqual(data["btrfs_mode"], "false")
        self.assertIn("/home/**", data["exclude"])
        self.assertIn("/var/tmp/**", data["exclude"])
        self.assertEqual(data["count_daily"], "5")
        for key in ("schedule_weekly", "schedule_daily", "schedule_boot"):
            self.assertEqual(data[key], "false", "VabaxOS has its own timer")

    def test_ensure_config(self):
        class Result:
            stdout = "abcd-1234\n"
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "timeshift", "timeshift.json")
            self.assertTrue(vr.ensure_config(path, run=lambda *a, **k: Result()))
            self.assertEqual(json.load(open(path))["backup_device_uuid"], "abcd-1234")
            self.assertFalse(vr.ensure_config(path, run=lambda *a, **k: Result()), "nothing to change")

    def test_live_system(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "cmdline")
            with open(path, "w") as f:
                f.write("BOOT_IMAGE=/live/vmlinuz boot=live components quiet\n")
            self.assertTrue(vr.live_system(path))
            with open(path, "w") as f:
                f.write("BOOT_IMAGE=/vmlinuz root=UUID=1 ro quiet\n")
            self.assertFalse(vr.live_system(path))


class BeforeInstallTest(unittest.TestCase):

    def test_comment(self):
        self.assertEqual(vr.before_install_comment([]), "Before installing")
        self.assertEqual(vr.before_install_comment(["/var/cache/apt/archives/orca_50.2-1_all.deb"]),
                         "Before installing orca")
        names = [f"/x/{n}_1_amd64.deb" for n in ("gnome-shell", "orca", "mutter", "gedit")]
        self.assertEqual(vr.before_install_comment(names),
                         "Before installing 4 packages: gedit, gnome-shell, mutter…")

    def test_when(self):
        self.assertEqual(vr.should_copy_before_install(0, 10_000, False, 50), (True, ""))
        self.assertEqual(vr.should_copy_before_install(0, 10_000, True, 50), (False, "live"))
        self.assertEqual(vr.should_copy_before_install(0, 10_000, False, 5), (False, "space"))
        self.assertEqual(vr.should_copy_before_install(9_000, 10_000, False, 50), (False, "recent"))

    def test_apt_hook_with_made_up_timeshift(self):
        with tempfile.TemporaryDirectory() as tmp:
            bin_dir = os.path.join(tmp, "bin")
            os.makedirs(bin_dir)
            log = os.path.join(tmp, "timeshift.log")
            executable(os.path.join(bin_dir, "timeshift"),
                       f'#!/bin/sh\necho "$@" >> "{log}"\n[ "$1" = --list ] && cat "{tmp}/list"\nexit 0\n')
            executable(os.path.join(bin_dir, "findmnt"), "#!/bin/sh\necho root-uuid\n")
            with open(os.path.join(tmp, "list"), "w") as f:
                f.write(LIST)
            env = dict(os.environ, PATH=f"{bin_dir}:{os.environ['PATH']}", PYTHONPATH=LIB,
                       VABAXOS_TIMESHIFT_CONFIG=os.path.join(tmp, "timeshift.json"),
                       VABAXOS_RESTORE_STATE=os.path.join(tmp, "last"), LANGUAGE="C")
            debs = "/var/cache/apt/archives/orca_50.3-1_all.deb\n"
            first = subprocess.run([sys.executable, HELPER, "before-install"], input=debs, env=env,
                                   capture_output=True, text=True, timeout=30)
            second = subprocess.run([sys.executable, HELPER, "before-install"], input=debs, env=env,
                                    capture_output=True, text=True, timeout=30)
            calls = open(log).read().splitlines()
            config = json.load(open(os.path.join(tmp, "timeshift.json")))
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0)
        self.assertIn("(recent)", second.stderr, "one copy for one update")
        creates = [c for c in calls if c.startswith("--create")]
        self.assertEqual(creates, ["--create --comments Before installing orca --tags O --scripted"])
        self.assertEqual(config["backup_device_uuid"], "root-uuid")


class ConsoleTest(unittest.TestCase):

    def run_menu(self, answers, listing):
        calls = []

        class Result:
            def __init__(self, stdout="", code=0):
                self.stdout, self.returncode = stdout, code

        def runner(command):
            calls.append(command)
            if command[1] == "list":
                return Result(json.dumps(listing))
            return Result()
        said = []
        feed = iter(answers)
        old = os.geteuid
        os.geteuid = lambda: 0
        old_live = console.live_system
        console.live_system = lambda: False
        try:
            code = console.main(read=lambda _p: next(feed), write=said.append, runner=runner)
        finally:
            os.geteuid = old
            console.live_system = old_live
        return code, said, calls

    def test_restore_chosen_copy(self):
        listing = [{"name": "2026-10-30_10-00-01", "tags": "O", "comment": "x", "title": "30/10/2026 at 10:00: x"},
                   {"name": "2026-11-01_18-30-12", "tags": "O", "comment": "y", "title": "01/11/2026 at 18:30: y"}]
        code, said, calls = self.run_menu(["2", "yes"], listing)
        self.assertEqual(code, 0)
        self.assertIn("2. 01/11/2026 at 18:30: y", said)
        self.assertEqual(calls[-1][1:], ["restore", "2026-11-01_18-30-12"])

    def test_no_means_no(self):
        listing = [{"name": "a", "tags": "O", "comment": "", "title": "t"}]
        code, said, calls = self.run_menu(["1", "no"], listing)
        self.assertEqual(code, 0)
        self.assertNotIn("restore", [c[1] for c in calls])
        self.assertIn("Nothing changed.", said)

    def test_no_copies(self):
        code, said, _calls = self.run_menu([], [])
        self.assertEqual(code, 1)
        self.assertIn("No copy of the system was found.", said)

    def test_devices(self):
        class Result:
            stdout = ("/dev/sda /dev/sda1 vfat\n/dev/sda2 crypto_LUKS\n/dev/mapper/vg-root ext4\n"
                      "/dev/mapper/vg-swap swap\n")
        devices = console.block_devices(lambda command: Result())
        self.assertEqual(console.candidates(devices), ["/dev/mapper/vg-root"])
        self.assertEqual(console.encrypted(devices), ["/dev/sda2"])


CHILD = r'''
import importlib.machinery, importlib.util, json, sys
loader = importlib.machinery.SourceFileLoader("restore_program", sys.argv[1])
spec = importlib.util.spec_from_loader("restore_program", loader)
program = importlib.util.module_from_spec(spec)
loader.exec_module(program)
from gi.repository import Adw, GLib, Gtk
calls = []
LISTING = [{"name": "2026-10-30_10-00-01", "tags": "O", "comment": "", "title": "30/10/2026 at 10:00: copy"},
           {"name": "2026-11-01_18-30-12", "tags": "O", "comment": "", "title": "01/11/2026 at 18:30: copy"}]
def helper(*args):
    calls.append(args[0])
    return True, json.dumps(LISTING) if args[0] == "list" else ""
App, Window = program.window_main(helper)

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

app = Adw.Application(application_id="org.vabaxos.RestoreTest")
def check(app):
    window = Window(app)
    window.present()
    def later():
        if window.busy:
            return True
        print("ROWS:" + "|".join(r.get_title() for r in window.rows), flush=True)
        unnamed = [type(w).__name__ for w in walk(window) if isinstance(w, Gtk.Button) and w.get_mapped()
                   and not w.get_label() and not w.get_tooltip_text() and not inner(w)]
        print("UNNAMED:" + ",".join(unnamed), flush=True)
        window.confirm_restore(LISTING[1])
        GLib.timeout_add(300, dialog)
        return False
    def dialog():
        dialogs = [w for w in walk(window) if isinstance(w, Adw.AlertDialog)]
        print("DIALOG:%d" % len(dialogs), flush=True)
        dialogs[0].emit("response", "cancel")
        print("CALLS:" + ",".join(calls), flush=True)
        app.quit()
        return False
    GLib.timeout_add(300, later)
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
        self.assertEqual(out.get("ROWS"), "01/11/2026 at 18:30: copy|30/10/2026 at 10:00: copy", err)
        self.assertEqual(out.get("UNNAMED"), "", err)
        self.assertEqual(out.get("DIALOG"), "1", err)
        self.assertEqual(out.get("CALLS"), "list", "cancel restores nothing")


if __name__ == "__main__":
    unittest.main(verbosity=2)
