#!/usr/bin/env python3
"""VabaxOS's Orca defaults are written as the user's own values, and never
over a value the user set (block 14, ADR-0027: Orca 48's JSON settings).

    python3 tests/screen-reader/test_orca_defaults.py

Orca's settings in a temporary data folder, in a child process: nothing on
the system changes.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
LIBRARY = os.path.join(REPO, "packages", "vabaxos-screen-reader", "root", "usr", "lib", "python3", "dist-packages")

DEFAULTS = {"general": {"enableKeyEcho": False, "enableEchoByCharacter": True},
            "keybindings": {"landmarkGoNext": [["d", "461", "0", "1"]]}}

CHILD = r'''
import json, sys
sys.path.insert(0, sys.argv[1])
from vabaxos_screen_reader import store
defaults, state = sys.argv[2], sys.argv[3]
echo = store.Store()
echo.set("typing-echo", "character-echo", False)          # the user's own choice
local = defaults + ".local"   # missing: no choices from the welcome
first = store.apply_vabaxos_defaults(defaults, state, local)
second = store.apply_vabaxos_defaults(defaults, state, local)
print("WRITTEN:%d,%d" % (first, second))
profile = store.load()["profiles"]["default"]
print("KEYECHO:%s,%s" % (echo.get("typing-echo", "key-echo"), "enableKeyEcho" in profile))
print("CHARECHO:%s" % echo.get("typing-echo", "character-echo"))
print("LANDMARK:%s" % echo.get("keybindings", "entries").get("landmarkGoNext"))
# The user turns key echo on again in Orca's preferences: Orca removes the
# value (it equals Orca's default). The next start must not undo it.
data = store.load()
del data["profiles"]["default"]["enableKeyEcho"]
store.save(data)
third = store.apply_vabaxos_defaults(defaults, state, local)
print("AFTERRESET:%d,%s" % (third, echo.get("typing-echo", "key-echo")))
# A newer VabaxOS changes a default: given again where the value is still
# the old default of VabaxOS, not where the user chose.
with open(defaults) as f:
    text = f.read()
with open(defaults, "w") as f:
    f.write(text.replace('"d"', '"x"'))
fourth = store.apply_vabaxos_defaults(defaults, state, local)
print("NEWDEFAULT:%d,%s,%s" % (fourth, echo.get("typing-echo", "key-echo"),
                               echo.get("keybindings", "entries").get("landmarkGoNext")))
# The speed chosen in the spoken welcome.
with open(local, "w") as f:
    json.dump({"general": {"voices": {"default": {"rate": 80, "established": True}}}}, f)
fifth = store.apply_vabaxos_defaults(defaults, state, local)
print("WELCOME:%d,%s" % (fifth, echo.get("voice", "rate", "voices/default")))
'''


class OrcaDefaultsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        defaults = os.path.join(cls.tmp.name, "orca-defaults.json")
        with open(defaults, "w", encoding="utf-8") as f:
            json.dump(DEFAULTS, f)
        env = dict(os.environ, XDG_DATA_HOME=os.path.join(cls.tmp.name, "data"), PYTHONDONTWRITEBYTECODE="1")
        state = os.path.join(cls.tmp.name, "state", "orca-defaults")
        result = subprocess.run([sys.executable, "-c", CHILD, LIBRARY, defaults, state], env=env,
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

    def test_given_once(self):
        # Orca removed the user's value that equals its own default: kept.
        self.assertEqual(self.out.get("AFTERRESET"), "0,True", self.err)

    def test_speed_of_the_welcome(self):
        self.assertEqual(self.out.get("WELCOME"), "1,80", self.err)

    def test_new_default(self):
        # The keys were still the old default of VabaxOS: replaced by the
        # new one; key echo, the user's choice, stays.
        self.assertEqual(self.out.get("NEWDEFAULT"), "1,True,[['x', '461', '0', '1']]", self.err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
