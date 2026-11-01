#!/usr/bin/env python3
"""Tests for the Firefox and Thunderbird settings of VabaxOS
(vabaxos-settings, /etc/*/policies/policies.json): valid, and ready for
Orca.

    python3 tests/firefox/test_policies.py
"""

import json
import os
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ETC = os.path.join(REPO, "packages", "vabaxos-settings", "root", "etc")

# Mozilla's "Preferences" policy accepts only these beginnings of names.
ALLOWED = ("accessibility.", "alerts.", "app.update.", "browser.", "datareporting.policy.", "dom.",
           "extensions.", "general.autoScroll", "general.smoothScroll", "geo.", "gfx.", "intl.",
           "layers.", "layout.", "media.", "network.", "pdfjs.", "places.", "print.", "signon.",
           "spellchecker.", "ui.", "widget.")


def load(program):
    with open(os.path.join(ETC, program, "policies", "policies.json"), encoding="utf-8") as f:
        return json.load(f)["policies"]


class PoliciesTest(unittest.TestCase):

    def test_accessibility_always_on(self):
        for program in ("firefox", "thunderbird"):
            prefs = load(program)["Preferences"]
            self.assertEqual(prefs["accessibility.force_disabled"]["Value"], -1, program)

    def test_only_allowed_preferences(self):
        for program in ("firefox", "thunderbird"):
            for name, value in load(program)["Preferences"].items():
                self.assertTrue(name.startswith(ALLOWED), name)
                self.assertIn(value["Status"], ("default", "locked", "user", "clear"))

    def test_nothing_speaks_over_orca(self):
        policies = load("firefox")
        self.assertEqual(policies["Permissions"]["Autoplay"]["Default"], "block-audio")
        self.assertTrue(policies["UserMessaging"]["SkipOnboarding"])
        self.assertEqual(policies["OverrideFirstRunPage"], "")
        self.assertFalse(policies["Preferences"]["browser.aboutwelcome.enabled"]["Value"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
