#!/usr/bin/env python3
"""Tests for vabaxos-update (ADR-0020), with a fake PackageKit: nothing is
installed and no network is needed. The window runs on a hidden Broadway
display.

    python3 tests/update/test_update.py
"""

import contextlib
import enum
import importlib.machinery
import importlib.util
import io
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import types
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ROOT = os.path.join(REPO, "packages", "vabaxos-update", "root")
PROGRAM = os.path.join(ROOT, "usr", "bin", "vabaxos-update")
LIB = os.path.join(ROOT, "usr", "lib", "python3", "dist-packages")
sys.path.insert(0, LIB)

from vabaxos_update import core, history, settings  # noqa: E402

loader = importlib.machinery.SourceFileLoader("vabaxos_update", PROGRAM)
spec = importlib.util.spec_from_loader("vabaxos_update", loader)
update = importlib.util.module_from_spec(spec)
loader.exec_module(update)


class Info(enum.IntEnum):
    NORMAL = 3
    SECURITY = 8


class ProgressType(enum.IntEnum):
    PERCENTAGE = 1


class Flag(enum.IntEnum):
    ONLY_TRUSTED = 1
    ONLY_DOWNLOAD = 4


class Package:
    def __init__(self, name, info):
        self.name, self.info = name, info

    def get_id(self):
        return f"{self.name};1.0;amd64;debian"

    def get_info(self):
        return self.info


class FakeClient:
    def __init__(self, packages):
        self.packages = packages
        self.installed = None
        self.flags = None
        self.offline = False
        client = self
        self.pk = types.SimpleNamespace(
            InfoEnum=Info, ProgressType=ProgressType, TransactionFlagEnum=Flag,
            FilterEnum=types.SimpleNamespace(NONE=1),
            OfflineAction=types.SimpleNamespace(REBOOT="reboot"),
            offline_trigger=lambda action, cancellable: setattr(client, "offline", True))

    def refresh_cache(self, *args):
        pass

    def get_updates(self, *args):
        return types.SimpleNamespace(get_package_array=lambda: self.packages)

    def update_packages(self, flags, ids, cancellable, callback, data):
        self.flags, self.installed = flags, ids
        for percent in (10, 30, 55, 80, 100):
            callback(types.SimpleNamespace(props=types.SimpleNamespace(percentage=percent)),
                     ProgressType.PERCENTAGE)


def run(argv, packages):
    client = FakeClient(packages)
    out = io.StringIO()
    env = dict(os.environ)
    env.pop("DBUS_SESSION_BUS_ADDRESS", None)
    old = os.environ
    os.environ = env
    try:
        with contextlib.redirect_stdout(out):
            code = update.main(argv, update.Updater(client))
    finally:
        os.environ = old
    return code, out.getvalue(), client


class TempHome(unittest.TestCase):
    """Settings and state in a temporary folder."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.saved = {k: os.environ.get(k) for k in ("XDG_CONFIG_HOME", "XDG_STATE_HOME")}
        os.environ["XDG_CONFIG_HOME"] = os.path.join(self.tmp.name, "config")
        os.environ["XDG_STATE_HOME"] = os.path.join(self.tmp.name, "state")

    def tearDown(self):
        for key, value in self.saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self.tmp.cleanup()


class UpdateTest(TempHome):

    def setUp(self):
        super().setUp()
        update.flatpak_updates = lambda: 0

    def test_up_to_date(self):
        code, out, _ = run([], [])
        self.assertEqual(code, 0)
        self.assertIn("VabaxOS is up to date.", out)

    def test_check_counts_security_and_installs_nothing(self):
        code, out, client = run([], [Package("openssl", Info.SECURITY), Package("gedit", Info.NORMAL)])
        self.assertEqual(code, 0)
        self.assertIn("2 updates, 1 for security", out)
        self.assertIsNone(client.installed)

    def test_now_installs_and_says_progress(self):
        code, out, client = run(["--now"], [Package("openssl", Info.SECURITY)])
        self.assertEqual(code, 0)
        self.assertEqual(client.installed, ["openssl;1.0;amd64;debian"])
        for step in ("25", "50", "75"):
            self.assertIn(f"Updating: {step} percent.", out)
        self.assertIn("Update finished.", out)
        self.assertFalse(client.offline)

    def test_at_restart_downloads_and_triggers(self):
        code, out, client = run(["--at-restart"], [Package("gedit", Info.NORMAL)])
        self.assertEqual(code, 0)
        self.assertTrue(client.flags & (1 << int(Flag.ONLY_DOWNLOAD)))
        self.assertTrue(client.offline)
        self.assertIn("installed at the next start", out)

    def test_daily_is_silent_without_security(self):
        code, out, _ = run(["--daily"], [Package("gedit", Info.NORMAL)])
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_daily_speaks_for_security(self):
        _, out, _ = run(["--daily"], [Package("openssl", Info.SECURITY)])
        self.assertIn("1 security updates are ready", out)

    def test_daily_follows_the_settings(self):
        settings.save({"frequency": "daily", "notify": "all"})
        _, out, _ = run(["--daily"], [Package("gedit", Info.NORMAL)])
        self.assertIn("1 updates are ready", out)
        # Checked a moment ago: the next daily run waits.
        _, out, client = run(["--daily"], [Package("openssl", Info.SECURITY)])
        self.assertEqual(out, "")
        settings.save({"frequency": "never", "notify": "all"})
        os.remove(settings.state_path())
        _, out, _ = run(["--daily"], [Package("openssl", Info.SECURITY)])
        self.assertEqual(out, "")


class FakePackage(Package):
    def __init__(self, name, info, version="2.0"):
        super().__init__(name, info)
        self.version = version

    def get_id(self):
        return f"{self.name};{self.version};amd64;debian"

    def get_summary(self):
        return f"the {self.name} package"


class CoreTest(unittest.TestCase):

    def test_packagekit_kinds_and_versions(self):
        updates = core.from_packagekit([FakePackage("openssl", Info.SECURITY, "3.5.1-1"),
                                        FakePackage("gedit", Info.NORMAL)], Info.SECURITY)
        self.assertEqual([(u.name, u.version, u.kind) for u in updates],
                         [("openssl", "3.5.1-1", core.SECURITY), ("gedit", "2.0", core.SYSTEM)])
        self.assertEqual(updates[0].ident, "openssl;3.5.1-1;amd64;debian")
        self.assertEqual(updates[0].summary, "the openssl package")

    def test_flatpak(self):
        text = "org.mozilla.firefox\tFirefox\t140.1\ncom.example.App\t\t\n\n"
        updates = core.parse_flatpak(text)
        self.assertEqual([(u.name, u.version, u.kind) for u in updates],
                         [("Firefox", "140.1", core.APPS), ("com.example.App", "", core.APPS)])

    def test_firmware(self):
        text = ('{"Devices": [{"Name": "UEFI dbx", "DeviceId": "abc", "Releases": '
                '[{"Version": "371", "Summary": "Secure Boot list"}]}, {"Name": "Disk", "Releases": []}]}')
        updates = core.parse_fwupd(text)
        self.assertEqual([(u.name, u.version, u.kind, u.ident) for u in updates],
                         [("UEFI dbx", "371", core.FIRMWARE, "abc")])
        self.assertEqual(core.parse_fwupd("not json"), [])
        self.assertEqual(core.parse_fwupd(""), [])

    def test_critical_updates_change_desktop_or_voice(self):
        updates = [core.Update("gnome-shell"), core.Update("orca", kind=core.SECURITY),
                   core.Update("linux-image-6.19-amd64"), core.Update("gedit"),
                   core.Update("org.gnome.Orca.Fake", kind=core.APPS)]
        self.assertEqual(core.critical(updates), ["gnome-shell", "linux-image-6.19-amd64", "orca"])


HISTORY = """Start-Date: 2026-10-30  10:01:02
Commandline: packagekit role='update-packages'
Upgrade: openssl:amd64 (3.5.0-1, 3.5.1-1), libssl3t64:amd64 (3.5.0-1, 3.5.1-1)
Install: linux-image-6.19-amd64:amd64 (6.19-1, automatic)
End-Date: 2026-10-30  10:03:00

Start-Date: 2026-10-31  18:00:00
Commandline: apt remove gedit
Remove: gedit:amd64 (48.0-1)
End-Date: 2026-10-31  18:00:05
"""


class HistoryTest(unittest.TestCase):

    def test_parse(self):
        entries = history.parse(HISTORY)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].changes["Upgrade"], ["openssl", "libssl3t64"])
        self.assertEqual(entries[0].changes["Install"], ["linux-image-6.19-amd64"])
        self.assertEqual(entries[1].total("Remove"), 1)

    def test_read_newest_first_also_rotated(self):
        import gzip
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "history.log")
            with open(path, "w", encoding="utf-8") as f:
                f.write(HISTORY)
            with gzip.open(path + ".1.gz", "wt", encoding="utf-8") as f:
                f.write("Start-Date: 2026-09-01  09:00:00\nInstall: orca:amd64 (50.2-1)\n")
            entries = history.read(path)
        self.assertEqual([e.date for e in entries],
                         ["2026-10-31  18:00:00", "2026-10-30  10:01:02", "2026-09-01  09:00:00"])

    def test_missing_log(self):
        self.assertEqual(history.read("/nonexistent/history.log"), [])


class SettingsTest(TempHome):

    def test_defaults_and_bad_values(self):
        self.assertEqual(settings.load(), settings.DEFAULTS)
        settings.save({"frequency": "hourly", "notify": "all"})
        self.assertEqual(settings.load(), {"frequency": "daily", "notify": "all"})

    def test_when_the_check_is_due(self):
        day = settings.DAY
        daily, weekly, never = ({"frequency": f, "notify": "security"} for f in ("daily", "weekly", "never"))
        self.assertTrue(settings.check_due(daily, 0, 10 * day))
        self.assertFalse(settings.check_due(daily, 10 * day - 3600, 10 * day))
        self.assertTrue(settings.check_due(daily, 9 * day, 10 * day))
        self.assertFalse(settings.check_due(weekly, 5 * day, 10 * day))
        self.assertFalse(settings.check_due(never, 0, 10 * day))
        settings.mark_checked(1234)
        self.assertEqual(settings.last_check(), 1234)


CHILD = r'''
import importlib.machinery, importlib.util, sys, enum, types, time
loader = importlib.machinery.SourceFileLoader("vabaxos_update_program", sys.argv[1])
spec = importlib.util.spec_from_loader("vabaxos_update_program", loader)
program = importlib.util.module_from_spec(spec)
loader.exec_module(program)
program.unchecked_sources = lambda: True
program.update_flatpak = lambda: None
program.update_firmware = lambda: None
from vabaxos_update import core, window as uw
core.flatpak_updates = lambda run=None: [core.Update("Firefox", "140.1", core.APPS)]
core.firmware_updates = lambda run=None: []
from gi.repository import Adw, GLib, Gtk

class Info(enum.IntEnum):
    NORMAL = 3
    SECURITY = 8

class Package:
    def __init__(self, name, info): self.name, self.info = name, info
    def get_id(self): return f"{self.name};2.0;amd64;debian"
    def get_info(self): return self.info
    def get_summary(self): return ""

class FakeUpdater:
    pk = types.SimpleNamespace(InfoEnum=Info)
    installed = []
    def __init__(self): self.cancellable = None; self.restart = "system"
    def packages(self): return [Package("openssl", Info.SECURITY), Package("orca", Info.NORMAL)]
    def install(self, ids, at_restart=False): FakeUpdater.installed.append((list(ids), at_restart))

def walk(widget):
    yield widget
    child = widget.get_first_child()
    while child is not None:
        yield from walk(child)
        child = child.get_next_sibling()

app = Adw.Application(application_id="org.vabaxos.UpdateTest")
def check(app):
    window = uw.UpdateWindow(app, program, updater_factory=FakeUpdater, history_path=sys.argv[2])
    window.present()
    window.check()
    def after_check():
        if window.busy:
            return True
        print("STATE:" + window.state_row.get_title(), flush=True)
        print("GROUPS:" + "|".join(row.get_subtitle() for row, _c in window.expanders.values()), flush=True)
        print("HISTORY:%d" % len(window.history_rows), flush=True)
        print("NOW:%s" % window.now_button.get_sensitive(), flush=True)
        # The tabs and the toast's close button are named by libadwaita itself.
        def inner(w):
            p = w
            while p is not None:
                if type(p).__name__ in ("AdwViewSwitcherButton", "AdwToastWidget", "WindowControls"):
                    return True
                p = p.get_parent()
            return False
        unnamed = [type(w).__name__ for w in walk(window) if isinstance(w, Gtk.Button) and w.get_mapped()
                   and not w.get_label() and not w.get_tooltip_text() and not inner(w)]
        print("UNNAMED:" + ",".join(unnamed), flush=True)
        # Orca is updated: the window advises the next start.
        window.install(False)
        GLib.timeout_add(300, dialog_up)
        return False
    def dialog_up():
        dialogs = [w for w in walk(window) if isinstance(w, Adw.AlertDialog)]
        print("DIALOG:%d" % len(dialogs), flush=True)
        if dialogs:
            dialogs[0].emit("response", "restart")
        GLib.timeout_add(300, installed)
        return False
    def installed():
        if window.busy:
            return True
        print("INSTALLED:%s" % FakeUpdater.installed, flush=True)
        print("AFTER:" + window.state_row.get_title(), flush=True)
        app.quit()
        return False
    GLib.timeout_add(300, after_check)
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

    def test_check_groups_history_and_advice(self):
        display = free_display()
        broadway = subprocess.Popen(["gtk4-broadwayd", f":{display}"], stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
        time.sleep(1)
        with tempfile.TemporaryDirectory() as tmp:
            log = os.path.join(tmp, "history.log")
            with open(log, "w", encoding="utf-8") as f:
                f.write(HISTORY)
            env = dict(os.environ, GDK_BACKEND="broadway", BROADWAY_DISPLAY=f":{display}",
                       GSETTINGS_BACKEND="memory", NO_AT_BRIDGE="1", PYTHONPATH=LIB,
                       XDG_CONFIG_HOME=tmp, XDG_STATE_HOME=tmp,
                       LANGUAGE="C", LANG="C.UTF-8", PYTHONDONTWRITEBYTECODE="1")
            try:
                result = subprocess.run([sys.executable, "-c", CHILD, PROGRAM, log], env=env,
                                        capture_output=True, text=True, timeout=60)
            finally:
                broadway.terminate()
                broadway.wait()
        out = dict(line.split(":", 1) for line in result.stdout.splitlines() if ":" in line)
        err = result.stderr[-2000:]
        self.assertEqual(out.get("STATE"), "3 updates, 1 for security.", err)
        self.assertEqual(out.get("GROUPS"), "1 update|1 update|1 update|Nothing to update", err)
        self.assertEqual(out.get("HISTORY"), "2", err)
        self.assertEqual(out.get("NOW"), "True", err)
        self.assertEqual(out.get("UNNAMED"), "", err)
        self.assertEqual(out.get("DIALOG"), "1", err)
        self.assertEqual(out.get("INSTALLED"),
                         "[(['openssl;2.0;amd64;debian', 'orca;2.0;amd64;debian'], True)]", err)
        self.assertEqual(out.get("AFTER"), "Ready. The updates will be installed at the next start.", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
