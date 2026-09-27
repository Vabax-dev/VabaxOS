#!/usr/bin/env python3
"""Tests for the Start button and the search box of the taskbar (block 15,
ADR-0025), in a headless GNOME Shell with private D-Bus buses and a
temporary home: nothing on the system changes.

    python3 tests/start/test_taskbar_start.py

vabaxos-keys@vabaxos.org runs without Dash to Panel, so its Start button
and search box go on GNOME's top bar; the accessibility tree is read with
vabaxos-a11y-check, as Orca would see it. Needs gnome-shell, at-spi2-core,
python3-gi and gir1.2-atspi-2.0; for the Italian test also the it_IT.UTF-8
locale. Without them the tests are skipped, except in the CI (CI=true).
"""

import importlib.util
import os
import re
import shutil
import subprocess
import sys
import time
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PACKAGE = os.path.join(REPO, "packages", "vabaxos-settings")
EXTENSION = os.path.join(PACKAGE, "root", "usr", "share", "gnome-shell", "extensions", "vabaxos-keys@vabaxos.org")
SCHEMA = os.path.join(PACKAGE, "root", "usr", "share", "glib-2.0", "schemas",
                      "org.gnome.shell.extensions.vabaxos-keys.gschema.xml")
UUID = "vabaxos-keys@vabaxos.org"

# The headless GNOME Shell of the button-names test.
_spec = importlib.util.spec_from_file_location(
    "button_names", os.path.join(REPO, "tests", "button-names", "test_button_names.py"))
button_names = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(button_names)

REQUIRED = button_names.REQUIRED


class Shell(button_names.Shell):
    """The same headless GNOME Shell, with vabaxos-keys only."""

    def __init__(self, lang):
        button_names.UUID, button_names.HELPER_UUID = UUID, UUID
        super().__init__(lang)

    def _install(self, extensions):
        version = re.search(r"(\d+)", subprocess.run(["gnome-shell", "--version"], capture_output=True,
                                                     text=True).stdout).group(1)
        target = os.path.join(extensions, UUID)
        shutil.copytree(EXTENSION, target)
        metadata = os.path.join(target, "metadata.json")
        with open(metadata) as f:
            text = f.read()
        with open(metadata, "w") as f:
            f.write(re.sub(r'"shell-version": \[[^\]]*\]', f'"shell-version": ["{version}"]', text))
        # Its settings and translations next to it, where GNOME Shell looks
        # first.
        schemas = os.path.join(target, "schemas")
        os.makedirs(schemas)
        shutil.copy(SCHEMA, schemas)
        subprocess.run(["glib-compile-schemas", schemas], check=True)
        mo = os.path.join(target, "locale", "it", "LC_MESSAGES", "vabaxos-settings.mo")
        os.makedirs(os.path.dirname(mo))
        subprocess.run([sys.executable, os.path.join(REPO, "scripts", "lib", "po2mo.py"),
                        os.path.join(PACKAGE, "po", "it.po"), mo], check=True)


def names(tree, role):
    return re.findall(rf"^\s*(?:{role}): (.*)$", tree, re.M)


@unittest.skipUnless(REQUIRED or shutil.which("gnome-shell"), "gnome-shell is not installed")
class TaskbarStartTest(unittest.TestCase):
    def check(self, lang, start, search):
        shell = Shell(lang)
        try:
            tree = shell.a11y()
            # AT-SPI 2.52 says "push button", 2.61 (forky) "button".
            self.assertIn(start, names(tree, "(?:push )?button"), tree)
            self.assertIn(search, names(tree, "entry|text"), tree)
        finally:
            shell.close()

    def test_english(self):
        self.check("C.UTF-8", "Start", "Search programs, settings and files")

    @unittest.skipUnless(REQUIRED or button_names.have_locale("it_IT.UTF-8"),
                         "the it_IT.UTF-8 locale is not installed")
    def test_italian(self):
        self.check("it_IT.UTF-8", "Start", "Cerca programmi, impostazioni e file")


if __name__ == "__main__":
    unittest.main(verbosity=2)
