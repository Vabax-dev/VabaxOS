#!/usr/bin/env python3
"""Tests for vabaxos-recovery, the recovery mode that speaks (block 16):
the menu on a pseudo-terminal, keys typed as a person would, the actions
only written down (VABAXOS_RECOVERY_DRY_RUN).

    python3 tests/accessibility/test_recovery.py
"""

import os
import pty
import select
import subprocess
import sys
import tempfile
import time
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PACKAGE = os.path.join(REPO, "packages", "vabaxos-accessibility")
PROGRAM = os.path.join(PACKAGE, "root", "usr", "sbin", "vabaxos-recovery")


class Session:
    """vabaxos-recovery on a pseudo-terminal."""

    def __init__(self, log):
        self.master, slave = pty.openpty()
        env = dict(os.environ, VABAXOS_RECOVERY_DRY_RUN=log, LANGUAGE="C",
                   VABAXOS_RECOVERY_HOME=os.path.dirname(os.path.expanduser("~")))
        self.proc = subprocess.Popen([sys.executable, PROGRAM], stdin=slave, stdout=slave, stderr=slave,
                                     env=env, close_fds=True)
        os.close(slave)
        self.text = ""

    def read_until(self, words, timeout=10):
        end = time.time() + timeout
        while words not in self.text and time.time() < end:
            ready, _, _ = select.select([self.master], [], [], 0.2)
            if ready:
                try:
                    self.text += os.read(self.master, 4096).decode("utf-8", "replace")
                except OSError:
                    break
        return words in self.text

    def type(self, keys):
        os.write(self.master, keys.encode())

    def close(self):
        if self.proc.poll() is None:
            self.proc.kill()
        self.proc.wait()
        os.close(self.master)


class Recovery(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.log = os.path.join(self.tmp.name, "done")
        self.session = Session(self.log)

    def tearDown(self):
        self.session.close()
        self.tmp.cleanup()

    def done(self):
        try:
            with open(self.log, encoding="utf-8") as f:
                return f.read()
        except OSError:
            return ""

    def test_menu_is_read_line_by_line(self):
        self.assertTrue(self.session.read_until("9  Shut down"), self.session.text)
        self.assertIn("VabaxOS recovery mode. Press the number of your choice.", self.session.text)
        # Speakup reads new lines: the screen is never cleared.
        self.assertNotIn("\x1b[2J", self.session.text)

    def test_voice_and_console(self):
        self.assertTrue(self.session.read_until("9  Shut down"))
        self.session.type("x0")  # not choices: nothing happens
        self.session.type("2")
        self.assertTrue(self.session.read_until("put back for:") or self.session.read_until("No user on"),
                        self.session.text)
        if os.getuid() >= 1000:
            self.assertIn("/usr/libexec/vabaxos/voice-rescue --orca-settings", self.done())
            self.assertIn("setpriv --reuid=%d" % os.getuid(), self.done())
        self.session.type("7")
        self.assertTrue(self.session.read_until("Log in with your name and password."), self.session.text)
        self.assertEqual(self.session.proc.wait(timeout=10), 0)

    def test_updates_and_restart(self):
        self.assertTrue(self.session.read_until("9  Shut down"))
        self.session.type("4")
        self.assertTrue(self.session.read_until("Updates finished."), self.session.text)
        self.assertIn("dpkg --configure -a", self.done())
        self.assertIn("apt-get -y -o Dpkg::Options::=--force-confold -f install", self.done())
        self.session.type("8")
        self.assertEqual(self.session.proc.wait(timeout=10), 0)
        self.assertIn("systemctl reboot", self.done())

    def test_desktop(self):
        self.assertTrue(self.session.read_until("9  Shut down"))
        self.session.type("1")
        self.assertEqual(self.session.proc.wait(timeout=10), 0)
        self.assertIn("systemctl --no-block isolate graphical.target", self.done())


class Boot(unittest.TestCase):

    def test_installed_boot_menu(self):
        with open(os.path.join(PACKAGE, "root", "etc", "default", "grub.d", "vabaxos.cfg"), encoding="utf-8") as f:
            text = f.read()
        self.assertIn('GRUB_CMDLINE_LINUX_RECOVERY="vabaxos.recovery ', text)
        self.assertIn("GRUB_DISABLE_SUBMENU=y", text)
        with open(os.path.join(REPO, "image", "config", "bootloaders", "grub-pc", "grub.cfg"),
                  encoding="utf-8") as f:
            live = f.read()
        self.assertIn("vabaxos.recovery systemd.unit=multi-user.target", live)


if __name__ == "__main__":
    unittest.main(verbosity=2)
