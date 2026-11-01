#!/usr/bin/env python3
"""Tests for vabaxos-braille-check: what it says for each state of BRLTTY,
BrlAPI, the group, the display and Orca (made-up probes).

    python3 tests/braille/test_braille_check.py
"""

import importlib.machinery
import importlib.util
import os
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROGRAM = os.path.join(REPO, "packages", "vabaxos-accessibility", "root", "usr", "bin", "vabaxos-braille-check")
loader = importlib.machinery.SourceFileLoader("braille_check", PROGRAM)
spec = importlib.util.spec_from_loader("braille_check", loader)
check = importlib.util.module_from_spec(spec)
loader.exec_module(check)


def probe(**changes):
    values = {"brltty": True, "running": True, "key": True, "group": True, "display": ("Baum", 40), "orca": True}
    values.update(changes)
    return {name: (lambda v=value: v) for name, value in values.items()}


class CheckTest(unittest.TestCase):

    def test_ready(self):
        text = check.summary(check.checks(probe()))
        self.assertTrue(text.startswith("Braille is ready."))
        self.assertIn("40 cells (Baum)", text)

    def test_not_in_group(self):
        text = check.summary(check.checks(probe(group=False)))
        self.assertTrue(text.startswith("Braille: 1 things to fix."))
        self.assertIn("brlapi group", text)

    def test_nothing_connected_and_off(self):
        results = check.checks(probe(display=None, orca=False, running=False))
        self.assertEqual(sum(1 for ok, _s in results if not ok), 3)

    def test_no_brltty(self):
        self.assertEqual(check.checks(probe(brltty=False)),
                         [(False, "BRLTTY is not installed: braille cannot work.")])

    def test_groups_of_live_user_and_installer(self):
        conf = os.path.join(REPO, "image", "config", "includes.chroot_after_packages", "etc", "live",
                            "config.conf.d", "vabaxos-groups.conf")
        self.assertIn(" brlapi", open(conf, encoding="utf-8").read())
        preseed = os.path.join(REPO, "image", "config", "includes.installer", "preseed.cfg")
        line = next(l for l in open(preseed, encoding="utf-8") if "user-default-groups" in l)
        self.assertIn("brlapi", line.split())

    def test_key_present_even_if_readable_by_root_only(self):
        import tempfile
        folder = tempfile.mkdtemp()
        key = os.path.join(folder, "brlapi.key")
        old = check.KEY
        self.addCleanup(setattr, check, "KEY", old)
        check.KEY = key
        self.assertFalse(check.key_present())
        with open(key, "w", encoding="utf-8") as f:
            f.write("0123456789abcdef\n")
        os.chmod(key, 0o600)
        self.assertTrue(check.key_present())
        os.remove(key)
        os.rmdir(folder)

    def test_group_created_by_the_package(self):
        package = os.path.join(REPO, "packages", "vabaxos-accessibility")
        sysusers = open(os.path.join(package, "root", "usr", "lib", "sysusers.d", "vabaxos-brlapi.conf"),
                        encoding="utf-8").read()
        self.assertIn("g brlapi -", [line.strip() for line in sysusers.splitlines()])
        postinst = open(os.path.join(package, "postinst"), encoding="utf-8").read()
        self.assertIn("systemd-sysusers vabaxos-brlapi.conf", postinst)


if __name__ == "__main__":
    unittest.main(verbosity=2)
