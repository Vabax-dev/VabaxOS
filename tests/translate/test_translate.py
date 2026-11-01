#!/usr/bin/env python3
"""Tests for vabaxos-translate: how texts are cut, the request to the
model, the answer cleaned, the engine with a made-up llama-server kept
running between translations, and the window on Broadway.

    python3 tests/translate/test_translate.py
"""

import json
import os
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import time
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ROOT = os.path.join(REPO, "packages", "vabaxos-translate", "root")
LIB = os.path.join(ROOT, "usr", "lib", "python3", "dist-packages")
DESCRIBE = os.path.join(REPO, "packages", "vabaxos-describe", "root", "usr", "lib", "python3", "dist-packages")
PROGRAM = os.path.join(ROOT, "usr", "bin", "vabaxos-translate")
sys.path[:0] = [LIB, DESCRIBE]

import vabaxos_describe as vd  # noqa: E402
import vabaxos_translate as vt  # noqa: E402

FAKE_SERVER = r'''#!/usr/bin/env python3
import http.server, json, sys
args = sys.argv[1:]
port = int(args[args.index("--port") + 1])
log = sys.argv[0] + ".log"
class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def reply(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        self.reply(200 if self.path == "/health" else 404, {"status": "ok"})
    def do_POST(self):
        request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        with open(log, "a") as f:
            f.write(json.dumps(request) + "\n")
        text = request["messages"][1]["content"]
        self.reply(200, {"choices": [{"message": {"content": "Translation: «" + text.upper() + "»"}}]})
http.server.HTTPServer(("127.0.0.1", port), Handler).serve_forever()
'''


class TextTest(unittest.TestCase):

    def test_chunks(self):
        self.assertEqual(vt.chunks("Uno.\n\nDue.\n \nTre."), ["Uno.", "Due.", "Tre."])
        long = " ".join(f"Frase numero {i}." for i in range(200))
        parts = vt.chunks(long, 300)
        self.assertTrue(all(len(p) <= 300 for p in parts))
        self.assertEqual(" ".join(parts), long)

    def test_request(self):
        body = vt.request_body("Good morning", "it")
        system = body["messages"][0]["content"]
        self.assertIn("into Italian", system)
        self.assertIn("translate it into English instead", system)
        self.assertEqual(body["messages"][1], {"role": "user", "content": "Good morning"})
        self.assertIn("into Italian instead", vt.request_body("Hi", "en", "en")["messages"][0]["content"])

    def test_clean(self):
        self.assertEqual(vt.clean("Traduzione: «Buongiorno»"), "Buongiorno")
        self.assertEqual(vt.clean('  "Hello"  '), "Hello")
        self.assertEqual(vt.clean("Riga uno\nRiga due"), "Riga uno\nRiga due")


class EngineTest(unittest.TestCase):

    def test_with_a_made_up_server(self):
        with tempfile.TemporaryDirectory() as tmp:
            server = os.path.join(tmp, "llama-server")
            with open(server, "w") as f:
                f.write(FAKE_SERVER.replace("#!/usr/bin/env python3", "#!" + sys.executable, 1))
            os.chmod(server, os.stat(server).st_mode | stat.S_IXUSR)
            for name in (vd.MODEL, vd.PROJECTOR):
                open(os.path.join(tmp, name), "w").close()
            old = os.environ["PATH"]
            os.environ["PATH"] = f"{tmp}:{old}"
            engine = vt.Engine(tmp)
            try:
                self.assertTrue(engine.available(tmp))
                steps = []
                first = engine.translate("ciao.\n\nmondo.", "en", progress=lambda d, t: steps.append((d, t)))
                pid = engine.server.pid
                second = engine.translate("ancora", "en")
                self.assertEqual(engine.server.pid, pid, "the engine stays on between translations")
            finally:
                engine.stop()
                os.environ["PATH"] = old
            with open(server + ".log") as f:
                requests = [json.loads(line) for line in f]
        self.assertEqual(first, "CIAO.\n\nMONDO.")
        self.assertEqual(second, "ANCORA")
        self.assertEqual(steps, [(1, 2), (2, 2)])
        self.assertEqual(len(requests), 3)
        self.assertIsNone(engine.server)


CHILD = r'''
import importlib.machinery, importlib.util, sys
loader = importlib.machinery.SourceFileLoader("translateprog", sys.argv[1])
spec = importlib.util.spec_from_loader("translateprog", loader)
program = importlib.util.module_from_spec(spec)
loader.exec_module(program)
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk

said, opened, asked = [], [], []

class FakeEngine:
    have = False
    def __init__(self): self.stopped = False
    def available(self): return FakeEngine.have
    def translate(self, text, target, fallback, progress):
        asked.append((text, target, fallback))
        return "Good morning, world."
    def stop(self): self.stopped = True

App, Window = program.window_classes(speak=said.append, engine_class=FakeEngine,
                                     model_opener=lambda: opened.append(1))
app = Adw.Application(application_id="org.vabaxos.TranslateTest")

def walk(widget):
    child = widget.get_first_child()
    while child:
        yield child
        yield from walk(child)
        child = child.get_next_sibling()

def text_of(view):
    b = view.get_buffer()
    return b.get_text(b.get_start_iter(), b.get_end_iter(), False)

def check(app):
    window = Window(app)
    window.present()
    def step1():
        window.translate()
        print("EMPTY:" + said[-1], flush=True)
        window.source.get_buffer().set_text("Buongiorno, mondo.")
        window.translate()
        print("NOMODEL:" + said[-1] + " " + str(window.model_button.get_visible()), flush=True)
        window.model_button.emit("clicked")
        print("OPENED:" + str(opened), flush=True)
        FakeEngine.have = True
        window.target.set_selected(1)
        window.translate()
        GLib.timeout_add(300, step2)
        return False
    def step2():
        print("RESULT:" + text_of(window.result) + " | " + said[-1] + " | " + repr(asked[-1]), flush=True)
        print("FOCUS:" + str(window.result.has_focus()), flush=True)
        window.copy()
        print("COPY:" + said[-1], flush=True)
        window.close()
        print("STOPPED:" + str(window.engine.stopped), flush=True)
        app.quit()
        return False
    GLib.timeout_add(300, step1)

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
                   NO_AT_BRIDGE="1", PYTHONPATH=os.pathsep.join([LIB, DESCRIBE]), LANGUAGE="C", LANG="C.UTF-8",
                   PYTHONDONTWRITEBYTECODE="1")
        try:
            result = subprocess.run([sys.executable, "-c", CHILD, PROGRAM], env=env, capture_output=True, text=True,
                                    timeout=60, check=False)
        finally:
            broadway.terminate()
            broadway.wait()
        out = dict(line.split(":", 1) for line in result.stdout.splitlines() if ":" in line)
        err = result.stderr[-3000:]
        self.assertEqual(out.get("EMPTY"), "Write or paste a text first.", err)
        self.assertEqual(out.get("NOMODEL"), "The translation needs the model of the descriptions of pictures: "
                                             "Download the model. True", err)
        self.assertEqual(out.get("OPENED"), "[1]", err)
        self.assertEqual(out.get("RESULT"), "Good morning, world. | Good morning, world. | "
                                            "('Buongiorno, mondo.', 'en', 'it')", err)
        self.assertEqual(out.get("FOCUS"), "True", err)
        self.assertEqual(out.get("COPY"), "Translation copied.", err)
        self.assertEqual(out.get("STOPPED"), "True", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
