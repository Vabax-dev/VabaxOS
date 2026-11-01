#!/usr/bin/env python3
"""Tests for vabaxos-math: the calculator, formulas in words (LaTeX,
MathML, plain writing, Italian and English), and the window on Broadway.

    python3 tests/math/test_math.py
"""

import os
import shutil
import socket
import subprocess
import sys
import time
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ROOT = os.path.join(REPO, "packages", "vabaxos-math", "root")
LIB = os.path.join(ROOT, "usr", "lib", "python3", "dist-packages")
PROGRAM = os.path.join(ROOT, "usr", "bin", "vabaxos-calc")
sys.path.insert(0, LIB)

from vabaxos_math import calc, speech  # noqa: E402


class CalcTest(unittest.TestCase):

    def value(self, text):
        return calc.format_number(calc.evaluate(text))

    def test_as_written_on_paper(self):
        cases = {"3+4*2": "11", "3 + 4 × 2": "11", "2,5 * 4": "10", "2^10": "1024", "radice di 2": "1,414213562",
                 "sqrt 16": "4", "20% di 150": "30", "sin(30)": "0,5", "(1+2)/3": "1", "2(3+1)": "8",
                 "10 x 3": "30", "7:2": "3,5", "-3 + 1": "-2", "pi * 2": "6,283185307", "log(1000)": "3"}
        for text, result in cases.items():
            self.assertEqual(self.value(text), result, text)

    def test_refused(self):
        for text in ("1/0", "__import__('os')", "open('x')", "2**99999", "", "3 +", "radice(-1)"):
            with self.assertRaises(calc.CalcError, msg=text):
                calc.evaluate(text)

    def test_english_decimal_point(self):
        self.assertEqual(calc.format_number(2.5, "."), "2.5")
        self.assertEqual(calc.format_number(1e20), "1 × 10^20")


class SpeechTest(unittest.TestCase):

    def test_latex_in_italian(self):
        cases = {
            r"\frac{a+b}{2}": "frazione: a più b, fratto 2, fine frazione",
            r"\frac{1}{2}": "1 fratto 2",
            "x^2 + y_1": "x al quadrato più y con indice 1",
            r"\sqrt[3]{8}": "radice cubica di 8",
            r"\sqrt{x}": "radice quadrata di x",
            r"\sum_{i=1}^{n} i": "sommatoria per i uguale a 1 fino a n di i",
            r"\int_0^1 x^2 dx": "integrale da 0 a 1 di x al quadrato d x",
            r"\alpha \le \beta": "alfa minore o uguale a beta",
            "$x^{n+1}$": "x elevato a n più 1, fine esponente",
            "sqrt(x) + 3.5": "radice quadrata di x più 3,5",
        }
        for formula, words in cases.items():
            self.assertEqual(speech.say(formula, "it"), words, formula)

    def test_limit(self):
        self.assertTrue(speech.say(r"\lim_{x \to 0} \frac{\sin x}{x} = 1", "it").startswith(
            "limite per x che tende a 0 di"))

    def test_english(self):
        self.assertEqual(speech.say(r"\frac{a+b}{2}", "en"), "fraction: a plus b, over 2, end fraction")
        self.assertEqual(speech.say("x^2", "en"), "x squared")

    def test_mathml(self):
        self.assertEqual(speech.say("<math><mfrac><mi>a</mi><mn>2</mn></mfrac><mo>+</mo><msqrt><mi>x</mi></msqrt>"
                                    "</math>", "it"), "a fratto 2 più radice quadrata di x")
        self.assertEqual(speech.say('<math xmlns="http://www.w3.org/1998/Math/MathML"><msup><mi>x</mi><mn>2</mn>'
                                    '</msup><mo>=</mo><mn>4</mn></math>', "it"), "x al quadrato uguale a 4")

    def test_command_line(self):
        env = dict(os.environ, PYTHONPATH=LIB, LANGUAGE="it", LANG="it_IT.UTF-8", DBUS_SESSION_BUS_ADDRESS="")
        out = subprocess.run([sys.executable, PROGRAM, "--say", r"\frac{1}{2}"], env=env, capture_output=True,
                             text=True, timeout=30).stdout
        self.assertEqual(out.strip(), "1 fratto 2")


CHILD = r'''
import importlib.machinery, importlib.util, sys
loader = importlib.machinery.SourceFileLoader("calcprog", sys.argv[1])
spec = importlib.util.spec_from_loader("calcprog", loader)
program = importlib.util.module_from_spec(spec)
loader.exec_module(program)
from gi.repository import Adw
said = []
App, Window = program.window_classes(speak=said.append)
app = Adw.Application(application_id="org.vabaxos.CalcTest")
def check(app):
    window = Window(app)
    window.present()
    for text in ("3+4*2", "boh", "2^10"):
        window.entry.set_text(text)
        window.calculate()
    print("SAID:" + "|".join(said), flush=True)
    print("ROWS:" + "|".join(r.get_title() for r in window.rows), flush=True)
    print("ENTRY:" + window.entry.get_text(), flush=True)
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

    def test_window(self):
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
        self.assertEqual(out.get("SAID"), "3+4*2 is 11|I cannot calculate this. Write for example 3+4*2.|"
                                          "2^10 is 1024", err)
        self.assertEqual(out.get("ROWS"), "2^10 = 1024|3+4*2 = 11", err)
        self.assertEqual(out.get("ENTRY"), "1024", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
