#!/usr/bin/env python3
"""Tests for vabaxos-orca-sounds: taking the kind of control out of what
Orca says, the Orca extension with a made-up Orca, the API of the real
Orca 51 when its source is at hand (ORCA_SOURCE, or the installed orca
package), the sounds made at build time, and the window on Broadway.

    python3 tests/orca-sounds/test_orca_sounds.py
"""

import ast
import importlib.machinery
import importlib.util
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import types
import unittest
import wave

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PACKAGE = os.path.join(REPO, "packages", "vabaxos-orca-sounds")
EXTENSION = os.path.join(PACKAGE, "root", "usr", "share", "vabaxos", "orca-extensions", "vabaxos_sounds",
                         "__init__.py")
PROGRAM = os.path.join(PACKAGE, "root", "usr", "bin", "vabaxos-orca-sounds")


def load(path, name, extra_modules=None):
    saved = {}
    for key, module in (extra_modules or {}).items():
        saved[key] = sys.modules.get(key)
        sys.modules[key] = module
    try:
        loader = importlib.machinery.SourceFileLoader(name, path)
        spec = importlib.util.spec_from_loader(name, loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        for key, module in saved.items():
            if module is None:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = module


class StripTest(unittest.TestCase):

    def setUp(self):
        self.sounds = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.sounds)
        for name in ("push-button", "check-box", "link"):
            open(os.path.join(self.sounds, name + ".wav"), "w").close()
        self.ext = load(EXTENSION, "vabaxos_sounds_plain")

    def strip(self, text, key, name):
        return self.ext.strip_role(text, key, name, self.sounds)

    def test_name_taken_out(self):
        self.assertEqual(self.strip("Nuova cartella pulsante", "push-button", "pulsante"),
                         ("Nuova cartella", os.path.join(self.sounds, "push-button.wav")))
        self.assertEqual(self.strip("Ricorda casella di controllo, non selezionata", "check-box",
                                    "casella di controllo")[0], "Ricorda, non selezionata")
        self.assertEqual(self.strip("Pulsante", "push-button", "pulsante")[0], "")
        self.assertEqual(self.strip("VabaxOS collegamento.", "link", "collegamento")[0], "VabaxOS.")

    def test_never_loses_information(self):
        self.assertIsNone(self.strip("Pulsantiera dei comandi", "push-button", "pulsante"), "whole words only")
        self.assertIsNone(self.strip("Nuova cartella", "push-button", "pulsante"), "name not said")
        self.assertIsNone(self.strip("Documenti cella", "table-cell", "cella"), "no sound for this role")
        self.assertIsNone(self.strip("Invia pulsante di scelta", "radio-button", "pulsante di scelta"),
                          "no sound file")
        self.assertIsNone(self.strip("", "push-button", "pulsante"))


class FakeResult:
    def __init__(self, text=None, consume=False):
        self.text, self.consume = text, consume

    @classmethod
    def replace(cls, text):
        return cls(text)

    @classmethod
    def consume_output(cls):
        return cls(consume=True)


class ExtensionTest(unittest.TestCase):

    def test_with_a_made_up_orca(self):
        fake = types.ModuleType("orca.extension")
        fake.Extension = type("Extension", (), {})
        fake.SpeechOutputResult = FakeResult
        fake.get_translation = lambda path: types.SimpleNamespace(gettext=lambda s: s)
        package = types.ModuleType("orca")
        package.extension = fake
        sounds = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, sounds)
        open(os.path.join(sounds, "push-button.wav"), "w").close()
        os.environ["VABAXOS_ORCA_SOUNDS"] = sounds
        try:
            ext = load(EXTENSION, "vabaxos_sounds_orca", {"orca": package, "orca.extension": fake})
        finally:
            del os.environ["VABAXOS_ORCA_SOUNDS"]
        played = []
        sounder = ext.VabaxosSounds()
        sounder.controller = types.SimpleNamespace(play_sound_file_internal=played.append)
        ext.role_of = lambda obj: obj
        output = types.SimpleNamespace
        result = sounder.on_speech_output(output(text="Salva pulsante", obj=("push-button", "pulsante")))
        self.assertEqual((result.text, result.consume), ("Salva", False))
        result = sounder.on_speech_output(output(text="pulsante", obj=("push-button", "pulsante")))
        self.assertTrue(result.consume, "the role alone: only the sound")
        self.assertEqual(len(played), 2)
        self.assertIsNone(sounder.on_speech_output(output(text="Ciao", obj=None)))
        self.assertIsNone(sounder.on_speech_output(output(text="Salva", obj=("push-button", "pulsante"))))


def orca_extension_source():
    folder = os.environ.get("ORCA_SOURCE")
    if folder:
        path = os.path.join(folder, "src", "orca", "extension.py")
        return path if os.path.exists(path) else None
    spec = importlib.util.find_spec("orca")
    if spec and spec.submodule_search_locations:
        path = os.path.join(list(spec.submodule_search_locations)[0], "extension.py")
        return path if os.path.exists(path) else None
    return None


@unittest.skipUnless(orca_extension_source(), "Orca 51 source not found (ORCA_SOURCE)")
class RealOrcaApiTest(unittest.TestCase):
    """What the extension uses exists in the real Orca."""

    def test_api(self):
        with open(orca_extension_source(), encoding="utf-8") as f:
            tree = ast.parse(f.read())
        classes = {n.name: n for n in tree.body if isinstance(n, ast.ClassDef)}
        functions = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
        self.assertIn("get_translation", functions)
        self.assertIn("on_speech_output", {f.name for f in classes["Extension"].body if isinstance(f, ast.FunctionDef)})
        result = {f.name for f in classes["SpeechOutputResult"].body if isinstance(f, ast.FunctionDef)}
        self.assertTrue({"replace", "consume_output"} <= result)
        fields = {n.target.id for n in classes["SpeechOutput"].body if isinstance(n, ast.AnnAssign)}
        self.assertEqual(fields, {"text", "obj"})
        source = os.path.dirname(orca_extension_source())
        with open(os.path.join(source, "dbus_service.py"), encoding="utf-8") as f:
            self.assertIn("def play_sound_file_internal", f.read())


class BuildTest(unittest.TestCase):

    def test_sounds_and_catalog(self):
        tree = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tree)
        subprocess.run([sys.executable, os.path.join(PACKAGE, "build"), tree], check=True,
                       env=dict(os.environ, REPO=REPO))
        folder = os.path.join(tree, "usr", "share", "vabaxos", "orca-sounds")
        ext = load(EXTENSION, "vabaxos_sounds_roles")
        for role in ext.ROLES:
            with wave.open(os.path.join(folder, role + ".wav")) as w:
                self.assertLess(w.getnframes() / w.getframerate(), 0.2, role)
        with open(os.path.join(folder, "push-button.wav"), "rb") as a, open(os.path.join(folder, "link.wav"),
                                                                            "rb") as b:
            self.assertNotEqual(a.read(), b.read())
        self.assertTrue(os.path.exists(os.path.join(tree, "usr", "share", "vabaxos", "orca-extensions",
                                                    "vabaxos_sounds", "locale", "it", "LC_MESSAGES",
                                                    "vabaxos_sounds.mo")))


class FakeOrca:
    def __init__(self, version):
        self.v, self.calls = version, []

    def version(self):
        return self.v

    def approve(self):
        self.calls.append("approve")
        return True

    def revoke(self):
        self.calls.append("revoke")

    def restart(self):
        self.calls.append("restart")


class ProgramTest(unittest.TestCase):

    def setUp(self):
        self.program = load(PROGRAM, "orcasoundsprog")
        self.folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.folder)
        self.source = os.path.dirname(EXTENSION)

    def test_old_orca(self):
        ok, sentence = self.program.turn_on(FakeOrca((50, 2)), self.source, self.folder)
        self.assertFalse(ok)
        self.assertIn("Orca 51", sentence)
        self.assertEqual(os.listdir(self.folder), [])

    def test_on_and_off(self):
        orca = FakeOrca((51, 0))
        ok, _sentence = self.program.turn_on(orca, self.source, self.folder)
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(os.path.join(self.folder, "vabaxos_sounds", "__init__.py")))
        self.assertFalse(any(name == "__pycache__" for _r, dirs, _f in os.walk(self.folder) for name in dirs))
        self.program.turn_off(orca, self.folder)
        self.assertEqual(orca.calls, ["approve", "restart", "revoke", "restart"])
        self.assertFalse(os.path.exists(os.path.join(self.folder, "vabaxos_sounds")))


CHILD = r'''
import importlib.machinery, importlib.util, sys
loader = importlib.machinery.SourceFileLoader("orcasounds", sys.argv[1])
spec = importlib.util.spec_from_loader("orcasounds", loader)
program = importlib.util.module_from_spec(spec)
loader.exec_module(program)
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk

class FakeOrca:
    def __init__(self, v): self.v = v
    def version(self): return self.v
    def approve(self): return True
    def revoke(self): pass
    def restart(self): pass

said, played = [], []
App, Window = program.window_classes(speak=said.append, orca=FakeOrca((51, 0)), player=played.append,
                                     folder=sys.argv[2], source=sys.argv[3])
App50, Window50 = program.window_classes(speak=said.append, orca=FakeOrca((50, 2)), player=played.append,
                                         folder=sys.argv[2], source=sys.argv[3])
app = Adw.Application(application_id="org.vabaxos.OrcaSoundsTest")

def check(app):
    window = Window(app)
    window.present()
    old = Window50(app)
    def step():
        window.rows[0].emit("activated")
        print("LISTEN:" + repr(played) + " " + said[-1], flush=True)
        window.switch.set_active(True)
        print("ON:" + said[-1], flush=True)
        print("OLD:" + str(old.switch.get_sensitive()) + " " + old.switch.get_subtitle(), flush=True)
        app.quit()
        return False
    GLib.timeout_add(400, step)

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
                   NO_AT_BRIDGE="1", LANGUAGE="C", LANG="C.UTF-8", PYTHONDONTWRITEBYTECODE="1")
        try:
            result = subprocess.run([sys.executable, "-c", CHILD, PROGRAM, folder, os.path.dirname(EXTENSION)],
                                    env=env, capture_output=True, text=True, timeout=60, check=False)
        finally:
            broadway.terminate()
            broadway.wait()
        out = dict(line.split(":", 1) for line in result.stdout.splitlines() if ":" in line)
        err = result.stderr[-3000:]
        self.assertEqual(out.get("LISTEN"), "['push-button'] Button", err)
        self.assertEqual(out.get("ON"), "Sounds on: Orca starts again.", err)
        self.assertEqual(out.get("OLD"), "False Needs Orca 51 or later; this VabaxOS has an older Orca. The sounds "
                                         "can be learnt already.", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
