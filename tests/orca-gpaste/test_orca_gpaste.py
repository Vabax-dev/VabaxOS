#!/usr/bin/env python3
"""Tests for the image hook that keeps Orca 50 speaking when the GPaste
history is empty (image/config/hooks/normal/8410-vabaxos-orca-gpaste.hook.chroot).

The hook runs on a copy of Orca's clipboard.py: Orca 50 gets the change
Orca 51 already has, Orca 51 is left alone, unknown code stops the build,
and a second run changes nothing.

    ORCA_50=/path/to/orca-50 ORCA_51=/path/to/orca-51 python3 tests/orca-gpaste/test_orca_gpaste.py

Without the sources only the unknown-code case runs.
"""

import os
import shutil
import subprocess
import tempfile
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(REPO, "image", "config", "hooks", "normal", "8410-vabaxos-orca-gpaste.hook.chroot")


def source(variable):
    folder = os.environ.get(variable, "")
    path = os.path.join(folder, "src", "orca", "clipboard.py")
    return path if folder and os.path.exists(path) else None


class HookTest(unittest.TestCase):

    def run_hook(self, original):
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder)
        copy = os.path.join(folder, "clipboard.py")
        if original:
            shutil.copy(original, copy)
        else:
            with open(copy, "w", encoding="utf-8") as f:
                f.write("x = 1\n")
        result = subprocess.run(["sh", HOOK], env=dict(os.environ, ORCA_CLIPBOARD=copy),
                                capture_output=True, text=True, check=False)
        return result, copy

    @unittest.skipUnless(source("ORCA_50"), "ORCA_50: no Orca 50 source")
    def test_orca_50_is_changed_once(self):
        result, copy = self.run_hook(source("ORCA_50"))
        self.assertEqual(result.returncode, 0, result.stderr)
        text = open(copy, encoding="utf-8").read()
        self.assertIn("        except DBusError as error:\n", text)
        self.assertIn('            return ""\n', text)
        self.assertEqual(text.count("GetElementAtIndex(0)"), 1)
        again = subprocess.run(["sh", HOOK], env=dict(os.environ, ORCA_CLIPBOARD=copy),
                               capture_output=True, text=True, check=False)
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertEqual(open(copy, encoding="utf-8").read(), text)

    @unittest.skipUnless(source("ORCA_51"), "ORCA_51: no Orca 51 source")
    def test_orca_51_is_left_alone(self):
        original = open(source("ORCA_51"), encoding="utf-8").read()
        result, copy = self.run_hook(source("ORCA_51"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(open(copy, encoding="utf-8").read(), original)

    def test_unknown_code_stops_the_build(self):
        result, _copy = self.run_hook(None)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not the expected one", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
