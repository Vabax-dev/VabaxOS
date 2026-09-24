#!/usr/bin/env python3
"""Tests for vabaxos-welcome (ADR-0016), without speech and without changing the system.

The program runs in a pseudo-terminal in dry-run mode: it writes what it
would say and do to a file, which the tests read.

    python3 tests/welcome/test_welcome.py
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
PACKAGE = os.path.join(REPO, "packages", "vabaxos-welcome")
PROGRAM = os.path.join(PACKAGE, "root", "usr", "bin", "vabaxos-welcome")

UP, DOWN, ENTER, ESC = b"\x1b[A", b"\x1b[B", b"\r", b"\x1b"


class Welcome:
    """Runs the welcome in a pseudo-terminal and presses keys."""

    def __init__(self, options="", installer=False, live=True):
        self.tmp = tempfile.TemporaryDirectory()
        self.log = os.path.join(self.tmp.name, "dry-run.log")
        locale_dir = os.path.join(self.tmp.name, "locale")
        for po in os.listdir(os.path.join(PACKAGE, "po")):
            lang = po[:-3]
            mo_dir = os.path.join(locale_dir, lang, "LC_MESSAGES")
            os.makedirs(mo_dir)
            subprocess.run(
                [sys.executable, os.path.join(REPO, "scripts", "lib", "po2mo.py"),
                 os.path.join(PACKAGE, "po", po), os.path.join(mo_dir, "vabaxos-welcome.mo")],
                check=True,
            )
        env = dict(os.environ,
                   VABAXOS_WELCOME_DRY_RUN=self.log,
                   VABAXOS_WELCOME_OPTIONS=options,
                   VABAXOS_WELCOME_LOCALE_DIR=locale_dir,
                   VABAXOS_WELCOME_INSTALLER="1" if installer else "0",
                   VABAXOS_WELCOME_LIVE="1" if live else "0",
                   PYTHONDONTWRITEBYTECODE="1")
        self.pid, self.fd = pty.fork()
        if self.pid == 0:
            os.execve(sys.executable, [sys.executable, PROGRAM], env)
        self.drain(0.5)

    def drain(self, seconds):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            ready, _, _ = select.select([self.fd], [], [], 0.05)
            if ready:
                try:
                    os.read(self.fd, 4096)
                except OSError:
                    return

    def press(self, *keys):
        for key in keys:
            os.write(self.fd, key)
            self.drain(0.3)

    def finish(self, timeout=5):
        """Waits for the program to exit; returns (exit status, dry-run lines)."""
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            pid, status = os.waitpid(self.pid, os.WNOHANG)
            if pid:
                break
            self.drain(0.1)
        else:
            os.kill(self.pid, 9)
            os.waitpid(self.pid, 0)
            raise AssertionError("the welcome did not exit")
        os.close(self.fd)
        with open(self.log, encoding="utf-8") if os.path.exists(self.log) else open(os.devnull) as f:
            lines = f.read().splitlines()
        self.tmp.cleanup()
        return os.waitstatus_to_exitcode(status), lines


class WelcomeTest(unittest.TestCase):

    def test_english_try(self):
        w = Welcome()
        w.press(ENTER, ENTER)
        code, log = w.finish()
        self.assertEqual(code, 0)
        self.assertEqual(log[0], "say en: Welcome to VabaxOS. Use the arrow keys to choose your language, then press Enter.")
        # English only; each language is then read in its own language.
        self.assertEqual(log[1], "say en: English")
        self.assertNotIn("say it: Benvenuto in VabaxOS. Usa le frecce per scegliere la lingua, poi premi Invio.", log)
        self.assertIn("do set LANG=en_US.UTF-8", log)
        self.assertIn("do localectl set-x11-keymap us", log)
        self.assertEqual(log[-1], "say en: Starting the desktop. Please wait.")

    def test_italian_items_in_their_voice(self):
        w = Welcome()
        w.press(DOWN, ENTER, ENTER)
        code, log = w.finish()
        self.assertEqual(code, 0)
        self.assertIn("say it: Italiano", log)
        self.assertIn("do set LANG=it_IT.UTF-8", log)
        self.assertIn("do localectl set-x11-keymap it", log)
        self.assertIn("say it: Benvenuto in VabaxOS. Usa le frecce per scegliere la modalità "
                      "di configurazione o di utilizzo, poi premi Invio.", log)
        self.assertIn("say it: Prova VabaxOS", log)
        self.assertEqual(log[-1], "say it: Avvio del desktop. Attendi.")

    def test_language_from_boot_menu_skips_the_list(self):
        w = Welcome("vabaxos.lang=it")
        w.press(ENTER)
        code, log = w.finish()
        self.assertEqual(code, 0)
        spoken = [line for line in log if line.startswith("say ")]
        self.assertTrue(spoken[0].startswith("say it: Benvenuto in VabaxOS. Usa le frecce"), spoken[0])
        self.assertNotIn("say en: English", log)

    def test_without_voice_nothing_is_spoken(self):
        w = Welcome("vabaxos.voice=off")
        w.press(ENTER, ENTER)
        code, log = w.finish()
        self.assertEqual(code, 0)
        self.assertFalse([line for line in log if line.startswith("say ")], log)
        self.assertIn("do set LANG=en_US.UTF-8", log)

    def test_escape_goes_back_to_the_language(self):
        w = Welcome()
        w.press(ENTER, ESC, DOWN, ENTER, ENTER)
        code, log = w.finish()
        self.assertEqual(code, 0)
        self.assertEqual(log.count("say en: Welcome to VabaxOS. Use the arrow keys to choose your language, then press Enter."), 2)
        self.assertEqual(log[-1], "say it: Avvio del desktop. Attendi.")

    def test_installed_system_runs_once(self):
        # In an installed system the first entry starts VabaxOS, and the
        # welcome marks itself done so it does not come back (ADR-0016).
        w = Welcome(live=False)
        w.press(DOWN, ENTER, ENTER)
        code, log = w.finish()
        self.assertEqual(code, 0)
        self.assertIn("say it: Avvia VabaxOS", log)
        self.assertNotIn("say it: Prova VabaxOS", log)
        self.assertIn("do touch /var/lib/vabaxos/welcome-done", log)

    def test_live_system_is_not_marked_done(self):
        w = Welcome()
        w.press(ENTER, ENTER)
        _, log = w.finish()
        self.assertNotIn("do touch /var/lib/vabaxos/welcome-done", log)

    def test_shut_down(self):
        w = Welcome()
        w.press(ENTER, UP, ENTER)
        code, log = w.finish()
        self.assertEqual(code, 0)
        self.assertIn("say en: Shut down", log)
        self.assertIn("do systemctl poweroff", log)

    def test_accessibility_choices_reach_console_and_desktop(self):
        w = Welcome()
        # English; Accessibility; Faster voice twice; keyboard; large text;
        # high contrast; zoom; sticky keys; back (Esc); Try VabaxOS.
        w.press(ENTER, DOWN, ENTER,
                DOWN, ENTER, ENTER,
                DOWN, ENTER,
                DOWN, ENTER,
                DOWN, ENTER,
                DOWN, ENTER,
                DOWN, ENTER,
                ESC, ENTER)
        code, log = w.finish()
        self.assertEqual(code, 0)
        self.assertIn("say en: Keyboard: Italiano", log)
        self.assertIn("say en: Large text: on", log)
        self.assertIn("say en: High contrast: on", log)
        self.assertIn("say en: Zoom: on", log)
        self.assertIn("say en: Sticky keys: on", log)
        self.assertIn("do localectl set-x11-keymap it", log)
        self.assertIn("do console font TerminusBold 16x32", log)
        self.assertIn("do speakup rate 6", log)
        for line in ("rate=70", "text-scaling-factor=1.5", "cursor-size=48", "high-contrast=true",
                     "screen-magnifier-enabled=true", "mag-factor=2.0", "stickykeys-enable=true"):
            self.assertIn("do gsettings " + line, log)

    def test_default_choices_only_set_the_orca_rate(self):
        w = Welcome()
        w.press(ENTER, ENTER)
        code, log = w.finish()
        self.assertEqual(code, 0)
        settings = [line for line in log if line.startswith("do gsettings ")]
        self.assertEqual(settings, ["do gsettings [org.gnome.Orca.Voice]", "do gsettings rate=50"])

    def test_italian_accessibility_labels(self):
        w = Welcome("vabaxos.lang=it")
        w.press(DOWN, ENTER, DOWN, DOWN, DOWN, DOWN, ENTER, ESC, ENTER)
        code, log = w.finish()
        self.assertEqual(code, 0)
        self.assertIn("say it: Accessibilità", log)
        self.assertIn("say it: Alto contrasto: spento", log)
        self.assertIn("say it: Alto contrasto: attivo", log)

    def test_install_explains_the_boot_menu(self):
        w = Welcome(installer=True)
        w.press(ENTER, DOWN, ENTER, ENTER)
        code, log = w.finish()
        self.assertEqual(code, 0)
        self.assertIn("say en: Install VabaxOS", log)
        self.assertTrue(any("press I for the installer with voice" in line for line in log))
        self.assertIn("do systemctl reboot", log)

    def test_no_install_item_without_installer(self):
        w = Welcome()
        w.press(ENTER, DOWN, ESC, ESC, ENTER, ENTER)
        code, log = w.finish()
        self.assertEqual(code, 0)
        self.assertNotIn("say en: Install VabaxOS", log)


if __name__ == "__main__":
    unittest.main(verbosity=2)
