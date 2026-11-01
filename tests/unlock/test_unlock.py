#!/usr/bin/env python3
"""Tests for vabaxos-unlock: the voice that asks the password of an
encrypted disk at boot (ADR-0021).

The initramfs hook runs on a made-up system and a made-up initramfs; the
askpass of VabaxOS runs with made-up espeak-ng, aplay and Debian askpass,
which write down what they are asked. Nothing is spoken, no disk is
touched.

    python3 tests/unlock/test_unlock.py
"""

import os
import stat
import subprocess
import tempfile
import time
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PACKAGE = os.path.join(REPO, "packages", "vabaxos-unlock")
ROOT = os.path.join(PACKAGE, "root")
HOOK = os.path.join(ROOT, "usr", "share", "initramfs-tools", "hooks", "vabaxos-unlock")
BOTTOM = os.path.join(ROOT, "usr", "share", "initramfs-tools", "scripts", "local-bottom", "vabaxos-unlock")

PCM = """00-03: HDMI 0 : HDMI 0 : playback 1
01-00: ALC257 Analog : ALC257 Analog : playback 1 : capture 1
01-02: ALC257 Alt Analog : ALC257 Alt Analog : capture 1
"""


def write(path, text, executable=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    if executable:
        os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def fake_tools(bin_dir, log):
    """espeak-ng, aplay, alsactl, modprobe and pidof that write down their
    arguments; espeak-ng also what it says (from its last argument)."""
    for name in ("espeak-ng", "aplay", "alsactl", "modprobe"):
        write(os.path.join(bin_dir, name),
              f'#!/bin/sh\necho "{name} $*" >> "{log}"\ncat > /dev/null 2>&1 &\nexit 0\n', executable=True)
    write(os.path.join(bin_dir, "pidof"), "#!/bin/sh\nexit 1\n", executable=True)


class HookTest(unittest.TestCase):

    def run_hook(self, locale="LANG=it_IT.UTF-8\n", choices="vabaxos.rate=4\n", conf=None, askpass=True):
        tmp = self.tmp.name
        system = os.path.join(tmp, "system")
        dest = os.path.join(tmp, "initramfs")
        bin_dir = os.path.join(tmp, "bin")
        log = os.path.join(tmp, "hook.log")
        fake_tools(bin_dir, log)
        write(os.path.join(system, "etc", "default", "locale"), locale)
        if choices:
            write(os.path.join(system, "var", "lib", "vabaxos", "installer-choices"), choices)
        if conf:
            write(os.path.join(system, "etc", "vabaxos", "unlock.conf"), conf)
        data = os.path.join(system, "usr", "lib", "x86_64-linux-gnu", "espeak-ng-data")
        for name in ("phondata", "phontab", "it_dict", "en_dict", "de_dict", "lang/roa/it"):
            write(os.path.join(data, name), "x")
        for name in ("askpass", "speech"):
            write(os.path.join(system, "usr", "lib", "vabaxos", "unlock", name),
                  open(os.path.join(ROOT, "usr", "lib", "vabaxos", "unlock", name), encoding="utf-8").read())
        write(os.path.join(system, "usr", "lib", "vabaxos", "unlock", "ready.wav"), "RIFF")
        if askpass:
            write(os.path.join(dest, "usr", "lib", "cryptsetup", "askpass"), "debian askpass", executable=True)
        functions = os.path.join(tmp, "hook-functions")
        write(functions, f'''
copy_exec() {{ echo "copy_exec $*" >> "{log}"; }}
copy_modules_dir() {{ echo "copy_modules_dir $*" >> "{log}"; }}
manual_add_modules() {{ echo "manual_add_modules $*" >> "{log}"; }}
''')
        env = dict(os.environ, DESTDIR=dest, VABAXOS_UNLOCK_ROOT=system, VABAXOS_HOOK_FUNCTIONS=functions,
                   PATH=f"{bin_dir}:{os.environ['PATH']}")
        result = subprocess.run(["sh", HOOK], env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        text = open(log, encoding="utf-8").read() if os.path.exists(log) else ""
        return dest, text

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def conf(self, dest):
        """The values of the configuration, read by sh as the initramfs does."""
        out = subprocess.run(["sh", "-c", '. "$1"; printf "%s\\n" "$VOICE" "$RATE" "$MSG_ASK" "$MSG_WRONG" "$MSG_OPEN"',
                              "sh", os.path.join(dest, "etc", "vabaxos-unlock.conf")],
                             capture_output=True, text=True, check=True).stdout
        return out.splitlines()

    def test_italian_with_the_speed_of_the_installer(self):
        dest, log = self.run_hook()
        voice, rate, ask, wrong, opened = self.conf(dest)
        self.assertEqual((voice, rate), ("it", "250"))
        self.assertIn("password del disco", ask)
        self.assertIn("sbagliata", wrong)
        self.assertIn("Disco aperto", opened)
        # Debian's askpass is kept, the VabaxOS one is in its place.
        cryptsetup = os.path.join(dest, "usr", "lib", "cryptsetup")
        self.assertEqual(open(os.path.join(cryptsetup, "askpass.real"), encoding="utf-8").read(), "debian askpass")
        self.assertIn("CRYPTTAB_TRIED", open(os.path.join(cryptsetup, "askpass"), encoding="utf-8").read())
        self.assertTrue(os.access(os.path.join(cryptsetup, "askpass"), os.X_OK))
        # Only the dictionaries of the language and English.
        data = os.path.join(dest, "usr", "lib", "x86_64-linux-gnu", "espeak-ng-data")
        self.assertEqual(sorted(n for n in os.listdir(data) if n.endswith("_dict")), ["en_dict", "it_dict"])
        self.assertTrue(os.path.exists(os.path.join(data, "lang", "roa", "it")))
        self.assertIn("copy_modules_dir kernel/sound", log)
        self.assertIn("manual_add_modules pcspkr", log)
        self.assertTrue(os.path.exists(os.path.join(dest, "usr", "lib", "vabaxos", "unlock", "speech")))

    def test_english_and_default_speed(self):
        dest, _log = self.run_hook(locale="LANG=en_GB.UTF-8\n", choices=None)
        voice, rate, ask, _w, _o = self.conf(dest)
        self.assertEqual((voice, rate), ("en-us", "175"))
        self.assertIn("password of the disk", ask)

    def test_own_messages_with_quotes(self):
        dest, _log = self.run_hook(conf="ENABLE=yes\nMSG_ASK=\"Scrivi la password dell'unità\"\n")
        self.assertEqual(self.conf(dest)[2], "Scrivi la password dell'unità")

    def test_nothing_without_encrypted_disks(self):
        dest, log = self.run_hook(askpass=False)
        self.assertFalse(os.path.exists(os.path.join(dest, "etc", "vabaxos-unlock.conf")))
        self.assertEqual(log, "")

    def test_turned_off(self):
        dest, _log = self.run_hook(conf="ENABLE=no\n")
        self.assertFalse(os.path.exists(os.path.join(dest, "etc", "vabaxos-unlock.conf")))
        self.assertEqual(open(os.path.join(dest, "usr", "lib", "cryptsetup", "askpass"),
                              encoding="utf-8").read(), "debian askpass")


class AskpassTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        tmp = self.tmp.name
        self.root = os.path.join(tmp, "initramfs")
        self.bin = os.path.join(tmp, "bin")
        self.log = os.path.join(tmp, "speech.log")
        self.run_dir = os.path.join(tmp, "run")
        fake_tools(self.bin, self.log)
        for name in ("askpass", "speech"):
            write(os.path.join(self.root, "usr", "lib", "vabaxos", "unlock", name),
                  open(os.path.join(ROOT, "usr", "lib", "vabaxos", "unlock", name), encoding="utf-8").read(),
                  executable=True)
        write(os.path.join(self.root, "usr", "lib", "vabaxos", "unlock", "ready.wav"), "RIFF")
        write(os.path.join(self.root, "etc", "vabaxos-unlock.conf"),
              "VOICE='it'\nRATE='210'\nMSG_ASK='Scrivi la password'\nMSG_WRONG='Password sbagliata'\n"
              "MSG_OPEN='Disco aperto'\n")
        write(os.path.join(self.root, "usr", "lib", "cryptsetup", "askpass.real"),
              '#!/bin/sh\necho "prompt: $1" >&2\necho secret\n', executable=True)
        write(os.path.join(tmp, "pcm"), PCM)
        self.env = dict(os.environ, VABAXOS_UNLOCK_ROOT=self.root, VABAXOS_UNLOCK_RUN=self.run_dir,
                        VABAXOS_UNLOCK_PCM=os.path.join(tmp, "pcm"),
                        VABAXOS_UNLOCK_CONSOLE=os.path.join(tmp, "console"),
                        PATH=f"{self.bin}:{os.environ['PATH']}")

    def tearDown(self):
        self.tmp.cleanup()

    def speech(self, lines):
        """Waits for the background voice: at most 15 seconds (slow CI runners)."""
        for _ in range(150):
            if os.path.exists(self.log):
                text = open(self.log, encoding="utf-8").read()
                if text.count("espeak-ng") >= lines:
                    return text
            time.sleep(0.1)
        return open(self.log, encoding="utf-8").read() if os.path.exists(self.log) else ""

    def askpass(self, tried):
        env = dict(self.env, CRYPTTAB_TRIED=str(tried))
        return subprocess.run([os.path.join(self.root, "usr", "lib", "vabaxos", "unlock", "askpass"),
                               "Please unlock disk sda3_crypt: "], env=env, capture_output=True, text=True,
                              timeout=30)

    def test_first_try_asks_with_the_voice(self):
        result = self.askpass(0)
        self.assertEqual(result.stdout, "secret\n")
        self.assertIn("prompt: Please unlock disk sda3_crypt: ", result.stderr)
        log = self.speech(1)
        self.assertIn("espeak-ng -v it -s 210 --stdout -- Scrivi la password", log)
        self.assertNotIn("sbagliata", log)
        # The analog card, not HDMI; the tones before the words.
        self.assertIn("aplay -q -D plughw:1,0", log)
        self.assertLess(log.index("ready.wav"), log.index("espeak-ng"))
        self.assertTrue(os.path.exists(os.path.join(self.run_dir, "asked")))
        self.assertEqual(open(os.path.join(self.tmp.name, "console"), encoding="utf-8").read(), "\a")

    def test_wrong_password_is_said(self):
        self.askpass(1)
        log = self.speech(2)
        self.assertLess(log.index("Password sbagliata"), log.index("Scrivi la password"))

    def test_disk_open_is_said_after_the_question(self):
        env = dict(self.env)
        subprocess.run(["sh", BOTTOM], env=env, check=True, timeout=30)
        self.assertEqual(self.speech(1), "", "nothing said when no password was asked")
        self.askpass(0)
        self.speech(1)
        subprocess.run(["sh", BOTTOM], env=env, check=True, timeout=30)
        self.assertIn("Disco aperto", self.speech(2))

    def test_without_a_sound_card_the_password_still_works(self):
        os.remove(os.path.join(self.tmp.name, "pcm"))
        self.env["VABAXOS_UNLOCK_TRIES"] = "5"
        start = time.monotonic()
        result = self.askpass(0)
        self.assertEqual(result.stdout, "secret\n")
        self.assertLess(time.monotonic() - start, 3, "the password must not wait for the sound card")
        time.sleep(1.5)  # the voice in the background gives up after half a second


class PackageTest(unittest.TestCase):

    def test_tones(self):
        import wave
        with tempfile.TemporaryDirectory() as tree:
            subprocess.run([os.path.join(PACKAGE, "build"), tree], check=True)
            with wave.open(os.path.join(tree, "usr", "lib", "vabaxos", "unlock", "ready.wav")) as f:
                seconds = f.getnframes() / f.getframerate()
        self.assertGreater(seconds, 0.3)
        self.assertLess(seconds, 0.6)


if __name__ == "__main__":
    unittest.main(verbosity=2)
