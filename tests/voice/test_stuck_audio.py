#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Vabax and VabaxOS contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""sd_kokoro must always answer Speech Dispatcher, even when the sound
server stops taking audio (found in QEMU, 2026-09-26: after one message the
module hung, and Orca fell silent). No model needed: the synthesis and the
player are fakes, and the first player never returns.

    python3 tests/voice/test_stuck_audio.py
"""

import io
import os
import sys
import tempfile
import threading
import time
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO, "packages", "vabaxos-voice", "root", "usr", "lib", "python3", "dist-packages"))

try:
    import numpy as np
    from vabaxos_voice import module
except ImportError as error:  # numpy is in the CI job of the programs
    module = None
    MISSING = str(error)


class FakeKokoro:
    def run_options(self):
        return type("Options", (), {"terminate": False})()

    def synthesize(self, text, voice, lang, options=None):
        return np.zeros(2400, dtype=np.int16)

    def sonic(self, pcm, speed, pitch):
        return pcm

    def tokens(self, text, lang):
        return [1]


class FakeCache:
    def get(self, *args):
        return None

    def put(self, *args, **kwargs):
        pass


class StuckPlayer:
    """A sound server that takes the first piece and never returns."""

    def __init__(self):
        self.release = threading.Event()

    def play(self, pcm, cancelled):
        self.release.wait()
        return True

    def drain(self, cancelled):
        return True

    def close(self):
        pass


class QuickPlayer:
    def __init__(self, rate=24000):
        self.played = 0

    def play(self, pcm, cancelled):
        self.played += len(pcm)
        return True

    def drain(self, cancelled):
        return True

    def close(self):
        pass


@unittest.skipIf(module is None, "numpy is not installed" if module is None else "")
class StuckAudioTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = io.StringIO()
        self.module = module.Module(out=self.out, config=os.path.join(self.tmp.name, "none"),
                                    state=os.path.join(self.tmp.name, "none"))
        self.module.cache = FakeCache()
        self.module.kokoro = FakeKokoro()
        self.module.load = lambda: self.module.kokoro
        self.stuck = StuckPlayer()
        self.module.player = self.stuck
        self.quick = []
        self.saved = module.make_player
        module.make_player = lambda rate: self.quick.append(QuickPlayer()) or self.quick[-1]

    def tearDown(self):
        module.make_player = self.saved
        self.stuck.release.set()
        self.tmp.cleanup()

    def wait_for(self, text, seconds=5):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            if text in self.out.getvalue():
                return True
            time.sleep(0.02)
        return False

    def test_next_message_is_spoken(self):
        self.module.speak("prima frase")
        self.assertTrue(self.wait_for("701 BEGIN"), self.out.getvalue())
        start = time.monotonic()
        self.module.speak("seconda frase")
        self.assertLess(time.monotonic() - start, 3.5, "the module waited for the stuck message")
        self.assertTrue(self.wait_for("702 END"), self.out.getvalue())
        lines = self.out.getvalue().split()
        # The stuck message is reported as stopped, then the second one
        # begins and ends on a new player.
        self.assertEqual(self.out.getvalue().count("703 STOP"), 1, self.out.getvalue())
        self.assertEqual(self.out.getvalue().count("701 BEGIN"), 2, self.out.getvalue())
        self.assertTrue(self.quick and self.quick[-1].played > 0)
        self.assertIn("END", lines)

    def test_left_behind_message_stays_quiet(self):
        self.module.speak("prima frase")
        self.assertTrue(self.wait_for("701 BEGIN"))
        self.module.speak("seconda frase")
        self.assertTrue(self.wait_for("702 END"))
        before = self.out.getvalue()
        self.stuck.release.set()  # the old message comes back to life
        time.sleep(0.5)
        self.assertEqual(self.out.getvalue(), before, "the old message wrote to Speech Dispatcher")


if __name__ == "__main__":
    unittest.main(verbosity=2)
