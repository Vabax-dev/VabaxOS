#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Vabax and VabaxOS contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for Orca's key schemes (block 10): NVDA and JAWS keys without
conflicts, in both keyboard layouts; the dconf defaults; key names.

    python3 tests/screen-reader/test_keys.py
"""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "packages", "vabaxos-screen-reader", "root", "usr", "lib", "python3",
                                "dist-packages"))

from vabaxos_screen_reader import keymaps  # noqa: E402
from vabaxos_screen_reader.orca_commands import COMMANDS  # noqa: E402

NAMES = {row[0] for row in COMMANDS}


class SchemesTest(unittest.TestCase):

    def test_commands_exist_in_orca(self):
        for scheme in ("nvda", "jaws"):
            for layout in ("desktop", "laptop"):
                unknown = set(keymaps.overrides(scheme, layout)) - NAMES
                self.assertEqual(unknown, set(), (scheme, layout))

    def test_no_conflicts(self):
        for scheme in keymaps.SCHEMES:
            for layout in ("desktop", "laptop"):
                changed = set(keymaps.overrides(scheme, layout))
                keys = keymaps.effective(keymaps.entries(scheme, layout), layout)
                self.assertEqual(keymaps.conflicts(keys, changed), [], (scheme, layout))

    def test_many_keys(self):
        # Vabax: as many NVDA and JAWS keys as possible.
        self.assertGreaterEqual(len(keymaps.overrides("nvda")), 50)
        self.assertGreaterEqual(len(keymaps.overrides("jaws")), 50)

    def test_nvda_keys(self):
        keys = keymaps.effective(keymaps.entries("nvda"))
        expected = {
            "sayAllHandler": ("Down", 256, 1), "reviewCurrentLineHandler": ("Up", 256, 1),
            "whereAmIBasicHandler": ("Tab", 256, 1), "getTitleHandler": ("t", 256, 1),
            "presentTimeHandler": ("F12", 256, 1), "presentDateHandler": ("F12", 256, 2),
            "flatReviewSayAllHandler": ("b", 256, 1), "getStatusBarHandler": ("End", 256, 1),
            "toggle_presentation_mode": ("space", 256, 1), "shutdownHandler": ("q", 256, 1),
            "enterLearnModeHandler": ("1", 256, 1), "increaseSpeechRateHandler": ("Up", 260, 1),
            "list_links": ("F7", 256, 1), "list_headings": ("F6", 256, 1),
            # Browse mode quick keys of NVDA (block 14).
            "next_heading": ("h", 0, 1), "next_link": ("k", 0, 1), "next_form_field": ("f", 0, 1),
            "next_table": ("t", 0, 1), "next_landmark": ("d", 0, 1), "previous_landmark": ("d", 1, 1),
            "next_iframe": ("m", 0, 1), "next_live_region": ("j", 0, 1),
        }
        for name, key in expected.items():
            self.assertEqual(keys[name], key, name)

    def test_jaws_differences(self):
        keys = keymaps.effective(keymaps.entries("jaws"))
        self.assertEqual(keys["getStatusBarHandler"], ("Page_Down", 256, 1))
        self.assertEqual(keys["toggle_presentation_mode"], ("z", 256, 1))
        self.assertEqual(keys["shutdownHandler"], ("F4", 256, 1))

    def test_orca_scheme_keeps_orca_keys(self):
        self.assertEqual(keymaps.entries("orca"), {})
        self.assertEqual(keymaps.effective({}), keymaps.defaults())

    def test_entries_format(self):
        for bindings in keymaps.entries("nvda").values():
            self.assertEqual(len(bindings), 1)
            self.assertEqual(len(bindings[0]), 4)
            self.assertTrue(all(isinstance(part, str) for part in bindings[0]))
            self.assertEqual(bindings[0][1], "461")

    def test_dconf_defaults(self):
        text = keymaps.dconf_defaults()
        self.assertIn("[org/gnome/orca/default/keybindings]", text)
        self.assertIn("'sayAllHandler': [['Down', '461', '256', '1']]", text)
        self.assertIn("desktop-modifier-keys=['Insert', 'KP_Insert']", text)
        try:
            from gi.repository import GLib
        except ImportError:
            self.skipTest("no GLib")
        line = next(l for l in text.splitlines() if l.startswith("entries="))
        value = GLib.Variant.parse(GLib.VariantType("a{saas}"), line[len("entries="):], None, None)
        self.assertEqual(value.unpack(), keymaps.entries("nvda"))

    def test_labels(self):
        self.assertEqual(keymaps.label(("Down", 256, 1)), "Ins+Freccia giù")
        self.assertEqual(keymaps.label(("F12", 256, 2)), "Ins+F12, due volte")
        self.assertEqual(keymaps.label(("t", 257, 1)), "Ins+Maiusc+T")
        self.assertEqual(keymaps.label(("Down", 256, 1), italian=False), "Insert+Down")
        self.assertEqual(keymaps.label(None), "nessun tasto")


class GuideTest(unittest.TestCase):

    def test_guide_matches_the_schemes(self):
        import subprocess
        script = os.path.join(REPO, "scripts", "lib", "make-orca-keys-guide.py")
        text = subprocess.run([sys.executable, script], capture_output=True, text=True, check=True).stdout
        with open(os.path.join(REPO, "docs", "utente", "tasti-orca.md"), encoding="utf-8") as f:
            guide = f.read()
        self.assertIn(text, guide, "run scripts/lib/make-orca-keys-guide.py --write")


class KeyTextTest(unittest.TestCase):

    def setUp(self):
        try:
            from vabaxos_screen_reader import keys_page
        except (ImportError, ValueError):
            self.skipTest("no GTK 4")
        self.parse = keys_page.key_from_text

    def test_key_names(self):
        self.assertEqual(self.parse("T"), "t")
        self.assertEqual(self.parse("5"), "5")
        self.assertEqual(self.parse("f12"), "F12")
        self.assertEqual(self.parse("Freccia su"), "Up")
        self.assertEqual(self.parse("page down"), "Page_Down")
        self.assertEqual(self.parse("8 del tastierino"), "KP_Up")
        self.assertIsNone(self.parse("tasto inesistente"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
