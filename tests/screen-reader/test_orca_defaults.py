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
# The user changes one key; a newer VabaxOS adds a key for another
# command: it arrives, the user's key stays.
data = store.load()
data["profiles"]["default"]["keybindings"]["landmarkGoNext"] = [["q", "461", "0", "1"]]
store.save(data)
with open(defaults) as f:
    newer = json.load(f)
newer["keybindings"]["headingGoNext"] = [["h", "461", "0", "1"]]
newer["keybindings"]["landmarkGoNext"] = [["y", "461", "0", "1"]]
with open(defaults, "w") as f:
    json.dump(newer, f)
added = store.apply_vabaxos_defaults(defaults, state, local)
keys = store.load()["profiles"]["default"]["keybindings"]
print("NEWKEY:%d,%s,%s" % (added, keys.get("headingGoNext"), keys.get("landmarkGoNext")))
# The speed chosen in the spoken welcome.
with open(local, "w") as f:
    json.dump({"general": {"voices": {"default": {"rate": 80, "established": True}}}}, f)
fifth = store.apply_vabaxos_defaults(defaults, state, local)
print("WELCOME:%d,%s" % (fifth, echo.get("voice", "rate", "voices/default")))
'''


# VabaxOS 0.1 kept all the keys as one line of the state file: after the
# upgrade, a key still at 0.1's default gets the new one, a changed key stays.
LEGACY_CHILD = r'''
import json, os, sys
sys.path.insert(0, sys.argv[1])
from vabaxos_screen_reader import store
defaults, state = sys.argv[2], sys.argv[3]
old_keys = {"landmarkGoNext": [["d", "461", "0", "1"]], "headingGoNext": [["h", "461", "0", "1"]]}
data = store.load()
data["profiles"].setdefault("default", {"profile": ["Default", "default"]})["keybindings"] = {
    "landmarkGoNext": [["d", "461", "0", "1"]], "headingGoNext": [["j", "461", "0", "1"]]}
store.save(data)
os.makedirs(os.path.dirname(state), exist_ok=True)
with open(state, "w") as f:
    f.write("keybindings\t%s\n" % json.dumps(old_keys, sort_keys=True))
with open(defaults, "w") as f:
    json.dump({"general": {}, "keybindings": {"landmarkGoNext": [["x", "461", "0", "1"]],
                                              "headingGoNext": [["k", "461", "0", "1"]]}}, f)
written = store.apply_vabaxos_defaults(defaults, state, defaults + ".local")
keys = store.load()["profiles"]["default"]["keybindings"]
print("LEGACY:%d,%s,%s" % (written, keys["landmarkGoNext"], keys["headingGoNext"]))
with open(state) as f:
    print("STATE:%s" % ",".join(sorted(line.split("\t")[0] for line in f)))
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

    def test_new_key_for_a_user_who_changed_one(self):
        self.assertEqual(self.out.get("NEWKEY"), "1,[['h', '461', '0', '1']],[['q', '461', '0', '1']]", self.err)

    def test_upgrade_from_the_state_of_0_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, XDG_DATA_HOME=os.path.join(tmp, "data"), PYTHONDONTWRITEBYTECODE="1")
            result = subprocess.run([sys.executable, "-c", LEGACY_CHILD, LIBRARY, os.path.join(tmp, "d.json"),
                                     os.path.join(tmp, "state", "orca-defaults")], env=env,
                                    capture_output=True, text=True, timeout=60)
        out = dict(line.split(":", 1) for line in result.stdout.splitlines() if ":" in line)
        self.assertEqual(out.get("LEGACY"), "1,[['x', '461', '0', '1']],[['j', '461', '0', '1']]",
                         result.stderr[-3000:])
        self.assertEqual(out.get("STATE"), "keybindings/headingGoNext,keybindings/landmarkGoNext")

    def test_speed_of_the_welcome(self):
        self.assertEqual(self.out.get("WELCOME"), "1,80", self.err)

    def test_new_default(self):
        # The keys were still the old default of VabaxOS: replaced by the
        # new one; key echo, the user's choice, stays.
        self.assertEqual(self.out.get("NEWDEFAULT"), "1,True,[['x', '461', '0', '1']]", self.err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
