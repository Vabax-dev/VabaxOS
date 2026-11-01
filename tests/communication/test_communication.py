#!/usr/bin/env python3
"""Tests for vabaxos-communication: the Start menu entries open the right
pages in Firefox, safely, with Italian names; AccessGram downloaded on
request (a made-up archive, a damaged one, the fixed version checked
against the real code when ACCESSGRAM_SOURCE names a clone of it), and
its window on Broadway.

    python3 tests/communication/test_communication.py
"""

import configparser
import glob
import hashlib
import io
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import zipfile

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ENTRIES = os.path.join(REPO, "packages", "vabaxos-communication", "root", "usr", "share", "applications")
LIB = os.path.join(REPO, "packages", "vabaxos-communication", "root", "usr", "lib", "python3", "dist-packages")
PROGRAM = os.path.join(REPO, "packages", "vabaxos-communication", "root", "usr", "bin", "vabaxos-accessgram")
sys.path.insert(0, LIB)

from vabaxos_communication import accessgram  # noqa: E402
EXPECTED = {"org.vabaxos.WhatsApp.desktop": "https://web.whatsapp.com/",
            "org.vabaxos.Telegram.desktop": "https://web.telegram.org/a/",
            "org.vabaxos.VideoCall.desktop": "https://meet.jit.si/"}


class EntriesTest(unittest.TestCase):

    def test_entries(self):
        found = {os.path.basename(p): p for p in glob.glob(os.path.join(ENTRIES, "*.desktop"))}
        self.assertEqual(set(found), set(EXPECTED) | {"org.vabaxos.AccessGramSetup.desktop"})
        for name, url in EXPECTED.items():
            entry = configparser.ConfigParser(interpolation=None)
            entry.optionxform = str
            entry.read(found[name], encoding="utf-8")
            section = entry["Desktop Entry"]
            self.assertEqual(section["Exec"], f"firefox-esr --new-window {url}", name)
            self.assertTrue(url.startswith("https://"))
            self.assertIn("Comment[it]", section)
            self.assertTrue(section["Categories"].startswith("Network;"))


class Reply(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def archive(files, top="AccessGram-" + accessgram.COMMIT):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        z.writestr(top + "/", b"")
        for name, data in files.items():
            z.writestr(f"{top}/{name}", data)
    return buffer.getvalue()


FILES = {"accessgram/__init__.py": b"", "accessgram/__main__.py": b"print('hi')\n", "LICENSE": b"MIT"}


class AccessGramTest(unittest.TestCase):

    def setUp(self):
        self.home = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.home)
        self.saved = os.environ.get("XDG_DATA_HOME")
        os.environ["XDG_DATA_HOME"] = self.home
        self.addCleanup(self.restore)
        self.expected = accessgram.tree_hash(zipfile.ZipFile(io.BytesIO(archive(FILES))))

    def restore(self):
        if self.saved is None:
            os.environ.pop("XDG_DATA_HOME", None)
        else:
            os.environ["XDG_DATA_HOME"] = self.saved

    def test_install_and_remove(self):
        asked = []

        def opener(request, timeout=60):
            asked.append(request.full_url)
            return Reply(archive(FILES))
        target = accessgram.install(opener, expected=self.expected)
        self.assertEqual(asked, [accessgram.URL])
        self.assertTrue(accessgram.installed())
        with open(os.path.join(target, "accessgram", "__main__.py"), "rb") as f:
            self.assertEqual(f.read(), FILES["accessgram/__main__.py"])
        with open(accessgram.launcher_path(), encoding="utf-8") as f:
            self.assertIn(f"Exec=env PYTHONPATH={target} python3 -m accessgram", f.read())
        accessgram.remove()
        self.assertFalse(accessgram.installed())
        self.assertFalse(os.path.exists(accessgram.launcher_path()))

    def test_damaged_or_changed(self):
        changed = dict(FILES, **{"accessgram/__main__.py": b"import os; os.system('evil')"})
        with self.assertRaisesRegex(accessgram.InstallError, "damaged"):
            accessgram.install(lambda r, timeout=60: Reply(archive(changed)), expected=self.expected)
        with self.assertRaisesRegex(accessgram.InstallError, "damaged"):
            accessgram.install(lambda r, timeout=60: Reply(b"not a zip"), expected=self.expected)
        escaping = {"../evil.py": b"x"}
        with self.assertRaisesRegex(accessgram.InstallError, "damaged"):
            accessgram.install(lambda r, timeout=60: Reply(archive(escaping)),
                               expected=accessgram.tree_hash(zipfile.ZipFile(io.BytesIO(archive(escaping)))))
        self.assertFalse(accessgram.installed())

    @unittest.skipUnless(os.environ.get("ACCESSGRAM_SOURCE"), "no clone of AccessGram (ACCESSGRAM_SOURCE)")
    def test_fixed_version_is_the_real_one(self):
        source = os.environ["ACCESSGRAM_SOURCE"]
        commit = subprocess.run(["git", "-C", source, "rev-parse", "HEAD"], capture_output=True, text=True,
                                check=True).stdout.strip()
        self.assertEqual(commit, accessgram.COMMIT)
        files = [f for f in subprocess.run(["git", "-C", source, "ls-files"], capture_output=True, text=True,
                                           check=True).stdout.split("\n") if f]
        digest = hashlib.sha256()
        for name in sorted(files):
            digest.update(name.encode() + b"\0")
            with open(os.path.join(source, name), "rb") as f:
                digest.update(f.read())
            digest.update(b"\0")
        self.assertEqual(digest.hexdigest(), accessgram.TREE_SHA)


CHILD = r'''
import importlib.machinery, importlib.util, sys, types
loader = importlib.machinery.SourceFileLoader("agprog", sys.argv[1])
spec = importlib.util.spec_from_loader("agprog", loader)
program = importlib.util.module_from_spec(spec)
loader.exec_module(program)
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk

said, started, browsed = [], [], []
state = {"installed": False}
fake = types.SimpleNamespace(MY_TELEGRAM="https://my.telegram.org", installed=lambda: state["installed"],
                             install=lambda: state.update(installed=True), remove=lambda: state.update(installed=False))
App, Window = program.window_classes(speak=said.append, program=fake, starter=lambda: started.append(1),
                                     browser=browsed.append)
app = Adw.Application(application_id="org.vabaxos.AccessGramTest")

def check(app):
    window = Window(app)
    window.present()
    def step1():
        print("START:" + window.status.get_title() + " / " + window.main_button.get_label(), flush=True)
        window.main_action()
        GLib.timeout_add(300, step2)
        return False
    def step2():
        print("INSTALLED:" + said[-1] + " / " + window.main_button.get_label(), flush=True)
        window.main_action()
        print("OPEN:" + said[-1] + " " + str(started), flush=True)
        window.open_site()
        print("SITE:" + browsed[-1], flush=True)
        window.remove()
        print("REMOVED:" + said[-1] + " / " + window.main_button.get_label(), flush=True)
        app.quit()
        return False
    GLib.timeout_add(300, step1)

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
        self.assertEqual(out.get("START"), "Not installed: about 1 MB, from GitHub, the version checked by VabaxOS. / "
                                           "Download and install", err)
        self.assertEqual(out.get("INSTALLED"), "AccessGram installed: it is also in the Start menu. Open it with Open "
                                               "AccessGram. / Open AccessGram", err)
        self.assertEqual(out.get("OPEN"), "AccessGram opens. [1]", err)
        self.assertEqual(out.get("SITE"), "https://my.telegram.org", err)
        self.assertEqual(out.get("REMOVED"), "AccessGram removed. Your Telegram session stays in AccessGram's "
                                             "folder. / Download and install", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
