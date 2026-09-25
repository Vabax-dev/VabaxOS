#!/usr/bin/env python3
"""Tests for the button-names@vabaxos.org GNOME Shell extension (ADR-0022),
in a headless GNOME Shell with private D-Bus buses and a temporary home:
nothing on the system changes.

    python3 tests/button-names/test_button_names.py

A helper extension shows a notification and a row of test buttons; the
accessibility tree is read with vabaxos-a11y-check, as Orca would see it.
Needs gnome-shell, at-spi2-core, python3-gi and gir1.2-atspi-2.0; for the
Italian test also the it_IT.UTF-8 locale. Without them the tests are
skipped, except in the CI (CI=true), where they must run.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PACKAGE = os.path.join(REPO, "packages", "vabaxos-accessibility")
EXTENSION = os.path.join(PACKAGE, "root", "usr", "share", "gnome-shell", "extensions", "button-names@vabaxos.org")
CHECKER = os.path.join(PACKAGE, "root", "usr", "bin", "vabaxos-a11y-check")
UUID = "button-names@vabaxos.org"
HELPER_UUID = "test-helper@vabaxos.test"

# Test buttons, left to right: icon only; icon that changes after 1.5 s;
# an icon not in the table; an icon with a name of its own; a label; the
# style class of GNOME Shell's notification Close button and an empty icon;
# a button that gets its icon after it is shown.
HELPER = r"""
import GLib from 'gi://GLib';
import St from 'gi://St';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';

export default class TestHelper extends Extension {
    enable() {
        Main.notify('Test', 'VabaxOS test');
        const box = new St.BoxLayout({x: 10, y: 10});
        const make = params => {
            const button = new St.Button({can_focus: true, reactive: true, ...params});
            box.add_child(button);
            return button;
        };
        make({icon_name: 'window-close-symbolic'});
        const play = make({icon_name: 'media-playback-start-symbolic'});
        make({icon_name: 'view-list-bullet-symbolic'});
        make({icon_name: 'window-close-symbolic', accessible_name: 'Mine'});
        make({label: 'Hello'});
        make({style_class: 'message-close-button', child: new St.Icon()});
        Main.layoutManager.uiGroup.add_child(box);
        GLib.timeout_add(GLib.PRIORITY_DEFAULT, 1500, () => {
            play.icon_name = 'media-playback-pause-symbolic';
            make({}).icon_name = 'go-next-symbolic';
            return GLib.SOURCE_REMOVE;
        });
    }

    disable() {}
}
"""

ENGLISH = ["Close", "Pause", "view list bullet", "Mine", "Hello", "Close", "Forward"]
ITALIAN = ["Chiudi", "Pausa", "view list bullet", "Mine", "Hello", "Chiudi", "Avanti"]


REQUIRED = os.environ.get("CI") == "true"


def have_locale(name):
    result = subprocess.run(["locale", "-a"], capture_output=True, text=True)
    return name.lower().replace("-", "") in result.stdout.lower().replace("-", "")


class Shell:
    """A headless GNOME Shell on its own session and "system" buses."""

    def __init__(self, lang):
        self.tmp = tempfile.mkdtemp(prefix="vabaxos-shell-")
        self.procs = []
        env = dict(os.environ)
        env.update(HOME=os.path.join(self.tmp, "home"), XDG_RUNTIME_DIR=os.path.join(self.tmp, "run"),
                   GSETTINGS_BACKEND="keyfile", LANG=lang, LANGUAGE=lang.split("_")[0], LC_ALL=lang)
        os.makedirs(env["HOME"])
        os.makedirs(env["XDG_RUNTIME_DIR"], mode=0o700)
        env["DBUS_SESSION_BUS_ADDRESS"] = self._bus(env)
        # GNOME Shell only needs to reach a system bus; a private one will do.
        env["DBUS_SYSTEM_BUS_ADDRESS"] = self._bus(env)
        self.env = env
        extensions = os.path.join(env["HOME"], ".local", "share", "gnome-shell", "extensions")
        self._install(extensions)
        for schema, key, value in (("org.gnome.desktop.interface", "toolkit-accessibility", "true"),
                                   ("org.gnome.shell", "disable-user-extensions", "false"),
                                   ("org.gnome.shell", "enabled-extensions", f"['{UUID}', '{HELPER_UUID}']")):
            subprocess.run(["gsettings", "set", schema, key, value], env=env, check=True)
        self.log = open(os.path.join(self.tmp, "shell.log"), "w")
        self.procs.append(subprocess.Popen(
            ["gnome-shell", "--headless", "--wayland", "--no-x11", "--virtual-monitor", "1280x800"],
            env=env, stdout=self.log, stderr=subprocess.STDOUT))
        self._wait_for_extensions()

    def _bus(self, env):
        proc = subprocess.Popen(["dbus-daemon", "--session", "--nofork", "--print-address"],
                                env=env, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        self.procs.append(proc)
        address = proc.stdout.readline().strip()
        proc.stdout.close()
        return address

    def _install(self, extensions):
        version = re.search(r"(\d+)", subprocess.run(["gnome-shell", "--version"], capture_output=True,
                                                     text=True).stdout).group(1)
        target = os.path.join(extensions, UUID)
        shutil.copytree(EXTENSION, target)
        # The package targets the GNOME of the ISO; accept the one running here.
        metadata = os.path.join(target, "metadata.json")
        with open(metadata) as f:
            text = f.read()
        with open(metadata, "w") as f:
            f.write(re.sub(r'"shell-version": \[[^\]]*\]', f'"shell-version": ["{version}"]', text))
        # A locale/ folder next to the extension is where GNOME Shell looks
        # first for its translations.
        mo = os.path.join(target, "locale", "it", "LC_MESSAGES", "vabaxos-accessibility.mo")
        os.makedirs(os.path.dirname(mo))
        subprocess.run([sys.executable, os.path.join(REPO, "scripts", "lib", "po2mo.py"),
                        os.path.join(PACKAGE, "po", "it.po"), mo], check=True)
        helper = os.path.join(extensions, HELPER_UUID)
        os.makedirs(helper)
        with open(os.path.join(helper, "metadata.json"), "w") as f:
            f.write('{"uuid": "%s", "name": "Test helper", "description": "Test", "shell-version": ["%s"]}'
                    % (HELPER_UUID, version))
        with open(os.path.join(helper, "extension.js"), "w") as f:
            f.write(HELPER)

    def call(self, method, *args):
        return subprocess.run(["gdbus", "call", "--session", "--dest", "org.gnome.Shell", "--object-path",
                               "/org/gnome/Shell", "--method", method, *args],
                              env=self.env, capture_output=True, text=True).stdout

    def _wait_for_extensions(self):
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            info = self.call("org.gnome.Shell.Extensions.GetExtensionInfo", HELPER_UUID)
            if "'state': <1.0>" in info:
                time.sleep(4)  # the helper changes its buttons after 1.5 s
                return
            time.sleep(1)
        raise RuntimeError("GNOME Shell did not start its extensions; log: " + self.log.name)

    def a11y(self):
        result = subprocess.run([sys.executable, CHECKER, "--wait", "20", "--list", "gnome-shell"],
                                env=self.env, capture_output=True, text=True, cwd="/")
        return result.stdout + result.stderr

    def close(self):
        for proc in reversed(self.procs):
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
        self.log.close()
        shutil.rmtree(self.tmp, ignore_errors=True)


def test_buttons(tree):
    """Names of the helper's buttons, found after the "Mine" button."""
    buttons = re.findall(r"^\s*push button: (.*)$", tree, re.M)
    start = buttons.index("Mine") - 3
    return buttons[start:start + 7]


def unnamed(tree):
    return int(re.search(r"gnome-shell: (\d+) controls without a name", tree).group(1))


@unittest.skipUnless(REQUIRED or shutil.which("gnome-shell"), "gnome-shell is not installed")
class ButtonNamesTest(unittest.TestCase):
    def test_english_and_disable(self):
        shell = Shell("C.UTF-8")
        try:
            tree = shell.a11y()
            self.assertEqual(test_buttons(tree), ENGLISH, tree)
            # The notification banner: GNOME Shell's Expand and Close.
            self.assertRegex(tree, r"notification: .*\n(.*\n){0,12}\s*push button: Expand\n(.*\n)?\s*push button: Close")
            self.assertEqual(unnamed(tree), 0, tree)
            # Turned off, the extension leaves every button as it found it.
            shell.call("org.gnome.Shell.Extensions.DisableExtension", UUID)
            time.sleep(1)
            tree = shell.a11y()
            self.assertEqual(test_buttons(tree), ["", "", "", "Mine", "Hello", "", ""], tree)
            self.assertGreaterEqual(unnamed(tree), 5, tree)
            shell.call("org.gnome.Shell.Extensions.EnableExtension", UUID)
            time.sleep(1)
            self.assertEqual(unnamed(shell.a11y()), 0)
        finally:
            shell.close()

    @unittest.skipUnless(REQUIRED or have_locale("it_IT.UTF-8"), "the it_IT.UTF-8 locale is not installed")
    def test_italian(self):
        shell = Shell("it_IT.UTF-8")
        try:
            tree = shell.a11y()
            self.assertEqual(test_buttons(tree), ITALIAN, tree)
            self.assertEqual(unnamed(tree), 0, tree)
        finally:
            shell.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
