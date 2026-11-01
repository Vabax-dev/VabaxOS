#!/usr/bin/env python3
"""Tests for vabaxos-dictation: the text cleaning, the silence check, the
call to whisper.cpp, and start and stop with a made-up recorder and a
made-up whisper.cpp (the real model is downloaded only when the package is
built). With espeak-ng, real speech is checked to count as speech.

    python3 tests/dictation/test_dictation.py
"""

import importlib.machinery
import importlib.util
import math
import os
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
import unittest
import wave

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PACKAGE = os.path.join(REPO, "packages", "vabaxos-dictation")
LIB = os.path.join(PACKAGE, "root", "usr", "lib", "python3", "dist-packages")
PROGRAM = os.path.join(PACKAGE, "root", "usr", "bin", "vabaxos-dictation")
sys.path.insert(0, LIB)

from vabaxos_dictation import core  # noqa: E402


def write_wav(path, samples, rate=16000):
    with wave.open(path, "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(rate)
        out.writeframes(struct.pack(f"<{len(samples)}h", *samples))


def tone(seconds, volume, rate=16000):
    return [int(32767 * volume * math.sin(2 * math.pi * 220 * i / rate)) for i in range(int(rate * seconds))]


def executable(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR)


class CleanTest(unittest.TestCase):

    def test_invented_sentences_go(self):
        self.assertEqual(core.clean("Sottotitoli creati dalla comunità Amara.org"), "")
        self.assertEqual(core.clean(" Ciao a tutti.\n Sottotitoli creati dalla comunità Amara.org\n"), "Ciao a tutti.")
        self.assertEqual(core.clean("Thanks for watching!"), "")

    def test_sounds_in_brackets_go(self):
        self.assertEqual(core.clean("[Musica] Buongiorno. (applausi)"), "Buongiorno.")

    def test_spoken_commands(self):
        self.assertEqual(core.clean("Caro Marco, a capo, come stai?"), "Caro Marco\nCome stai?")
        self.assertEqual(core.clean("Prima parte. Nuovo paragrafo. seconda parte."), "Prima parte.\n\nSeconda parte.")
        self.assertEqual(core.clean("Hello new line world"), "Hello\nWorld")

    def test_spaces(self):
        self.assertEqual(core.clean("  Una   frase  \n  e un'altra. "), "Una frase e un'altra.")


class SilenceTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def wav(self, samples):
        path = os.path.join(self.tmp.name, "a.wav")
        write_wav(path, samples)
        return path

    def test_silence_and_room_noise_are_not_speech(self):
        self.assertFalse(core.has_speech(self.wav([0] * 32000)))
        self.assertFalse(core.has_speech(self.wav(tone(2, 0.003))))

    def test_voice_is_speech(self):
        self.assertTrue(core.has_speech(self.wav(tone(1, 0.2))))
        self.assertFalse(core.has_speech(self.wav(tone(0.1, 0.2) + [0] * 16000)), "a click is not speech")

    @unittest.skipUnless(shutil.which("espeak-ng"), "espeak-ng is not installed")
    def test_real_speech(self):
        path = os.path.join(self.tmp.name, "voice.wav")
        subprocess.run(["espeak-ng", "-v", "it", "-w", path, "Buongiorno, questa è una prova di dettatura."],
                       check=True)
        self.assertTrue(core.has_speech(path))

    def test_converted_to_16k_mono(self):
        source = os.path.join(self.tmp.name, "stereo.wav")
        with wave.open(source, "wb") as out:
            out.setnchannels(2)
            out.setsampwidth(2)
            out.setframerate(22050)
            out.writeframes(struct.pack("<4410h", *([1000, 3000] * 2205)))
        target = os.path.join(self.tmp.name, "16k.wav")
        self.assertTrue(core.as_16k_mono(source, target))
        with wave.open(target) as f:
            self.assertEqual((f.getnchannels(), f.getframerate()), (1, 16000))
            self.assertEqual(f.getnframes(), 1600)
            self.assertEqual(struct.unpack("<h", f.readframes(1))[0], 2000)
        self.assertFalse(core.as_16k_mono(target, os.path.join(self.tmp.name, "again.wav")))

    def test_broken_file(self):
        path = os.path.join(self.tmp.name, "broken.wav")
        with open(path, "wb") as f:
            f.write(b"not a wav")
        self.assertFalse(core.has_speech(path))

    def test_silence_never_reaches_whisper(self):
        self.assertEqual(core.transcribe(self.wav([0] * 16000), program="/nonexistent"), "")


class TranscribeTest(unittest.TestCase):

    def test_whisper_is_called_and_cleaned(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = os.path.join(tmp, "args")
            whisper = os.path.join(tmp, "whisper-cli")
            executable(whisper, f'#!/bin/sh\necho "$@" > "{log}"\n'
                                'printf " Caro Marco, a capo, ci vediamo domani.\\n'
                                ' Sottotitoli creati dalla comunità Amara.org\\n"\n')
            audio = os.path.join(tmp, "a.wav")
            write_wav(audio, tone(1, 0.2))
            text = core.transcribe(audio, "it", program=whisper, model="/m.bin")
            args = open(log, encoding="utf-8").read().split()
        self.assertEqual(text, "Caro Marco\nCi vediamo domani.")
        self.assertEqual(args[args.index("-l") + 1], "it")
        self.assertEqual(args[args.index("-m") + 1], "/m.bin")
        self.assertIn("-nt", args)

    def test_whisper_error_is_told(self):
        with tempfile.TemporaryDirectory() as tmp:
            whisper = os.path.join(tmp, "whisper-cli")
            executable(whisper, '#!/bin/sh\necho "error: failed to open model" >&2\nexit 1\n')
            audio = os.path.join(tmp, "a.wav")
            write_wav(audio, tone(1, 0.2))
            with self.assertRaisesRegex(RuntimeError, "failed to open model"):
                core.transcribe(audio, "it", program=whisper, model="/m.bin")


class CommandTest(unittest.TestCase):
    """start and stop, with made-up pw-record, pw-play and whisper-cli."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        tmp = self.tmp.name
        bin_dir = os.path.join(tmp, "bin")
        os.makedirs(bin_dir)
        self.voice = os.path.join(tmp, "voice.wav")
        write_wav(self.voice, tone(1, 0.2))
        # The recorder copies a prepared recording and waits for Ctrl+C.
        executable(os.path.join(bin_dir, "pw-record"),
                   f'#!/bin/sh\ncp "{self.voice}" "$7"\ntrap "exit 0" INT\nwhile :; do sleep 0.05; done\n')
        executable(os.path.join(bin_dir, "pw-play"), "#!/bin/sh\nexit 0\n")
        executable(os.path.join(bin_dir, "whisper-cli"), '#!/bin/sh\necho " Ciao Vabax, a capo, tutto bene?"\n')
        model_dir = os.path.join(tmp, "model")
        os.makedirs(model_dir)
        open(os.path.join(model_dir, core.MODEL), "w").close()
        self.env = dict(os.environ, PATH=f"{bin_dir}:{os.environ['PATH']}", XDG_RUNTIME_DIR=tmp,
                        VABAXOS_WHISPER_DIR=model_dir, LANGUAGE="it", LANG="it_IT.UTF-8",
                        PYTHONPATH=LIB, PYTHONDONTWRITEBYTECODE="1")

    def tearDown(self):
        subprocess.run([sys.executable, PROGRAM, "cancel"], env=self.env, capture_output=True)
        self.tmp.cleanup()

    def run_program(self, *args):
        return subprocess.run([sys.executable, PROGRAM, *args], env=self.env, capture_output=True, text=True,
                              timeout=30)

    def test_start_then_stop_gives_the_text(self):
        self.assertEqual(self.run_program("start").returncode, 0)
        self.assertEqual(self.run_program("start").returncode, 1, "only one recording at a time")
        result = self.run_program("stop")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "Ciao Vabax\nTutto bene?\n")
        folder = os.path.join(self.tmp.name, "vabaxos-dictation")
        self.assertEqual(os.listdir(folder), [], "the recording is deleted")
        self.assertEqual(self.run_program("stop").returncode, 1, "nothing to stop")

    def test_silence_gives_nothing(self):
        write_wav(self.voice, [0] * 16000)
        self.run_program("start")
        self.assertEqual(self.run_program("stop").returncode, 3)

    def test_cancel(self):
        self.run_program("start")
        self.assertEqual(self.run_program("cancel").returncode, 0)
        self.assertEqual(self.run_program("stop").returncode, 1)


class PackageTest(unittest.TestCase):

    def test_tones_and_model_line(self):
        with tempfile.TemporaryDirectory() as tree:
            subprocess.run([os.path.join(PACKAGE, "build"), tree], check=True)
            for name in ("start", "stop"):
                with wave.open(os.path.join(tree, "usr", "share", "vabaxos", "dictation", name + ".wav")) as f:
                    self.assertLess(f.getnframes() / f.getframerate(), 0.4)
        lines = [line.split() for line in open(os.path.join(PACKAGE, "fetch"), encoding="utf-8")
                 if line.strip() and not line.startswith("#")]
        self.assertEqual(len(lines), 1)
        url, sha, path = lines[0]
        self.assertTrue(url.endswith("/" + core.MODEL))
        self.assertEqual(len(sha), 40, "SHA-1 of whisper.cpp's model list")
        self.assertEqual(path, "usr/share/vabaxos/whisper/" + core.MODEL)

    def test_program_loads(self):
        loader = importlib.machinery.SourceFileLoader("vabaxos_dictation_program", PROGRAM)
        spec = importlib.util.spec_from_loader("vabaxos_dictation_program", loader)
        program = importlib.util.module_from_spec(spec)
        loader.exec_module(program)
        self.assertEqual(program.MAX_SECONDS, 120)


if __name__ == "__main__":
    unittest.main(verbosity=2)
