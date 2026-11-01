#!/usr/bin/env python3
"""Tests for vabaxos-camera: the guidance from made-up camera pictures
(a sheet of text drawn in different places, sizes and light, read by the
real tesseract), the sides said as the user sees them, and the window on
Broadway with a made-up webcam.

    python3 tests/camera/test_camera.py
"""

import os
import shutil
import socket
import subprocess
import sys
import time
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ROOT = os.path.join(REPO, "packages", "vabaxos-camera", "root")
LIB = os.path.join(ROOT, "usr", "lib", "python3", "dist-packages")
PROGRAM = os.path.join(ROOT, "usr", "bin", "vabaxos-camera")
sys.path.insert(0, LIB)

import vabaxos_camera as vc  # noqa: E402

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
TEXT = ["Gentile cliente, la bolletta", "di ottobre è di 54 euro.", "La scadenza del pagamento",
        "è il 30 novembre 2026.", "Grazie per la fiducia."]


def frame(x, y, size, light=200, width=640, height=480):
    """A camera picture: a grey room, a sheet of paper with five lines."""
    from PIL import Image, ImageDraw, ImageFont
    image = Image.new("RGB", (width, height), (light // 3,) * 3)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(FONT, size)
    draw.rectangle([x, y, x + size * 16, y + int(size * 1.6 * len(TEXT) + size * 2)], fill=(light, light, light - 10))
    for i, line in enumerate(TEXT):
        draw.text((x + size, y + size + i * size * 1.6), line, fill=(20, 20, 20), font=font)
    return image


class SidesTest(unittest.TestCase):

    def words(self, *boxes):
        return [vc.Word("parola", left, top, w, h, 90) for left, top, w, h in boxes]

    def test_cut_sides_as_the_user_sees_them(self):
        words = self.words((0, 100, 80, 20), (2, 140, 90, 20), (200, 100, 80, 20), (200, 140, 80, 20),
                           (300, 100, 80, 20), (300, 140, 80, 20))
        facing = vc.analyze(words, 640, 480, facing_user=True)
        self.assertEqual((facing.kind, facing.sides), ("cut", ("left",)))
        self.assertEqual(facing.sentence, "The text goes out on the right: move the paper a little to the left.")
        table = vc.analyze(words, 640, 480, facing_user=False)
        self.assertEqual(table.sentence, "The text goes out on the left: move the paper a little to the right.")

    def test_top_and_bottom_are_not_mirrored(self):
        words = self.words((100, 470, 80, 9), (200, 471, 80, 9), (300, 200, 80, 20), (100, 200, 80, 20))
        self.assertEqual(vc.analyze(words, 640, 480).sentence,
                         "The text goes out at the bottom: move the paper a little up.")

    def test_words_from_tsv(self):
        tsv = ("level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n"
               "5\t1\t1\t1\t1\t1\t10\t20\t50\t15\t91.5\tBolletta\n"
               "5\t1\t1\t1\t1\t2\t70\t20\t9\t15\t95.0\te\n"
               "5\t1\t1\t1\t1\t3\t90\t20\t9\t15\t30.0\tlucE\n"
               "5\t1\t1\t1\t1\t4\t90\t20\t9\t15\t90.0\t--\n")
        self.assertEqual([w.text for w in vc.words_from_tsv(tsv)], ["Bolletta"])


@unittest.skipUnless(shutil.which("tesseract") and os.path.exists(FONT), "tesseract or DejaVu missing")
class PicturesTest(unittest.TestCase):

    def kind(self, image, facing=True):
        return vc.guide(image, facing).kind

    def test_guidance(self):
        self.assertEqual(self.kind(frame(60, 80, 22)), "ready")
        self.assertEqual(self.kind(frame(10, 10, 30)), "ready")
        self.assertEqual(vc.guide(frame(-150, 80, 22)).sides, ("left",))
        self.assertEqual(vc.guide(frame(400, 80, 22)).sides, ("right",))
        self.assertEqual(vc.guide(frame(60, -60, 22)).sides[0], "top")
        self.assertEqual(self.kind(frame(200, 180, 8)), "far")
        self.assertEqual(self.kind(frame(-60, -40, 60)), "near")
        self.assertEqual(self.kind(frame(60, 80, 22, light=40)), "dark")
        from PIL import Image
        self.assertEqual(self.kind(Image.new("RGB", (640, 480), (120, 120, 120))), "empty")


CHILD = r'''
import importlib.machinery, importlib.util, sys
loader = importlib.machinery.SourceFileLoader("camprog", sys.argv[1])
spec = importlib.util.spec_from_loader("camprog", loader)
program = importlib.util.module_from_spec(spec)
loader.exec_module(program)
program.INTERVAL_MS = 100
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk
from PIL import Image
import vabaxos_camera as vc

said, opened = [], []
plan = [vc.Guidance("cut", "The text goes out on the right: move the paper a little to the left."),
        vc.Guidance("ready", "Still like this."), vc.Guidance("ready", "Still like this.")]

class FakeCamera:
    def start(self): pass
    def frame(self): return Image.new("RGB", (64, 48), (200, 200, 200))
    def stop(self): pass

def guide(frame, facing):
    return plan.pop(0) if plan else vc.Guidance("ready", "Still like this.")

def no_camera():
    raise RuntimeError("no camera")

App, Window = program.window_classes(speak=said.append, camera_factory=FakeCamera, guide=guide,
                                     opener=lambda program_, path: (opened.append((program_, path.endswith(".png"))),
                                                                    __import__("os").remove(path)),
                                     which=lambda name: "/usr/bin/" + name)
app = Adw.Application(application_id="org.vabaxos.CameraTest")

def check(app):
    window = Window(app)
    window.present()
    def step1():
        print("SAID:" + "|".join(said), flush=True)
        print("OPENED:" + repr(opened), flush=True)
        print("AGAIN:" + str(window.again_button.get_visible()), flush=True)
        window.resume()
        window.take("describe")
        print("DESCRIBE:" + repr(opened[-1]) + " " + said[-1], flush=True)
        window.close()
        App2, Window2 = program.window_classes(speak=said.append, camera_factory=no_camera, guide=guide,
                                               opener=lambda *a: None, which=lambda name: None)
        empty = Window2(app)
        empty.present()
        GLib.timeout_add(300, lambda: step2(empty))
        return False
    def step2(empty):
        print("NOCAMERA:" + said[-1] + " " + str(empty.take_button.get_sensitive()) + " "
              + str(empty.describe_button.get_visible()), flush=True)
        app.quit()
        return False
    GLib.timeout_add(1500, step1)

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
        self.assertEqual(out.get("SAID"), "Camera on. Hold the paper in front of it.|The text goes out on the right: "
                                          "move the paper a little to the left.|Still like this.|Picture taken: "
                                          "reading the text.", err)
        self.assertEqual(out.get("OPENED"), "[('vabaxos-ocr', True)]", err)
        self.assertEqual(out.get("AGAIN"), "True", err)
        self.assertEqual(out.get("DESCRIBE"), "('vabaxos-describe', True) Picture taken: describing it.", err)
        self.assertEqual(out.get("NOCAMERA"), "No camera found: connect a webcam, then open this program again. "
                                              "False False", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
