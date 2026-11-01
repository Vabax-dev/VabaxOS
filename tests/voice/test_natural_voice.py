#!/usr/bin/env python3
"""Tests for the natural voice on request: how text is cut into parts (the
first words alone), the download of the model with made-up files, the
speed verdict, and the window on Broadway with a made-up model and Orca.
No Kokoro model needed; with VABAXOS_KOKORO_DIR set, the real model is
measured too.

    python3 tests/voice/test_natural_voice.py
"""

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

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ROOT = os.path.join(REPO, "packages", "vabaxos-voice", "root")
LIB = os.path.join(ROOT, "usr", "lib", "python3", "dist-packages")
PROGRAM = os.path.join(ROOT, "usr", "bin", "vabaxos-natural-voice")
sys.path.insert(0, LIB)
os.environ["VABAXOS_KOKORO_FIRST_WORDS"] = "3"

try:
    from vabaxos_voice import engine, model
except ImportError as error:  # numpy is missing
    engine = model = None
    MISSING = str(error)


@unittest.skipIf(engine is None, "numpy is not installed")
class SplitTest(unittest.TestCase):

    def test_first_words_alone(self):
        self.assertEqual(engine.split("Il documento è stato salvato nella cartella Documenti."),
                         ["Il documento è stato", "salvato nella cartella Documenti."])
        self.assertEqual(engine.split("Save the file in the folder of your documents now"),
                         ["Save the file", "in the folder of your documents now"])

    def test_never_after_a_function_word(self):
        self.assertEqual(engine.split("Apri la cartella dei documenti di oggi")[0], "Apri la cartella")
        self.assertEqual(engine.split("Il file della relazione di ieri è pronto")[0], "Il file della relazione")

    def test_short_texts_stay_whole(self):
        self.assertEqual(engine.split("Nuova cartella pulsante"), ["Nuova cartella pulsante"])
        self.assertEqual(engine.split("Apri il file della relazione"), ["Apri il file della relazione"])
        self.assertEqual(engine.split("Salva con nome, finestra di dialogo"),
                         ["Salva con nome,", "finestra di dialogo"])

    def test_long_clauses_are_cut(self):
        text = " ".join(f"parola{i}" for i in range(40))
        parts = engine.split(text)
        self.assertEqual(" ".join(parts), text)
        self.assertTrue(all(len(p.split()) <= engine.MAX_WORDS + 3 for p in parts))
        self.assertEqual(len(parts[0].split()), 3)

    def test_setting(self):
        self.assertEqual(engine.split("Il documento è stato salvato nella cartella.", first_words=0),
                         ["Il documento è stato salvato nella cartella."])
        with tempfile.NamedTemporaryFile("w", suffix=".conf", delete=False) as f:
            f.write("engine=espeak\nfirst_words=5  # comment\n")
        self.addCleanup(os.remove, f.name)
        saved = os.environ.pop("VABAXOS_KOKORO_FIRST_WORDS")
        try:
            self.assertEqual(engine.first_words_setting(f.name), 5)
            self.assertEqual(engine.first_words_setting("/nonexistent"), engine.FIRST_WORDS)
        finally:
            os.environ["VABAXOS_KOKORO_FIRST_WORDS"] = saved


class FakeReply(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


@unittest.skipIf(model is None, "numpy is not installed")
class ModelTest(unittest.TestCase):

    def setUp(self):
        self.folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.folder)
        self.data = {engine.MODEL: b"model" * 1000, engine.VOICES_FILE: b"voices" * 500}
        self.saved = model.FILES, model.TOTAL
        model.FILES = [(name, hashlib.sha256(data).hexdigest(), len(data)) for name, data in self.data.items()]
        model.TOTAL = sum(len(d) for d in self.data.values())
        self.addCleanup(self.restore)

    def restore(self):
        model.FILES, model.TOTAL = self.saved

    def opener(self, url, timeout=60):
        self.assertTrue(url.startswith(model.BASE))
        return FakeReply(self.data[url.rsplit("/", 1)[-1]])

    def test_install_and_remove(self):
        steps = []
        model.install(lambda done, total: steps.append((done, total)), folder=self.folder, opener=self.opener)
        self.assertTrue(model.downloaded(self.folder))
        self.assertEqual(steps[-1], (model.TOTAL, model.TOTAL))
        model.save_speed(250, self.folder)
        self.assertEqual(model.load_speed(self.folder)["verdict"], "fast")
        model.remove(self.folder)
        self.assertFalse(model.downloaded(self.folder))
        self.assertIsNone(model.load_speed(self.folder))

    def test_damaged_and_cancelled(self):
        self.data[engine.VOICES_FILE] = b"other"
        with self.assertRaisesRegex(model.DownloadError, "damaged"):
            model.install(folder=self.folder, opener=self.opener)
        self.assertFalse(os.path.exists(os.path.join(self.folder, engine.VOICES_FILE + ".part")))
        with self.assertRaisesRegex(model.DownloadError, "cancelled"):
            model.install(folder=tempfile.mkdtemp(dir=self.folder), cancelled=lambda: True, opener=self.opener)

    def test_verdict(self):
        self.assertEqual([model.verdict(ms) for ms in (150, 300, 450, 601)], ["fast", "fast", "slow", "too-slow"])

    def test_pinned_files_match_the_build(self):
        """The same files and SHA-256 as packages/vabaxos-voice/fetch."""
        with open(os.path.join(REPO, "packages", "vabaxos-voice", "fetch"), encoding="utf-8") as f:
            fetched = {line.split()[0].rsplit("/", 1)[-1]: line.split()[1] for line in f
                       if line.strip() and not line.startswith("#")}
        self.assertEqual({name: sha for name, sha, _size in self.saved[0]}, fetched)

    @unittest.skipUnless(os.environ.get("VABAXOS_KOKORO_DIR"), "no Kokoro model")
    def test_measure_the_real_model(self):
        ms = model.measure()
        self.assertGreater(ms, 0)
        print(f"\nKokoro on this computer: {ms} ms, {model.verdict(ms)}")


@unittest.skipIf(model is None, "numpy is not installed")
@unittest.skipUnless(shutil.which("espeak-ng"), "espeak-ng is not installed")
class NoModelTest(unittest.TestCase):
    """Kokoro chosen for Orca, model deleted: eSpeak NG speaks, never silence."""

    def test_speaks_with_espeak(self):
        sys.path.insert(0, os.path.dirname(__file__))
        import test_module
        work = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, work)
        empty = os.path.join(work, "empty")
        os.makedirs(empty)
        with open(os.path.join(work, "kokoro.conf"), "w", encoding="utf-8") as f:
            f.write("DefaultVoice it im_nicola\n")
        with open(os.path.join(work, "state.conf"), "w", encoding="utf-8") as f:
            f.write("engine=kokoro\n")
        saved = {k: os.environ.get(k) for k in ("VABAXOS_KOKORO_DIR", "XDG_DATA_HOME")}
        os.environ["XDG_DATA_HOME"] = empty
        test_module.DATA = empty
        try:
            sd = test_module.Session(work)
        finally:
            for key, value in saved.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
        try:
            sd.send("INIT")
            sd.wait_for("299 OK", timeout=30)
            sd.send("AUDIO", "audio_output_method=pulse", ".")
            sd.wait_for("203 OK AUDIO")
            sd.send("SET", "language=it", "rate=0", "voice=NULL", ".")
            sd.wait_for("203 OK SETTINGS")
            start = len(sd.lines)
            sd.send("SPEAK", "Nuova cartella pulsante", ".")
            sd.wait_for("701 BEGIN", start, timeout=30)
            sd.wait_for("702 END", start, timeout=30)
            self.assertGreater(os.path.getsize(sd.record), 1000, "eSpeak NG was heard")
        finally:
            sd.close()


CHILD = r'''
import importlib.machinery, importlib.util, sys, types
loader = importlib.machinery.SourceFileLoader("voiceprog", sys.argv[1])
spec = importlib.util.spec_from_loader("voiceprog", loader)
program = importlib.util.module_from_spec(spec)
loader.exec_module(program)
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk
from vabaxos_voice import model as real

state = {"installed": False, "speed": None}
fake = types.SimpleNamespace(
    TOTAL=real.TOTAL, verdict=real.verdict,
    installed=lambda: state["installed"], downloaded=lambda: state["installed"],
    load_speed=lambda: state["speed"],
    save_speed=lambda ms: state.update(speed={"ms": ms}),
    measure=lambda: 420,
    remove=lambda: state.update(installed=False, speed=None))

def install(progress, cancelled):
    for done in (100, 300, 600, 900, 1000):
        progress(done, 1000)
    state["installed"] = True
fake.install = install

class FakeOrca:
    on = False
    def get(self): return FakeOrca.on
    def set(self, on): FakeOrca.on = on

said = []
program.language = lambda: "en"
App, Window = program.window_classes(speak=said.append, model_module=fake, player=lambda: None,
                                     orca_class=FakeOrca)
app = Adw.Application(application_id="org.vabaxos.NaturalVoiceTest")

def check(app):
    window = Window(app)
    window.present()
    def step1():
        print("START:" + window.status.get_title() + " / " + window.speed.get_title(), flush=True)
        print("SENSITIVE:" + str(window.use.get_sensitive()), flush=True)
        window.download_or_remove()
        GLib.timeout_add(800, step2)
        return False
    def step2():
        print("DOWNLOAD:" + "|".join(said), flush=True)
        print("AFTER:" + window.status.get_title() + " / " + window.download_button.get_label(), flush=True)
        window.use.set_active(True)
        print("ORCA:" + str(FakeOrca.on) + " " + said[-1], flush=True)
        window.download_or_remove()
        print("DELETED:" + str(FakeOrca.on) + " " + said[-1] + " / " + window.download_button.get_label(), flush=True)
        app.quit()
        return False
    GLib.timeout_add(400, step1)

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


@unittest.skipIf(model is None, "numpy is not installed")
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
        self.assertEqual(out.get("START"), "Not downloaded: about 350 MB, from GitHub. / Speed not measured yet.", err)
        self.assertEqual(out.get("SENSITIVE"), "False", err)
        self.assertEqual(out.get("DOWNLOAD"),
                         "Downloading the natural voice: some minutes, depending on Internet.|25 percent.|50 percent."
                         "|75 percent.|Natural voice downloaded. Now I measure the speed of this computer.|"
                         "Measuring: about half a minute.|It answers in 0.42 seconds: a little late for the screen "
                         "reader; good for reading documents.", err)
        self.assertEqual(out.get("AFTER"), "Downloaded. / Delete", err)
        self.assertEqual(out.get("ORCA"), "True Orca speaks with the natural voice.", err)
        self.assertEqual(out.get("DELETED"), "False Natural voice deleted. Orca speaks with eSpeak NG. / Download", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
