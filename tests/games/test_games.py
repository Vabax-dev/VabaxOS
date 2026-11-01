#!/usr/bin/env python3
"""Tests for vabaxos-games: the rules of the three games, the sounds, and
a game of each in the window on Broadway (made-up voice and player).

    python3 tests/games/test_games.py
"""

import io
import os
import random
import shutil
import socket
import subprocess
import sys
import time
import unittest
import wave

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ROOT = os.path.join(REPO, "packages", "vabaxos-games", "root")
LIB = os.path.join(ROOT, "usr", "lib", "python3", "dist-packages")
PROGRAM = os.path.join(ROOT, "usr", "bin", "vabaxos-games")
sys.path.insert(0, LIB)

import vabaxos_games as vg  # noqa: E402


class RulesTest(unittest.TestCase):

    def test_guess(self):
        game = vg.Guess(random.Random(3))
        target = game.number
        self.assertEqual(game.guess(target - 1) if target > 1 else "higher", "higher")
        self.assertEqual(game.guess(target), "right")

    def test_simon(self):
        game = vg.Simon(random.Random(5))
        first = game.next_round()
        self.assertEqual(len(first), 1)
        self.assertEqual(game.press(first[0]), "round")
        self.assertEqual(game.press(first[0]), "wait", "keys between rounds are ignored")
        second = game.next_round()
        self.assertEqual(second[0], first[0], "the sequence grows, it does not change")
        self.assertEqual(game.press(second[0]), "ok")
        wrong = 1 if second[1] != 1 else 2
        self.assertEqual(game.press(wrong), "wrong")
        self.assertEqual(game.score(), 1)

    def test_tris_computer_wins_and_blocks(self):
        game = vg.TicTacToe(random.Random(0))
        game.cells = ["O", "O", "", "X", "X", "", "", "", ""]
        self.assertEqual(game.computer(), 2, "wins first")
        game.cells = ["X", "X", "", "", "O", "", "", "", ""]
        self.assertEqual(game.computer(), 2, "blocks")
        self.assertEqual(vg.KEY_TO_CELL[7], 0)
        self.assertEqual(vg.KEY_TO_CELL[3], 8)

    def test_tris_never_loses(self):
        for seed in range(30):
            rng = random.Random(seed)
            game = vg.TicTacToe(random.Random(seed))
            while not game.winner():
                game.place(rng.choice(game.free()))
                if not game.winner():
                    game.computer()
            self.assertNotEqual(game.winner(), "X", seed)

    def test_sounds(self):
        with wave.open(io.BytesIO(vg.tone(523))) as f:
            self.assertEqual((f.getframerate(), f.getnchannels()), (vg.RATE, 1))
        with wave.open(io.BytesIO(vg.chord([523, 659]))) as f:
            self.assertGreater(f.getnframes(), vg.RATE // 3)


CHILD = r'''
import importlib.machinery, importlib.util, sys
loader = importlib.machinery.SourceFileLoader("gamesprog", sys.argv[1])
spec = importlib.util.spec_from_loader("gamesprog", loader)
program = importlib.util.module_from_spec(spec)
loader.exec_module(program)
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw
said, played = [], []
App, Window = program.window_classes(speak=said.append, player=played.append)
app = Adw.Application(application_id="org.vabaxos.GamesTest")
def check(app):
    window = Window(app)
    window.present()
    window.start("guess")
    window.number.number = 42
    for text in ("50", "abc", "42"):
        window.entry.set_text(text)
        window.guess()
    print("GUESS:" + "|".join(said[1:]), flush=True)
    window.start("tris")
    window.tris.rng.seed(1)
    window.tris_move(5)
    print("TRIS:" + said[-1], flush=True)
    window.tris_move(5)
    print("TAKEN:" + said[-1], flush=True)
    window.start("simon")
    window.simon_round()
    first = window.simon.sequence[0]
    window.simon_press(first)
    window.simon_press(first)
    window.simon_round()
    window.simon_press(1 if first != 1 else 2)
    print("SIMON:" + said[-1], flush=True)
    app.quit()
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

    def test_play(self):
        display = free_display()
        broadway = subprocess.Popen(["gtk4-broadwayd", f":{display}"], stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
        time.sleep(1)
        env = dict(os.environ, GDK_BACKEND="broadway", BROADWAY_DISPLAY=f":{display}", GSETTINGS_BACKEND="memory",
                   NO_AT_BRIDGE="1", PYTHONPATH=LIB, LANGUAGE="C", LANG="C.UTF-8", PYTHONDONTWRITEBYTECODE="1")
        try:
            result = subprocess.run([sys.executable, "-c", CHILD, PROGRAM], env=env, capture_output=True, text=True,
                                    timeout=60)
        finally:
            broadway.terminate()
            broadway.wait()
        out = dict(line.split(":", 1) for line in result.stdout.splitlines() if ":" in line)
        err = result.stderr[-2000:]
        self.assertEqual(out.get("GUESS"), "50: lower.|Write a number from 1 to 100.|Right, it is 42! 2 tries. "
                                           "Write a number to play again.", err)
        self.assertTrue(out.get("TRIS", "").startswith("X centre. O "), err)
        self.assertEqual(out.get("TAKEN"), "Taken: centre.", err)
        self.assertEqual(out.get("SIMON"), "Wrong. You remembered 1 note. Enter plays again.", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
