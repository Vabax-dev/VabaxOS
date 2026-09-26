#!/usr/bin/env python3
"""vabaxos-desktop depends on every VabaxOS package, so an update brings new
components to systems installed with an earlier version (ADR-0020).

    python3 tests/packages/test_desktop.py
"""

import os
import re
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PACKAGES = os.path.join(REPO, "packages")


def control(name):
    with open(os.path.join(PACKAGES, name, "control"), encoding="utf-8") as f:
        return f.read()


class DesktopTest(unittest.TestCase):

    def test_depends_on_every_package(self):
        names = {n for n in os.listdir(PACKAGES)
                 if os.path.isfile(os.path.join(PACKAGES, n, "control")) and n != "vabaxos-desktop"}
        depends = re.search(r"^Depends: (.*)$", control("vabaxos-desktop"), re.M).group(1)
        listed = {part.strip().split(" ")[0] for part in depends.split(",")}
        self.assertEqual(names - listed, set(), "packages missing from vabaxos-desktop")
        self.assertEqual(listed - names, set(), "vabaxos-desktop depends on packages that do not exist")


if __name__ == "__main__":
    unittest.main(verbosity=2)
