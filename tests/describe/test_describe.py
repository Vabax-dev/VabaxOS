#!/usr/bin/env python3
"""Tests for vabaxos-describe (ADR-0029, proposed): the request to
llama.cpp, the answer, and a whole description with a made-up
llama-server that answers like the real one.

    python3 tests/describe/test_describe.py
"""

import base64
import json
import os
import stat
import sys
import tempfile
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LIB = os.path.join(REPO, "packages", "vabaxos-describe", "root", "usr", "lib", "python3", "dist-packages")
sys.path.insert(0, LIB)

import vabaxos_describe as vd  # noqa: E402

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
        with open(log, "w") as f:
            json.dump({"args": args, "request": request}, f)
        self.reply(200, {"choices": [{"message": {"content": " Un gatto rosso dorme   su un divano blu. "}}]})
http.server.HTTPServer(("127.0.0.1", port), Handler).serve_forever()
'''


class RequestTest(unittest.TestCase):

    def test_body_has_prompt_and_picture(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "a.png")
            with open(path, "wb") as f:
                f.write(b"\x89PNG fake")
            body = vd.request_body(path, "it_IT")
        content = body["messages"][0]["content"]
        self.assertTrue(content[0]["text"].startswith("Descrivi questa immagine"))
        url = content[1]["image_url"]["url"]
        self.assertTrue(url.startswith("data:image/png;base64,"))
        self.assertEqual(base64.b64decode(url.split(",", 1)[1]), b"\x89PNG fake")
        self.assertIn("in English", vd.prompt("fr"))

    def test_answer(self):
        self.assertEqual(vd.answer_text({"choices": [{"message": {"content": " a  b\nc "}}]}), "a b c")
        self.assertEqual(vd.answer_text({"choices": [{"message": {"content": [{"type": "text", "text": "x"}]}}]}),
                         "x")
        self.assertEqual(vd.answer_text({}), "")

    def test_server_command(self):
        command = vd.server_command(8123, "/m", threads=3)
        self.assertEqual(command[:5], ["llama-server", "-m", "/m/model.gguf", "--mmproj", "/m/mmproj.gguf"])
        self.assertIn("127.0.0.1", command)


class DescribeTest(unittest.TestCase):

    def test_with_a_made_up_server(self):
        with tempfile.TemporaryDirectory() as tmp:
            server = os.path.join(tmp, "llama-server")
            with open(server, "w") as f:
                f.write(FAKE_SERVER.replace("#!/usr/bin/env python3", "#!" + sys.executable, 1))
            os.chmod(server, os.stat(server).st_mode | stat.S_IXUSR)
            for name in (vd.MODEL, vd.PROJECTOR):
                open(os.path.join(tmp, name), "w").close()
            picture = os.path.join(tmp, "p.png")
            with open(picture, "wb") as f:
                f.write(b"\x89PNG fake")
            old = os.environ["PATH"]
            os.environ["PATH"] = f"{tmp}:{old}"
            try:
                self.assertTrue(vd.available(tmp))
                text = vd.describe(picture, "it", model_dir=tmp)
            finally:
                os.environ["PATH"] = old
            with open(server + ".log") as f:
                seen = json.load(f)
        self.assertEqual(text, "Un gatto rosso dorme su un divano blu.")
        self.assertIn("--mmproj", seen["args"])
        self.assertEqual(seen["request"]["messages"][0]["content"][1]["type"], "image_url")

    def test_not_available_without_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(vd.available(tmp))


if __name__ == "__main__":
    unittest.main(verbosity=2)
