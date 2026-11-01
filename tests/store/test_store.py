#!/usr/bin/env python3
"""Tests for vabaxos-store: the answers of appstreamcli and flatpak, the
search of both, PackageKit and flatpak actions with made-up tools, and
the window on Broadway with a made-up search and made-up actions.

    python3 tests/store/test_store.py
"""

import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from types import SimpleNamespace

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ROOT = os.path.join(REPO, "packages", "vabaxos-store", "root")
LIB = os.path.join(ROOT, "usr", "lib", "python3", "dist-packages")
PROGRAM = os.path.join(ROOT, "usr", "bin", "vabaxos-store")
sys.path.insert(0, LIB)

import vabaxos_store as store  # noqa: E402
from vabaxos_store import actions  # noqa: E402

APPSTREAM = """Identifier: org.audacityteam.Audacity [desktop-application]
Internal ID: os/package/os/org.audacityteam.Audacity/*
Name: Audacity
Summary: Record and edit audio files
Package: audacity
Homepage: https://www.audacityteam.org/
License: GPL-2.0+
Description:
  Audacity is a multi-track audio editor.
  It records, plays and edits sound.
Categories:
  - AudioVideo
---
Identifier: org.gnome.Software.WebApp_123.desktop [web-application]
Name: Photopea
Summary: Online photo editor
---
Identifier: org.gnome.Sound.Plugin [addon]
Name: Sound plugin
Package: sound-plugin
---
Identifier: org.tenacityaudio.Tenacity [desktop-application]
Name: Tenacity
Summary: Easy-to-use audio editor
Package: tenacity
---
Identifier: libreoffice-writer.desktop [desktop-application]
Name: LibreOffice Writer
Summary: Word processor
---
Identifier: org.audacityteam.Audacity.desktop [desktop-application]
Name: Audacity
Summary: Duplicate entry of the same package
Package: audacity
"""

FLATPAK = ("com.spotify.Client\tSpotify\tOnline music streaming service\t1.2.3\tflathub\n"
           "org.audacityteam.Audacity\tAudacity\tAudio editor\t3.7\tflathub\n"
           "org.other.App\tOther\tFrom another remote\t1\tfedora\n")


def fake_run(answers):
    calls = []

    def run(command, timeout=120):
        calls.append(command)
        for words, answer in answers.items():
            if tuple(command[:len(words)]) == words:
                return answer(command) if callable(answer) else answer
        return ""
    run.calls = calls
    return run


class ParseTest(unittest.TestCase):

    def test_appstream(self):
        apps = store.parse_appstream(APPSTREAM, owner=lambda ident: "libreoffice-writer"
                                     if ident.startswith("libreoffice") else None)
        self.assertEqual([(a.name, a.package) for a in apps],
                         [("Audacity", "audacity"), ("Tenacity", "tenacity"),
                          ("LibreOffice Writer", "libreoffice-writer"), ("Audacity", "audacity")])
        self.assertEqual(apps[0].extra["description"],
                         "Audacity is a multi-track audio editor. It records, plays and edits sound.")
        self.assertEqual(apps[0].extra["license"], "GPL-2.0+")

    def test_flatpak(self):
        apps = store.parse_flatpak_search(FLATPAK + "No matches found\n")
        self.assertEqual([(a.name, a.package, a.source) for a in apps],
                         [("Spotify", "com.spotify.Client", "flathub"),
                          ("Audacity", "org.audacityteam.Audacity", "flathub")])

    def test_describe_and_protected(self):
        self.assertEqual(store.App("x", "Audacity", "Record and edit audio files.", installed=True).describe(),
                         "Audacity, Record and edit audio files, from Debian, installed")
        self.assertEqual(store.App("x", "Spotify", "Music", "flathub").describe(), "Spotify, Music, from Flathub")
        self.assertTrue(store.App("x", "Orca", package="orca").protected)
        self.assertTrue(store.App("x", "Reader", package="vabaxos-reader").protected)
        self.assertFalse(store.App("x", "Orca", source="flathub", package="orca").protected)


class SearchTest(unittest.TestCase):

    def run_for(self):
        return fake_run({
            ("appstreamcli", "search"): APPSTREAM,
            ("dpkg-query", "-W"): lambda c: "ii " if c[-1] == "tenacity" else "un ",
            ("dpkg-query", "-S"): "",
            ("flatpak", "search"): FLATPAK,
            ("flatpak", "list"): "com.spotify.Client\n",
        })

    def test_debian_only(self):
        run = self.run_for()
        apps = store.search("audacity", run=run)
        self.assertEqual([(a.name, a.installed) for a in apps], [("Audacity", False), ("Tenacity", True)])
        self.assertFalse(any(c[0] == "flatpak" for c in run.calls))
        self.assertEqual(store.search("a", run=run), [], "one letter: no search yet")

    def test_with_flathub(self):
        apps = store.search("spotify", flathub=True, run=self.run_for())
        self.assertEqual([(a.name, a.source, a.installed) for a in apps][-2:],
                         [("Spotify", "flathub", True), ("Audacity", "flathub", False)])

    def test_settings_and_catalog(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "vabaxos", "store.json")
            self.assertEqual(store.load_settings(path), {"flathub": False})
            store.save_settings({"flathub": True}, path)
            self.assertEqual(store.load_settings(path), {"flathub": True})
            self.assertFalse(store.catalog_ready([folder + "/none"]))
            self.assertTrue(store.catalog_ready([folder]))


class FakePk:
    FilterEnum = SimpleNamespace(INSTALLED=2, NOT_INSTALLED=3)
    TransactionFlagEnum = SimpleNamespace(ONLY_TRUSTED=1)
    ProgressType = SimpleNamespace(PERCENTAGE=1)


class FakeClient:
    def __init__(self, ids):
        self.ids = ids
        self.calls = []

    def resolve(self, filters, packages, cancellable, callback, data):
        self.calls.append(("resolve", filters, packages))
        return SimpleNamespace(get_package_array=lambda: [SimpleNamespace(get_id=lambda i=i: i) for i in self.ids])

    def install_packages(self, flags, ids, cancellable, callback, data):
        self.calls.append(("install", flags, ids))
        for percent in (10, 30, 55, 80, 100):
            callback(SimpleNamespace(props=SimpleNamespace(percentage=percent)), FakePk.ProgressType.PERCENTAGE)

    def remove_packages(self, flags, ids, allow_deps, autoremove, cancellable, callback, data):
        self.calls.append(("remove", ids, allow_deps, autoremove))


class ActionsTest(unittest.TestCase):

    def test_packagekit(self):
        arch = subprocess.run(["dpkg", "--print-architecture"], capture_output=True, text=True).stdout.strip()
        client = FakeClient(["audacity;3.7;i386;debian", f"audacity;3.7;{arch};debian"])
        pk = actions.PackageKit(client, FakePk)
        steps = []
        pk.install("audacity", steps.append)
        self.assertEqual(client.calls[0], ("resolve", 1 << 3, ["audacity"]))
        self.assertEqual(client.calls[1], ("install", 1 << 1, [f"audacity;3.7;{arch};debian"]))
        self.assertEqual(steps, [25, 50, 75])
        pk.remove("audacity")
        self.assertEqual(client.calls[-1][2:], (False, True), "never remove other programs with it")
        with self.assertRaises(actions.ActionError):
            actions.PackageKit(FakeClient([]), FakePk).install("nothing")

    def test_flatpak_and_protected(self):
        commands = []

        def run(command, **_kwargs):
            commands.append(command)
            return SimpleNamespace(returncode=1 if "fail" in command else 0, stderr="error: no network\n")
        acts = actions.Actions(packagekit="unused", run=run)
        acts.install(store.App("com.spotify.Client", "Spotify", source="flathub", package="com.spotify.Client"))
        self.assertEqual(commands[-1], ["flatpak", "install", "--user", "-y", "--noninteractive", "flathub",
                                        "com.spotify.Client"])
        with self.assertRaisesRegex(actions.ActionError, "no network"):
            acts.install(store.App("fail", "Fail", source="flathub", package="fail"))
        with self.assertRaises(actions.ActionError):
            acts.remove(store.App("orca", "Orca", package="orca"))

    def test_enable_flathub(self):
        commands = []
        store.enable_flathub(lambda command, **_k: commands.append(command) or SimpleNamespace(returncode=0))
        self.assertEqual(commands[0][:4], ["flatpak", "remote-add", "--user", "--if-not-exists"])
        self.assertEqual(commands[1], ["flatpak", "update", "--user", "--appstream", "flathub"])


CHILD = r'''
import importlib.machinery, importlib.util, sys
loader = importlib.machinery.SourceFileLoader("storeprog", sys.argv[1])
spec = importlib.util.spec_from_loader("storeprog", loader)
program = importlib.util.module_from_spec(spec)
loader.exec_module(program)
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk
from vabaxos_store import App

said, searched = [], []

def searcher(query, flathub):
    searched.append((query, flathub))
    return [App("org.audacityteam.Audacity", "Audacity", "Record and edit audio files", package="audacity",
                extra={"description": "A multi-track audio editor.", "license": "GPL-2.0+"}),
            App("com.spotify.Client", "Spotify", "Music", "flathub", "com.spotify.Client", installed=True)]

class FakeActions:
    def __init__(self): self.done = []
    def install(self, app, progress):
        progress(50)
        self.done.append(("install", app.package))
    def remove(self, app, progress): self.done.append(("remove", app.package))
    def open(self, app): return True
    def refresh(self): self.done.append(("refresh",))

App_, Window = program.window_classes(speak=said.append, searcher=searcher, actions_class=FakeActions,
                                      settings_path=sys.argv[2], flathub_enabler=lambda: None,
                                      catalog_ready=lambda: False)
app = Adw.Application(application_id="org.vabaxos.StoreTest")

def walk(widget):
    child = widget.get_first_child()
    while child:
        yield child
        yield from walk(child)
        child = child.get_next_sibling()

def inner(w):
    while w is not None:
        if type(w).__name__ in ("AdwToastWidget", "WindowControls", "AdwBackButton"):
            return True
        w = w.get_parent()
    return False

def check(app):
    window = Window(app)
    window.present()
    def step1():
        print("CATALOG:" + "|".join(said), flush=True)
        window.entry.set_text("audio")
        window.search()
        GLib.timeout_add(600, step2)
        return False
    def step2():
        print("FOUND:" + said[-1], flush=True)
        print("ROWS:" + "|".join(r.get_title() + " - " + r.get_subtitle() for r in window.rows), flush=True)
        window.details(window.apps[0])
        print("DETAILS:" + window.dialog.get_body().replace("\n\n", " / "), flush=True)
        window.dialog.emit("response", "install")
        GLib.timeout_add(600, step3)
        return False
    def step3():
        print("INSTALL:" + "|".join(said[-3:]), flush=True)
        print("ACTIONS:" + repr(window.actions.done), flush=True)
        print("ROW:" + window.rows[0].get_subtitle(), flush=True)
        window.flathub.set_active(True)
        GLib.timeout_add(600, step4)
        return False
    def step4():
        print("FLATHUB:" + repr(searched[-1]) + " " + open(sys.argv[2]).read(), flush=True)
        window.escape()
        print("ESCAPE:" + repr(window.entry.get_text()) + " " + window.results.get_description(), flush=True)
        unnamed = [type(w).__name__ for w in walk(window) if isinstance(w, Gtk.Button) and w.get_mapped()
                   and not w.get_label() and not w.get_tooltip_text() and not inner(w)]
        print("UNNAMED:" + ",".join(unnamed), flush=True)
        app.quit()
        return False
    GLib.timeout_add(600, step1)

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
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder)
        env = dict(os.environ, GDK_BACKEND="broadway", BROADWAY_DISPLAY=f":{display}", GSETTINGS_BACKEND="memory",
                   NO_AT_BRIDGE="1", PYTHONPATH=LIB, LANGUAGE="C", LANG="C.UTF-8", PYTHONDONTWRITEBYTECODE="1")
        try:
            result = subprocess.run([sys.executable, "-c", CHILD, PROGRAM, os.path.join(folder, "store.json")],
                                    env=env, capture_output=True, text=True, timeout=60, check=False)
        finally:
            broadway.terminate()
            broadway.wait()
        out = dict(line.split(":", 1) for line in result.stdout.splitlines() if ":" in line)
        err = result.stderr[-3000:]
        self.assertEqual(out.get("CATALOG"), "Downloading the list of programs: it can take a minute.|"
                                             "List of programs ready.", err)
        self.assertEqual(out.get("FOUND"), "2 programs found.", err)
        self.assertEqual(out.get("ROWS"), "Audacity - Record and edit audio files, from Debian|"
                                          "Spotify - Music, from Flathub, installed", err)
        self.assertEqual(out.get("DETAILS"), "Record and edit audio files. / A multi-track audio editor. / "
                                             "From Debian. / License: GPL-2.0+.", err)
        self.assertEqual(out.get("INSTALL"), "Installing Audacity. It can take some minutes.|50 percent.|"
                                             "Audacity installed. You find it in the Start menu.", err)
        self.assertEqual(out.get("ACTIONS"), "[('refresh',), ('install', 'audacity')]", err)
        self.assertEqual(out.get("ROW"), "Record and edit audio files, from Debian, installed", err)
        self.assertEqual(out.get("FLATHUB"), "('audio', True) {\"flathub\": true}", err)
        self.assertEqual(out.get("ESCAPE"), "'' The programs appear here while you write.", err)
        self.assertEqual(out.get("UNNAMED"), "", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
