#!/usr/bin/env python3
"""Tests for vabaxos-ocr, the text recognition of the screen reader.

Pictures like a screen are drawn here (small letters, light and dark
backgrounds, a dark title bar) and recognized with tesseract; the window
runs on a hidden Broadway display.

    python3 tests/ocr/test_ocr.py
"""

import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ROOT = os.path.join(REPO, "packages", "vabaxos-ocr", "root")
LIB = os.path.join(ROOT, "usr", "lib", "python3", "dist-packages")
PROGRAM = os.path.join(ROOT, "usr", "bin", "vabaxos-ocr")
sys.path.insert(0, LIB)

from vabaxos_ocr import recognize  # noqa: E402

FONTS = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"]
FONT = next((f for f in FONTS if os.path.exists(f)), None)
LINES = ["Nome della connessione: Casa", "Indirizzo IP: 192.168.1.20", "Salva le modifiche", "Annulla"]


def have_pil():
    try:
        import PIL  # noqa: F401
        return True
    except ImportError:
        return False


def draw(path, dark, size=10):
    """A small settings window: a title bar and four lines."""
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.truetype(FONT, size)
    background, ink = ((36, 36, 36), (230, 230, 230)) if dark else ((250, 250, 250), (30, 30, 30))
    image = Image.new("RGB", (420, 160), background)
    pen = ImageDraw.Draw(image)
    pen.rectangle((0, 0, 420, 28), fill=(20, 20, 20) if dark else (60, 60, 70))
    pen.text((10, 7), "Impostazioni di rete", font=font, fill=(255, 255, 255))
    for i, text in enumerate(LINES):
        pen.text((14, 40 + i * 26), text, font=font, fill=ink)
    image.save(path)


TSV = "\n".join([
    "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext",
    "1\t1\t0\t0\t0\t0\t0\t0\t100\t100\t-1\t",
    "5\t1\t1\t1\t1\t1\t0\t0\t10\t10\t96\tSalva",
    "5\t1\t1\t1\t1\t2\t0\t0\t10\t10\t91\tle",
    "5\t1\t1\t1\t1\t3\t0\t0\t10\t10\t90\tmodifiche",
    "5\t1\t1\t1\t2\t1\t0\t0\t10\t10\t12\t@@",
    "5\t1\t2\t1\t1\t1\t0\t0\t10\t10\t88\tAnnulla",
    "5\t1\t2\t1\t1\t2\t0\t0\t10\t10\t95\t ",
])


class ParseTest(unittest.TestCase):

    def test_lines_in_order_with_blocks_apart(self):
        self.assertEqual(recognize.lines_from_tsv(TSV), ["Salva le modifiche", "", "Annulla"])

    def test_unsure_words_left_out(self):
        self.assertNotIn("@@", " ".join(recognize.lines_from_tsv(TSV)))
        self.assertIn("@@", " ".join(recognize.lines_from_tsv(TSV, min_confidence=0)))

    def test_empty(self):
        self.assertEqual(recognize.lines_from_tsv(""), [])

    def test_languages_follow_the_user(self):
        self.assertTrue(recognize.LANGUAGES["it"].startswith("ita"))
        self.assertTrue(recognize.LANGUAGES["en"].startswith("eng"))


@unittest.skipUnless(have_pil() and FONT, "python3-pil or a DejaVu/Liberation font is missing")
class PrepareTest(unittest.TestCase):

    def test_dark_background_is_inverted_and_enlarged(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as tmp:
            for dark in (False, True):
                source, ready = os.path.join(tmp, "a.png"), os.path.join(tmp, "b.png")
                draw(source, dark)
                self.assertEqual(recognize.prepare(source, ready), dark)
                with Image.open(ready) as image:
                    self.assertEqual(image.size, (420 * recognize.SCALE, 160 * recognize.SCALE))
                    self.assertEqual(image.mode, "L")


@unittest.skipUnless(have_pil() and FONT and shutil.which("tesseract")
                     and "ita" in recognize.installed_languages(), "tesseract with Italian is missing")
class RecognizeTest(unittest.TestCase):

    def check(self, dark):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "screen.png")
            draw(path, dark)
            text = "\n".join(recognize.recognize(path, "it"))
        for line in LINES + ["Impostazioni di rete"]:
            self.assertIn(line, text)

    def test_light_window(self):
        self.check(False)

    def test_dark_window(self):
        self.check(True)


CHILD = r'''
import importlib.machinery, importlib.util, sys
loader = importlib.machinery.SourceFileLoader("ocr", sys.argv[1])
spec = importlib.util.spec_from_loader("ocr", loader)
ocr = importlib.util.module_from_spec(spec)
loader.exec_module(ocr)
from gi.repository import Adw, GLib, Gtk

def walk(widget):
    yield widget
    child = widget.get_first_child()
    while child is not None:
        yield from walk(child)
        child = child.get_next_sibling()

app = Adw.Application(application_id="org.vabaxos.OcrTest")
def check(app):
    window = ocr.ResultWindow(app, "Impostazioni", ["Salva le modifiche", "", "Annulla"])
    window.present()
    def report():
        print("TITLE:" + window.get_title(), flush=True)
        print("FOCUS:" + type(window.get_focus()).__name__, flush=True)
        print("TEXT:" + window.text().replace("\n", "|"), flush=True)
        unnamed = [type(w).__name__ for w in walk(window) if isinstance(w, Gtk.Button) and w.get_mapped()
                   and not w.get_label() and not w.get_tooltip_text()
                   and not w.get_ancestor(Gtk.WindowControls)]
        print("UNNAMED:" + ",".join(unnamed), flush=True)
        app.quit()
        return False
    GLib.timeout_add(500, report)
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

    def test_window_has_the_text_and_the_focus(self):
        display = free_display()
        broadway = subprocess.Popen(["gtk4-broadwayd", f":{display}"], stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
        time.sleep(1)
        try:
            env = dict(os.environ, GDK_BACKEND="broadway", BROADWAY_DISPLAY=f":{display}",
                       GSETTINGS_BACKEND="memory", NO_AT_BRIDGE="1", PYTHONPATH=LIB,
                       LANGUAGE="C", LANG="C.UTF-8", PYTHONDONTWRITEBYTECODE="1")
            result = subprocess.run([sys.executable, "-c", CHILD, PROGRAM], env=env,
                                    capture_output=True, text=True, timeout=60)
        finally:
            broadway.terminate()
            broadway.wait()
        out = dict(line.split(":", 1) for line in result.stdout.splitlines() if ":" in line)
        self.assertEqual(out.get("TITLE"), "Recognized text, 2 lines: Impostazioni", result.stderr[-2000:])
        self.assertEqual(out.get("FOCUS"), "TextView", result.stderr[-2000:])
        self.assertEqual(out.get("TEXT"), "Salva le modifiche||Annulla")
        self.assertEqual(out.get("UNNAMED"), "")


class ProgramTest(unittest.TestCase):

    def test_arguments(self):
        import importlib.machinery
        import importlib.util
        loader = importlib.machinery.SourceFileLoader("vabaxos_ocr_program", PROGRAM)
        spec = importlib.util.spec_from_loader("vabaxos_ocr_program", loader)
        try:
            program = importlib.util.module_from_spec(spec)
            loader.exec_module(program)
        except (ImportError, ValueError) as error:
            self.skipTest(f"GTK 4 is missing: {error}")
        self.assertEqual(program.parse(["--title", "Posta", "/tmp/a.png"]), ("Posta", False, "/tmp/a.png"))
        self.assertEqual(program.parse(["--keep", "/tmp/a.png"]), ("", True, "/tmp/a.png"))
        self.assertEqual(program.window_title("", 1), "Recognized text, 1 line")


if __name__ == "__main__":
    unittest.main(verbosity=2)
