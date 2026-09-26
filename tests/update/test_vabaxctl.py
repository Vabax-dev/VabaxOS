#!/usr/bin/env python3
"""Tests for vabaxctl (block 13): files in a temporary folder, nothing
changes on the system.

    python3 tests/update/test_vabaxctl.py
"""

import contextlib
import importlib.machinery
import importlib.util
import io
import os
import re
import tempfile
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PACKAGE = os.path.join(REPO, "packages", "vabaxos-update")
PROGRAM = os.path.join(PACKAGE, "root", "usr", "bin", "vabaxctl")

loader = importlib.machinery.SourceFileLoader("vabaxctl", PROGRAM)
spec = importlib.util.spec_from_loader("vabaxctl", loader)
ctl = importlib.util.module_from_spec(spec)
loader.exec_module(ctl)


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = ctl.main(argv)
    return code, out.getvalue(), err.getvalue()


class VabaxctlTest(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        d = self.dir.name
        self.saved = {name: getattr(ctl, name) for name in
                      ("DEBIAN_SOURCES", "ARCHIVE_SOURCES", "VOICE_CONFIG", "VOICE_STATE", "output")}
        ctl.DEBIAN_SOURCES = os.path.join(d, "vabaxos-debian.sources")
        ctl.ARCHIVE_SOURCES = os.path.join(d, "vabaxos.sources")
        ctl.VOICE_CONFIG = os.path.join(d, "etc", "voice.conf")
        ctl.VOICE_STATE = os.path.join(d, "state.conf")
        ctl.output = lambda *command: {"dpkg-query": "0.1.0~alpha.1", "systemctl": "active"}.get(command[0], "")

    def tearDown(self):
        for name, value in self.saved.items():
            setattr(ctl, name, value)
        self.dir.cleanup()

    def test_status_without_vabaxos_sources(self):
        code, out, _ = run([])
        self.assertEqual(code, 0)
        self.assertIn("VabaxOS 0.1.0~alpha.1.", out)
        self.assertIn("not checked by VabaxOS", out)
        self.assertIn("VabaxOS archive: not set up yet.", out)
        self.assertIn("Desktop voice: eSpeak NG.", out)
        self.assertIn("Orca is on.", out)

    def test_status_with_vabaxos_sources_and_kokoro(self):
        with open(ctl.DEBIAN_SOURCES, "w") as f:
            f.write("URIs: https://snapshot.debian.org/archive/debian/20260924T000000Z/\n")
        open(ctl.ARCHIVE_SOURCES, "w").close()
        with open(ctl.VOICE_STATE, "w") as f:
            f.write("engine=kokoro\nit=if_sara\n")
        _, out, _ = run(["status"])
        self.assertIn("date 2026-09-24", out)
        self.assertIn("VabaxOS archive: on.", out)
        self.assertIn("Kokoro, the natural voice", out)

    def test_write_voice_keeps_other_settings(self):
        os.makedirs(os.path.dirname(ctl.VOICE_CONFIG))
        with open(ctl.VOICE_CONFIG, "w") as f:
            f.write("# mine\nengine=espeak\nmax_delay_ms=600\n")
        ctl.shutil.which, which = (lambda name: None), ctl.shutil.which
        try:
            ctl.write_voice("auto")
        finally:
            ctl.shutil.which = which
        with open(ctl.VOICE_CONFIG) as f:
            text = f.read()
        self.assertEqual(re.findall(r"^engine=.*$", text, re.M), ["engine=auto"])
        self.assertIn("max_delay_ms=600", text)
        self.assertIn("# mine", text)
        _, out, _ = run(["voice"])
        self.assertIn("Chosen at every start", out)

    def test_unknown_voice_and_command(self):
        code, _, err = run(["voice", "piper"])
        self.assertEqual(code, 2)
        self.assertIn("use espeak, kokoro or auto", err)
        code, _, err = run(["nothing"])
        self.assertEqual(code, 2)
        self.assertIn("Commands:", err)
        self.assertEqual(run(["--as-root-voice", "rm -rf"])[0], 2)

    def test_every_message_is_translated(self):
        with open(PROGRAM, encoding="utf-8") as f:
            messages = set(re.findall(r'_\("((?:[^"\\]|\\.)*)"\)', f.read()))
        with open(os.path.join(PACKAGE, "po", "it.po"), encoding="utf-8") as f:
            translated = set(re.findall(r'^msgid "(.+)"$', f.read(), re.M))
        self.assertEqual(messages - translated, set())


if __name__ == "__main__":
    unittest.main(verbosity=2)
