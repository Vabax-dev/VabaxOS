#!/usr/bin/env python3
"""Tests for vabaxos-communication: the Start menu entries open the right
pages in Firefox, safely, with Italian names.

    python3 tests/communication/test_communication.py
"""

import configparser
import glob
import os
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ENTRIES = os.path.join(REPO, "packages", "vabaxos-communication", "root", "usr", "share", "applications")
EXPECTED = {"org.vabaxos.WhatsApp.desktop": "https://web.whatsapp.com/",
            "org.vabaxos.Telegram.desktop": "https://web.telegram.org/a/",
            "org.vabaxos.VideoCall.desktop": "https://meet.jit.si/"}


class EntriesTest(unittest.TestCase):

    def test_entries(self):
        found = {os.path.basename(p): p for p in glob.glob(os.path.join(ENTRIES, "*.desktop"))}
        self.assertEqual(set(found), set(EXPECTED))
        for name, url in EXPECTED.items():
            entry = configparser.ConfigParser(interpolation=None)
            entry.optionxform = str
            entry.read(found[name], encoding="utf-8")
            section = entry["Desktop Entry"]
            self.assertEqual(section["Exec"], f"firefox-esr --new-window {url}", name)
            self.assertTrue(url.startswith("https://"))
            self.assertIn("Comment[it]", section)
            self.assertTrue(section["Categories"].startswith("Network;"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
