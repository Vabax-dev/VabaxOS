#!/usr/bin/env python3
"""VabaxOS's Orca defaults are written as the user's own values, and never
over a value the user set (block 14). Orca 50 ignores system dconf defaults.

    python3 tests/screen-reader/test_orca_defaults.py

Orca's schema (the copy of Orca 50.2's in this folder) in a GSettings memory
backend, in a child process: nothing on the system changes.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
LIBRARY = os.path.join(REPO, "packages", "vabaxos-screen-reader", "root", "usr", "lib", "python3", "dist-packages")
COMPILER = shutil.which("glib-compile-schemas") or next(
    (p for p in ("/usr/lib/x86_64-linux-gnu/glib-2.0/glib-compile-schemas",
                 "/usr/lib/aarch64-linux-gnu/glib-2.0/glib-compile-schemas") if os.path.exists(p)), None)

KEYFILE = """# test
[org/gnome/orca/default/typing-echo]
key-echo=false
character-echo=true

[org/gnome/orca/default/keybindings]
entries={'next_landmark': [['d', '461', '0', '1']]}

[org/gnome/other]
ignored=true
"""

CHILD = r'''
import sys
sys.path.insert(0, sys.argv[1])
from gi.repository import Gio
from vabaxos_screen_reader import store
echo = Gio.Settings.new_with_path("org.gnome.Orca.TypingEcho", "/org/gnome/orca/default/typing-echo/")
echo.set_boolean("character-echo", False)          # the user's own choice
first = store.apply_vabaxos_defaults(sys.argv[2])
second = store.apply_vabaxos_defaults(sys.argv[2])
keys = Gio.Settings.new_with_path("org.gnome.Orca.Keybindings", "/org/gnome/orca/default/keybindings/")
print("WRITTEN:%d,%d" % (first, second))
print("KEYECHO:%s,%s" % (echo.get_boolean("key-echo"), echo.get_user_value("key-echo") is not None))
print("CHARECHO:%s" % echo.get_boolean("character-echo"))
print("LANDMARK:%s" % keys.get_value("entries").unpack().get("next_landmark"))
'''


@unittest.skipUnless(COMPILER, "glib-compile-schemas is not installed")
class OrcaDefaultsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        schemas = os.path.join(cls.tmp.name, "schemas")
        defaults = os.path.join(cls.tmp.name, "vabaxos.d")
        os.makedirs(schemas)
        os.makedirs(defaults)
        shutil.copy(os.path.join(HERE, "org.gnome.Orca.gschema.xml"), schemas)
        subprocess.run([COMPILER, schemas], check=True)
        with open(os.path.join(defaults, "41-orca-test"), "w", encoding="utf-8") as f:
            f.write(KEYFILE)
        env = dict(os.environ, GSETTINGS_BACKEND="memory", GSETTINGS_SCHEMA_DIR=schemas,
                   PYTHONDONTWRITEBYTECODE="1")
        result = subprocess.run([sys.executable, "-c", CHILD, LIBRARY, defaults], env=env,
                                capture_output=True, text=True, timeout=60)
        cls.out = dict(line.split(":", 1) for line in result.stdout.splitlines() if ":" in line)
        cls.err = result.stderr[-3000:]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_written_once_as_user_values(self):
        # key-echo and the keys; character-echo was the user's; nothing twice.
        self.assertEqual(self.out.get("WRITTEN"), "2,0", self.err)
        self.assertEqual(self.out.get("KEYECHO"), "False,True", self.err)

    def test_never_over_the_users_value(self):
        self.assertEqual(self.out.get("CHARECHO"), "False", self.err)

    def test_keys(self):
        self.assertEqual(self.out.get("LANDMARK"), "[['d', '461', '0', '1']]", self.err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
