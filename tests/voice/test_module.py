#!/usr/bin/env python3
"""Tests for sd_kokoro, the Speech Dispatcher module (ADR-0019).

The module runs as Speech Dispatcher would run it, but its audio goes to a
file (VABAXOS_VOICE_RECORD), so nothing is heard. Needs the Kokoro model:
VABAXOS_KOKORO_DIR must point to a folder with kokoro-v1.0.onnx,
voices-v1.0.bin and vocab.json; otherwise the tests are skipped.

    VABAXOS_KOKORO_DIR=/path/to/kokoro python3 tests/voice/test_module.py
"""

import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ROOT = os.path.join(REPO, "packages", "vabaxos-voice", "root")
MODULE = os.path.join(ROOT, "usr", "lib", "speech-dispatcher-modules", "sd_kokoro")
DATA = os.environ.get("VABAXOS_KOKORO_DIR", "")


class Session:
    """sd_kokoro with a line reader running in the background."""

    def __init__(self, workdir):
        self.record = os.path.join(workdir, "audio.raw")
        env = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "usr", "lib", "python3", "dist-packages"),
                   VABAXOS_VOICE_RECORD=self.record, XDG_CACHE_HOME=os.path.join(workdir, "cache"),
                   VABAXOS_KOKORO_DIR=DATA, VABAXOS_VOICE_STATE=os.path.join(workdir, "state.conf"))
        self.proc = subprocess.Popen([sys.executable, MODULE, os.path.join(workdir, "kokoro.conf")],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                     text=True, bufsize=1, env=env)
        self.lines = []
        self.cond = threading.Condition()
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for line in self.proc.stdout:
            with self.cond:
                self.lines.append((time.monotonic(), line.rstrip("\n")))
                self.cond.notify_all()

    def send(self, *lines):
        for line in lines:
            self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()
        return time.monotonic()

    def wait_for(self, text, since=0, timeout=30):
        deadline = time.monotonic() + timeout
        with self.cond:
            while True:
                for i, (t, line) in enumerate(self.lines):
                    if i >= since and line.startswith(text):
                        return i, t
                left = deadline - time.monotonic()
                if left <= 0:
                    raise AssertionError(f"no {text!r} in {self.lines[since:]}")
                self.cond.wait(left)

    def close(self):
        try:
            self.send("QUIT")
            self.proc.wait(10)
        except (BrokenPipeError, subprocess.TimeoutExpired):
            self.proc.kill()


@unittest.skipUnless(DATA and os.path.exists(os.path.join(DATA, "kokoro-v1.0.onnx")), "Kokoro model not found")
class ModuleTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        with open(os.path.join(cls.tmp.name, "kokoro.conf"), "w", encoding="utf-8") as f:
            f.write("DefaultVoice it im_nicola\n")
        with open(os.path.join(cls.tmp.name, "state.conf"), "w", encoding="utf-8") as f:
            f.write("engine=espeak\n")  # as on a slow computer: no model at start
        cls.sd = Session(cls.tmp.name)
        sent = cls.sd.send("INIT")
        _, loaded = cls.sd.wait_for("299 OK LOADED SUCCESSFULLY", timeout=60)
        cls.init_time = loaded - sent
        cls.sd.send("AUDIO", "audio_output_method=pulse", ".")
        cls.sd.wait_for("203 OK AUDIO INITIALIZED")
        cls.sd.send("SET", "language=it", "rate=0", "voice=NULL", ".")
        cls.sd.wait_for("203 OK SETTINGS RECEIVED")

    @classmethod
    def tearDownClass(cls):
        cls.sd.close()
        cls.tmp.cleanup()

    def speak(self, text, command="SPEAK"):
        start = len(self.sd.lines)
        self.sd.send(command, text, ".")
        _, spoken = self.sd.wait_for("200 OK SPEAKING", start)
        _, begin = self.sd.wait_for("701 BEGIN", start)
        return start, begin - spoken

    def test_0_init_is_quick(self):
        # Speech Dispatcher starts every module, also where eSpeak NG was
        # chosen: there the model must not be loaded at start.
        print(f"\n  INIT in {self.init_time * 1000:.0f} ms")
        self.assertLess(self.init_time, 1.0)

    def test_1_speaks_and_ends(self):
        size = os.path.getsize(self.sd.record) if os.path.exists(self.sd.record) else 0
        start, delay = self.speak("<speak>Impostazioni, pulsante</speak>")
        self.sd.wait_for("702 END", start)
        self.assertGreater(os.path.getsize(self.sd.record) - size, 24000 * 2 * 0.5)
        print(f"\n  first words after {delay * 1000:.0f} ms (new phrase)")

    def test_2_cache_is_faster(self):
        start, first = self.speak("<speak>Casella di controllo, non selezionata</speak>")
        self.sd.wait_for("702 END", start)
        start, again = self.speak("<speak>Casella di controllo, non selezionata</speak>")
        self.sd.wait_for("702 END", start)
        print(f"\n  new phrase {first * 1000:.0f} ms, from the cache {again * 1000:.0f} ms")
        self.assertLess(again, 0.1)

    def test_3_marks_are_reported(self):
        start, _ = self.speak('<speak>Primo paragrafo.<mark name="m1"/> Secondo paragrafo.</speak>')
        i, _ = self.sd.wait_for("700-m1", start)
        self.sd.wait_for("702 END", i)

    def test_4_stop_is_quick(self):
        start, _ = self.speak("<speak>Questa è una frase lunga, che non deve arrivare alla fine, "
                              "perché la fermo subito dopo l'inizio, come quando si preme un tasto.</speak>")
        time.sleep(0.3)
        sent = self.sd.send("STOP")
        _, stopped = self.sd.wait_for("703 STOP", start)
        print(f"\n  stopped after {(stopped - sent) * 1000:.0f} ms")
        self.assertLess(stopped - sent, 0.5)

    def test_5_char_and_key(self):
        start, _ = self.speak("a", "CHAR")
        self.sd.wait_for("702 END", start)
        start, _ = self.speak("shift_a", "KEY")
        self.sd.wait_for("702 END", start)

    def test_6_voices_listed(self):
        start = len(self.sd.lines)
        self.sd.send("LIST VOICES")
        self.sd.wait_for("200 OK VOICE LIST SENT", start)
        names = [line for _, line in self.sd.lines[start:]]
        self.assertIn("200-im_nicola\tit\tnone", names)
        self.assertIn("200-if_sara\tit\tnone", names)


if __name__ == "__main__":
    unittest.main(verbosity=2)
