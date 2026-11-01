#!/usr/bin/env python3
"""Tests for the download of the vision model of vabaxos-describe: which
files are chosen, the checksum, the progress, cancel, and the window that
asks to download, with a made-up repository and a made-up download.

    python3 tests/describe/test_model.py
"""

import hashlib
import io
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LIB = os.path.join(REPO, "packages", "vabaxos-describe", "root", "usr", "lib", "python3", "dist-packages")
PROGRAM = os.path.join(REPO, "packages", "vabaxos-describe", "root", "usr", "bin", "vabaxos-describe")
sys.path.insert(0, LIB)

import vabaxos_describe as vd  # noqa: E402
from vabaxos_describe import model as vm  # noqa: E402

MODEL_BYTES = b"model" * 300000
PROJECTOR_BYTES = b"proj" * 100000


def entry(path, data):
    return {"type": "file", "path": path, "size": len(data),
            "lfs": {"oid": hashlib.sha256(data).hexdigest(), "size": len(data)}}


LISTING = [
    {"type": "file", "path": "README.md", "size": 10},
    entry("Qwen3.5-0.8B-Q4_K_M.gguf", b"small"),
    entry("Qwen3.5-0.8B-Q8_0.gguf", MODEL_BYTES),
    entry("Qwen3.5-0.8B-F16.gguf", b"big" * 10),
    entry("mmproj-Qwen3.5-0.8B-F16.gguf", PROJECTOR_BYTES),
    entry("mmproj-Qwen3.5-0.8B-BF16.gguf", b"x"),
]
CONTENT = {"Qwen3.5-0.8B-Q8_0.gguf": MODEL_BYTES, "mmproj-Qwen3.5-0.8B-F16.gguf": PROJECTOR_BYTES}


class Reply(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def opener(damaged=False):
    def open_url(url, timeout=None):
        if "/api/models/" in url:
            return Reply(json.dumps(LISTING).encode())
        name = url.rsplit("/", 1)[1]
        data = CONTENT[name]
        return Reply(data[:-1] + b"!" if damaged else data)
    return open_url


class ChooseTest(unittest.TestCase):

    def test_q8_and_its_projector(self):
        model, projector = vm.choose(LISTING)
        self.assertEqual(model["path"], "Qwen3.5-0.8B-Q8_0.gguf")
        self.assertEqual(projector["path"], "mmproj-Qwen3.5-0.8B-F16.gguf")
        self.assertEqual(vm.total_size([model, projector]), len(MODEL_BYTES) + len(PROJECTOR_BYTES))

    def test_no_projector(self):
        with self.assertRaises(vm.DownloadError):
            vm.choose([entry("a-Q8_0.gguf", b"x")])

    def test_checksum_needed(self):
        with self.assertRaises(vm.DownloadError):
            vm.expected_sha({"path": "a.gguf"})

    def test_size_text(self):
        self.assertEqual(vm.size_text(1_050_000_000), "1,1 GB")
        self.assertEqual(vm.size_text(600_000_000), "600 MB")


class InstallTest(unittest.TestCase):

    def test_install_with_progress(self):
        seen = []
        with tempfile.TemporaryDirectory() as tmp:
            folder = vm.install(progress=lambda done, total: seen.append((done, total)), folder=tmp,
                                opener=opener())
            self.assertTrue(vd.has_model(folder))
            self.assertEqual(open(os.path.join(folder, vd.MODEL), "rb").read(), MODEL_BYTES)
            vm.remove(folder)
            self.assertFalse(vd.has_model(folder))
        total = len(MODEL_BYTES) + len(PROJECTOR_BYTES)
        self.assertEqual(seen[-1], (total, total))
        self.assertTrue(all(a[0] <= b[0] for a, b in zip(seen, seen[1:])), "progress only goes forward")

    def test_damaged_download_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(vm.DownloadError, "damaged"):
                vm.install(folder=tmp, opener=opener(damaged=True))
            self.assertEqual(os.listdir(tmp), [], "nothing half written stays")

    def test_cancel(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(vm.DownloadError, "cancelled"):
                vm.install(folder=tmp, opener=opener(), cancelled=lambda: True)
            self.assertFalse(vd.has_model(tmp))


CHILD = r'''
import importlib.machinery, importlib.util, sys
loader = importlib.machinery.SourceFileLoader("describe_program", sys.argv[1])
spec = importlib.util.spec_from_loader("describe_program", loader)
program = importlib.util.module_from_spec(spec)
loader.exec_module(program)
from gi.repository import Adw, GLib, Gtk
program.vd.engine_installed = lambda: True
said, described = [], []
def installer(progress, cancelled):
    for done in (10, 30, 60, 100):
        progress(done, 100)
    folder = program.vd.user_dir()
    import os
    os.makedirs(folder, exist_ok=True)
    for name in (program.vd.MODEL, program.vd.PROJECTOR):
        open(os.path.join(folder, name), "w").close()
app = Adw.Application(application_id="org.vabaxos.DescribeTest")
def check(app):
    app.hold()  # the window closes itself after the download, as in real use
    window = program.ModelWindow(app, then=lambda: described.append(True), installer=installer, say=said.append)
    window.present()
    print("ASK:" + window.state.get_text()[:40], flush=True)
    print("BUTTONS:%s,%s" % (window.download_button.get_visible(), window.delete_button.get_visible()), flush=True)
    window.download()
    def later():
        print("SAID:" + "|".join(said), flush=True)
        print("THEN:%d" % len(described), flush=True)
        app.quit()
        return False
    GLib.timeout_add(800, later)
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

    def test_ask_download_then_describe(self):
        display = free_display()
        broadway = subprocess.Popen(["gtk4-broadwayd", f":{display}"], stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
        time.sleep(1)
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, GDK_BACKEND="broadway", BROADWAY_DISPLAY=f":{display}",
                       GSETTINGS_BACKEND="memory", NO_AT_BRIDGE="1", PYTHONPATH=LIB, XDG_DATA_HOME=tmp,
                       LANGUAGE="C", LANG="C.UTF-8", PYTHONDONTWRITEBYTECODE="1")
            env.pop("VABAXOS_DESCRIBE_DIR", None)
            try:
                result = subprocess.run([sys.executable, "-c", CHILD, PROGRAM], env=env, capture_output=True,
                                        text=True, timeout=60)
            finally:
                broadway.terminate()
                broadway.wait()
        out = dict(line.split(":", 1) for line in result.stdout.splitlines() if ":" in line)
        err = result.stderr[-2000:]
        self.assertEqual(out.get("ASK"), "To describe pictures without Internet, V", err)
        self.assertEqual(out.get("BUTTONS"), "True,False", err)
        said = out.get("SAID", "").split("|")
        self.assertEqual(said, ["Downloading the model. The progress is said every 25 percent.",
                                "Downloaded 25 percent.", "Downloaded 50 percent.", "The model is ready."], err)
        self.assertEqual(out.get("THEN"), "1", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
