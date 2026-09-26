#!/usr/bin/env python3
"""Tests for vabaxos-update (ADR-0020), with a fake PackageKit: nothing is
installed and no network is needed.

    python3 tests/update/test_update.py
"""

import contextlib
import enum
import importlib.machinery
import importlib.util
import io
import os
import subprocess
import tempfile
import types
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROGRAM = os.path.join(REPO, "packages", "vabaxos-update", "root", "usr", "bin", "vabaxos-update")

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
        self.rounds = getattr(self, "rounds", []) + [ids]
        self.packages = [p for p in self.packages if p.get_id() not in ids] + getattr(self, "after", [])
        self.after = []
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


class UpdateTest(unittest.TestCase):

    def setUp(self):
        update.flatpak_updates = lambda: 0
        self.saved = update.installed_snapshot, update.security_snapshot
        update.installed_snapshot = lambda path=None: None
        update.security_snapshot = lambda installed: None

    def tearDown(self):
        update.installed_snapshot, update.security_snapshot = self.saved

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

    def test_note_only_without_vabaxos_sources(self):
        _, out, _ = run([], [Package("gedit", Info.NORMAL)])
        self.assertIn("straight from Debian testing", out)
        update.installed_snapshot = lambda path=None: "20260924T000000Z"
        _, out, _ = run([], [Package("gedit", Info.NORMAL)])
        self.assertNotIn("straight from Debian testing", out)

    def test_daily_speaks_for_a_date_moved_for_security(self):
        update.installed_snapshot = lambda path=None: "20260924T000000Z"
        update.security_snapshot = lambda installed: "20261001T000000Z"
        _, out, _ = run(["--daily"], [Package("vabaxos-apt", Info.NORMAL), Package("gedit", Info.NORMAL)])
        self.assertIn("1 security updates are ready", out)

    def test_new_debian_date_first(self):
        client = FakeClient([Package("vabaxos-apt", Info.NORMAL), Package("gedit", Info.NORMAL)])
        client.after = [Package("openssl", Info.NORMAL)]
        env = dict(os.environ)
        env.pop("DBUS_SESSION_BUS_ADDRESS", None)
        old, os.environ = os.environ, env
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                code = update.main(["--now"], update.Updater(client))
        finally:
            os.environ = old
        self.assertEqual(code, 0)
        self.assertEqual(client.rounds, [["vabaxos-apt;1.0;amd64;debian"],
                                         ["gedit;1.0;amd64;debian", "openssl;1.0;amd64;debian"]])


class SnapshotTest(unittest.TestCase):

    def test_installed_snapshot(self):
        with tempfile.NamedTemporaryFile("w", suffix=".sources") as f:
            f.write("Types: deb\nURIs: https://snapshot.debian.org/archive/debian/20260924T000000Z/\n")
            f.flush()
            self.assertEqual(update.installed_snapshot(f.name), "20260924T000000Z")
        self.assertIsNone(update.installed_snapshot("/nonexistent"))

    def test_security_snapshot_only_when_newer(self):
        shown = ("Package: vabaxos-apt\nVersion: 0.1.0~alpha.2\nVabaxos-Security-Snapshot: 20261001T000000Z\n\n"
                 "Package: vabaxos-apt\nVersion: 0.1.0~alpha.1\n\n")
        real_run, real_which = subprocess.run, update.shutil.which
        update.subprocess.run = lambda *a, **k: types.SimpleNamespace(stdout=shown)
        update.shutil.which = lambda name: "/usr/bin/" + name
        try:
            self.assertEqual(update.security_snapshot("20260924T000000Z"), "20261001T000000Z")
            self.assertIsNone(update.security_snapshot("20261001T000000Z"))
            self.assertIsNone(update.security_snapshot(None))
        finally:
            update.subprocess.run, update.shutil.which = real_run, real_which


if __name__ == "__main__":
    unittest.main(verbosity=2)
