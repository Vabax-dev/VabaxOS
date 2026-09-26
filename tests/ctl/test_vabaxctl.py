#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Vabax and VabaxOS contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for vabaxctl (block 13): the answers, the Italian command names,
the changes of voice and screen reader, on a fake system (no gsettings, no
APT), and the Italian translation.

    python3 tests/ctl/test_vabaxctl.py
"""

import gettext
import importlib.machinery
import importlib.util
import os
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
PROGRAM = os.path.join(REPO, "packages", "vabaxos-ctl", "root", "usr", "bin", "vabaxctl")
PO = os.path.join(REPO, "packages", "vabaxos-ctl", "po", "it.po")

loader = importlib.machinery.SourceFileLoader("vabaxctl", PROGRAM)
spec = importlib.util.spec_from_loader("vabaxctl", loader)
vabaxctl = importlib.util.module_from_spec(spec)
loader.exec_module(vabaxctl)

APT_UPGRADE = """Reading package lists...
Inst vabaxos-voice [0.1.0~alpha.1] (0.1.0~alpha.1+git20260927.101010 VabaxOS:forky [all])
Inst orca [50.2-1] (50.3-1 Debian:testing [all])
Conf vabaxos-voice (0.1.0~alpha.1+git20260927.101010 VabaxOS:forky [all])
"""


class FakeSystem:
    def __init__(self, archive_enabled=False, key=True, session=True):
        self.settings = {("org.gnome.desktop.a11y.applications", "screen-reader-enabled"): "true",
                         (vabaxctl.ORCA_SPEECH, "synthesizer"): ""}
        self.session = session
        self.sources = "Types: deb\nURIs: https://example.invalid/\n" + ("" if archive_enabled else "Enabled: no\n")
        self.key = key
        self.executed = []

    def run(self, args):
        if args[0] == "dpkg-query":
            return "0.1.0~alpha.1"
        if args[0] == "apt-get":
            return APT_UPGRADE
        if args[0] == "gpg":
            return "pub:u:255:22:ABCD:::\nfpr:::::::::0123456789ABCDEF0123456789ABCDEF01234567:\n"
        return None

    def gsettings_get(self, schema, key):
        return self.settings.get((schema, key)) if self.session else None

    def gsettings_set(self, schema, key, value):
        if not self.session:
            return False
        self.settings[(schema, key)] = value
        return True

    def read(self, path):
        if path == vabaxctl.SOURCES:
            return self.sources
        if path == vabaxctl.OS_RELEASE:
            return 'PRETTY_NAME="VabaxOS 0.1 (Debian forky)"\n'
        return None

    def exists(self, path):
        return self.key and path == vabaxctl.KEYRING

    def exec(self, args):
        self.executed.append(args)
        return 0


def run(argv, system):
    lines = []
    code = vabaxctl.main(argv, system=system, out=lines.append)
    return code, lines


class VabaxctlTest(unittest.TestCase):

    def test_status(self):
        code, lines = run(["status"], FakeSystem())
        self.assertEqual(code, 0)
        self.assertEqual(lines[0], "VabaxOS 0.1 (Debian forky), packages 0.1.0~alpha.1")
        self.assertIn("Screen reader: on.", lines)
        self.assertIn("Voice: eSpeak NG.", lines)
        self.assertIn("VabaxOS archive: not on yet.", lines)
        self.assertIn("Updates: 2 ready. To install: vabaxctl update --now.", lines)

    def test_italian_names_and_default(self):
        self.assertEqual(run(["stato"], FakeSystem())[1], run(["status"], FakeSystem())[1])
        self.assertEqual(run([], FakeSystem())[1], run(["status"], FakeSystem())[1])

    def test_voice(self):
        system = FakeSystem()
        code, lines = run(["voce", "kokoro"], system)
        self.assertEqual(code, 0)
        self.assertEqual(system.settings[(vabaxctl.ORCA_SPEECH, "synthesizer")], "kokoro")
        self.assertIn("Kokoro", lines[0])
        self.assertEqual(run(["voice"], system)[1], ["Voice: natural voice, Kokoro."])
        run(["voice", "espeak"], system)
        self.assertEqual(system.settings[(vabaxctl.ORCA_SPEECH, "synthesizer")], "")
        self.assertEqual(run(["voice", "robot"], system)[0], 2)

    def test_screen_reader(self):
        system = FakeSystem()
        code, lines = run(["lettore", "spento"], system)
        self.assertEqual(code, 0)
        self.assertEqual(system.settings[("org.gnome.desktop.a11y.applications", "screen-reader-enabled")], "false")
        self.assertIn("Super+Alt+S", lines[0])
        run(["screen-reader", "on"], system)
        self.assertEqual(system.settings[("org.gnome.desktop.a11y.applications", "screen-reader-enabled")], "true")
        self.assertEqual(run(["screen-reader", "forse"], system)[0], 2)

    def test_without_desktop_session(self):
        system = FakeSystem(session=False)
        code, lines = run(["voice", "kokoro"], system)
        self.assertEqual(code, 1)
        self.assertIn("desktop", lines[0])
        self.assertIn("Screen reader: unknown here (no desktop session).", run(["status"], system)[1])

    def test_archive(self):
        code, lines = run(["archivio"], FakeSystem(archive_enabled=True))
        self.assertEqual(lines, ["VabaxOS archive: on.",
                                 "Project key: 0123 4567 89AB CDEF 0123 4567 89AB CDEF 0123 4567"])
        self.assertIn("Project key: not installed.", run(["archive"], FakeSystem(key=False))[1])

    def test_update_and_report_start_the_programs(self):
        system = FakeSystem()
        run(["aggiorna", "--now"], system)
        run(["rapporto"], system)
        self.assertEqual(system.executed, [["vabaxos-update", "--now"], ["vabaxos-report"]])

    def test_unknown_command(self):
        code, lines = run(["balla"], FakeSystem())
        self.assertEqual(code, 2)
        self.assertIn("vabaxctl help", lines[0])

    def test_italian_translation(self):
        with tempfile.TemporaryDirectory() as tmp:
            mo = os.path.join(tmp, "it", "LC_MESSAGES", "vabaxos-ctl.mo")
            os.makedirs(os.path.dirname(mo))
            subprocess.run(["msgfmt", "-o", mo, PO], check=True)
            translation = gettext.translation("vabaxos-ctl", tmp, languages=["it"])
            saved = vabaxctl._
            vabaxctl._ = translation.gettext
            vabaxctl.gettext.ngettext, saved_n = translation.ngettext, vabaxctl.gettext.ngettext
            try:
                lines = run(["stato"], FakeSystem())[1]
            finally:
                vabaxctl._ = saved
                vabaxctl.gettext.ngettext = saved_n
        self.assertIn("Lettore di schermo: acceso.", lines)
        self.assertIn("Aggiornamenti: 2 pronti. Per installarli: vabaxctl aggiorna --now.", lines)


if __name__ == "__main__":
    unittest.main(verbosity=2)
