#!/usr/bin/env python3
"""Tests for voice-rescue, the program behind Ctrl+Super+Enter (block 16).

Orca's settings are fixed in a temporary home; the steps as root are only
written down (VABAXOS_RESCUE_DRY_RUN), nothing is stopped or started.

    python3 tests/accessibility/test_voice_rescue.py
"""

import importlib.machinery
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PACKAGE = os.path.join(REPO, "packages", "vabaxos-accessibility")
PROGRAM = os.path.join(PACKAGE, "root", "usr", "libexec", "vabaxos", "voice-rescue")


def load():
    loader = importlib.machinery.SourceFileLoader("voice_rescue", PROGRAM)
    spec = importlib.util.spec_from_loader("voice_rescue", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


rescue = load()


class OrcaSettings(unittest.TestCase):
    def test_silent_settings_are_put_back(self):
        data = {"general": {"enableSpeech": False, "speechServerInfo": ["kokoro", "kokoro"],
                            "voices": {"default": {"rate": 99, "gain": 0.0,
                                                   "family": {"name": "im_nicola"}}}},
                "profiles": {"default": {"profile": ["Default", "default"]},
                             "studio": {"enableSpeech": False, "voices": {"default": {"rate": 5}}}}}
        changes = rescue.fix_orca(data)
        self.assertTrue(changes)
        self.assertIs(data["general"]["enableSpeech"], True)
        self.assertEqual(data["general"]["speechServerInfo"], ["espeak-ng", "espeak-ng"])
        voice = data["general"]["voices"]["default"]
        self.assertEqual((voice["rate"], voice["gain"]), (50, 10.0))
        self.assertNotIn("family", voice)
        for profile in data["profiles"].values():
            self.assertEqual(profile["speechServerInfo"], ["espeak-ng", "espeak-ng"])
        self.assertIs(data["profiles"]["studio"]["enableSpeech"], True)
        self.assertEqual(data["profiles"]["studio"]["voices"]["default"]["rate"], 50)

    def test_other_settings_stay(self):
        data = {"general": {"enableSpeech": True, "speechServerInfo": ["espeak-ng", "espeak-ng"],
                            "verbalizePunctuationStyle": 0, "enableEchoByWord": True,
                            "voices": {"default": {"rate": 80, "gain": 7.0}}},
                "profiles": {}}
        before = json.loads(json.dumps(data))
        self.assertEqual(rescue.fix_orca(data), [])
        self.assertEqual(data, before)

    def test_program_settings_change_only_when_silent(self):
        app = {"profiles": {"default": {"general": {"enableSpeech": False, "enableEchoByWord": True}},
                            "fast": {"general": {"speechServerInfo": ["kokoro", "kokoro"]}},
                            "plain": {"general": {"enableEchoByWord": False}}}}
        rescue.fix_app(app, "gnome-terminal")
        self.assertIs(app["profiles"]["default"]["general"]["enableSpeech"], True)
        self.assertEqual(app["profiles"]["fast"]["general"]["speechServerInfo"], ["espeak-ng", "espeak-ng"])
        self.assertEqual(app["profiles"]["plain"]["general"], {"enableEchoByWord": False})

    def test_files_and_copy(self):
        with tempfile.TemporaryDirectory() as home:
            orca = os.path.join(home, ".local", "share", "orca")
            os.makedirs(os.path.join(orca, "app-settings"))
            with open(os.path.join(orca, "user-settings.conf"), "w", encoding="utf-8") as f:
                json.dump({"general": {"enableSpeech": False}, "profiles": {}}, f)
            with open(os.path.join(orca, "app-settings", "soffice.conf"), "w", encoding="utf-8") as f:
                json.dump({"profiles": {"default": {"general": {"enableSpeech": False}}}}, f)
            env = dict(os.environ, HOME=home)
            env.pop("XDG_DATA_HOME", None)
            result = subprocess.run([sys.executable, PROGRAM, "--orca-settings"], env=env,
                                    capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            with open(os.path.join(orca, "user-settings.conf"), encoding="utf-8") as f:
                self.assertIs(json.load(f)["general"]["enableSpeech"], True)
            with open(os.path.join(orca, "app-settings", "soffice.conf"), encoding="utf-8") as f:
                self.assertIs(json.load(f)["profiles"]["default"]["general"]["enableSpeech"], True)
            copies = os.path.join(home, ".local", "share", "vabaxos", "voice-rescue")
            (copy,) = os.listdir(copies)
            with open(os.path.join(copies, copy, "user-settings.conf"), encoding="utf-8") as f:
                self.assertIs(json.load(f)["general"]["enableSpeech"], False)


class Steps(unittest.TestCase):
    def test_order_as_root(self):
        """Sound, a word at once, speech-dispatcher, Orca's settings, the
        check through speech-dispatcher, Orca, console speech."""
        with tempfile.TemporaryDirectory() as tmp:
            runtime = os.path.join(tmp, "run-user")
            os.makedirs(os.path.join(runtime, str(os.getuid())))
            log = os.path.join(tmp, "commands")
            env = dict(os.environ, VABAXOS_RESCUE_DRY_RUN=log, VABAXOS_RESCUE_RUNTIME=runtime,
                       VABAXOS_RESCUE_DRY_OUTPUT="Volume: 0.10 [MUTED]")
            result = subprocess.run([sys.executable, PROGRAM], env=env, capture_output=True, text=True,
                                    check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            with open(log, encoding="utf-8") as f:
                commands = f.read().splitlines()
            if os.getuid() == 0:
                self.skipTest("run as root: no user under /run/user")
            order = ["wpctl set-mute", "wpctl set-volume @DEFAULT_AUDIO_SINK@ 0.5", "espeak-ng -v",
                     "pkill -TERM -u", "--orca-settings", "spd-say -w", "pkill -TERM -u {} -x orca",
                     "systemd-run --user", "systemctl restart espeakup.service"]
            position = 0
            for step in order:
                step = step.format(os.getuid())
                found = [i for i, line in enumerate(commands) if step in line and i >= position]
                self.assertTrue(found, f"{step!r} missing or out of order:\n" + "\n".join(commands))
                position = found[0]
            # Every user command runs as that user, never pkill -f.
            self.assertFalse([line for line in commands if "pkill -f" in line or "pgrep -f" in line])
            self.assertIn("vabaxos-voice-rescue: done", result.stdout)


class Package(unittest.TestCase):
    def test_keys_and_units(self):
        with open(os.path.join(PACKAGE, "root", "etc", "triggerhappy", "triggers.d",
                               "vabaxos-voice-rescue.conf"), encoding="utf-8") as f:
            lines = [line.split() for line in f if line.strip() and not line.startswith("#")]
        combos = {tuple(sorted(words[0].split("+"))) for words in lines}
        self.assertEqual(len(combos), 8)
        for words in lines:
            self.assertEqual(words[1], "1")
            self.assertEqual(words[2:], ["/usr/bin/touch", "/run/vabaxos-voice-rescue/request"])
        unit = os.path.join(PACKAGE, "root", "usr", "lib", "systemd", "system", "vabaxos-voice-rescue.path")
        with open(unit, encoding="utf-8") as f:
            self.assertIn("PathModified=/run/vabaxos-voice-rescue/request", f.read())
        with open(os.path.join(PACKAGE, "postinst"), encoding="utf-8") as f:
            self.assertIn("enable vabaxos-voice-rescue.path", f.read())
        self.assertTrue(os.access(PROGRAM, os.X_OK))


if __name__ == "__main__":
    unittest.main()
