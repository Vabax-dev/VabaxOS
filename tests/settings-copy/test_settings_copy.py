#!/usr/bin/env python3
"""Tests for vabaxos-settings-copy (block 16): a copy made and put back in
a temporary home, with the commands (dconf, nmcli, flatpak, PackageKit)
answered by a made-up computer; and the window on a hidden Broadway
display, where every button must have a name.

    python3 tests/settings-copy/test_settings_copy.py
"""

import json
import os
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
ROOT = os.path.join(REPO, "packages", "vabaxos-settings-copy", "root")
LIB = os.path.join(ROOT, "usr", "lib", "python3", "dist-packages")
PROGRAM = os.path.join(ROOT, "usr", "bin", "vabaxos-settings-copy")
sys.path.insert(0, LIB)
os.environ.setdefault("LANGUAGE", "C")

from vabaxos_settings_copy import copy  # noqa: E402

DCONF = """[/]
x=1

[org/gnome/desktop/a11y/applications]
screen-reader-enabled=true

[org/gnome/nautilus/window-state]
initial-size=(890, 550)

[org/gnome/desktop/wm/keybindings]
close=['<Alt>F4']
window-size=(1, 2)

[org/gnome/control-center]
last-panel='wifi'
"""

HISTORY = """Start-Date: 2026-09-27  10:00:00
Commandline: apt-get install -y grub-efi
Install: grub-efi:amd64 (2.12-9)
End-Date: 2026-09-27  10:01:00

Start-Date: 2026-10-01  09:00:00
Commandline: apt install gimp
Requested-By: user (1000)
Install: gimp:amd64 (3.0.4-3), libgimp:amd64 (3.0.4-3, automatic)
End-Date: 2026-10-01  09:02:00

Start-Date: 2026-10-02  09:00:00
Commandline: packagekit role='install-packages'
Install: audacity:amd64 (3.7.3-1), removed-later:amd64 (1.0), vabaxos-doctor:amd64 (0.1)
End-Date: 2026-10-02  09:02:00
"""


class Fake(copy.System):
    """A home in a temporary folder; commands answered from a dictionary."""

    def __init__(self, home, outputs=None):
        self._home = home
        self.outputs = {
            "dconf dump /": DCONF,
            "nmcli -t -e no -f NAME,TYPE connection show": "Casa:802-11-wireless\nWired:802-3-ethernet\n",
            "nmcli -s -e no -g 802-11-wireless.ssid,802-11-wireless-security.key-mgmt,"
            "802-11-wireless-security.psk connection show Casa": "CasaNet\nwpa-psk\nsegreta:123\n",
            "flatpak list --app --columns=application": "org.gnome.Podcasts\n",
            "apt-mark showmanual": "gimp\naudacity\ngrub-efi\n",
            "hostname": "vabaxos\n",
            "nmcli -t -e no -f NAME connection show": "Wired\n",
            "dpkg-query -W -f=${Package}\\n": "audacity\n",
        }
        self.outputs.update(outputs or {})
        self.ran = []
        self.stdin = {}

    def output(self, command, timeout=30, stdin=None):
        key = " ".join(command)
        self.ran.append(key)
        if stdin is not None:
            self.stdin[key] = stdin
        return self.outputs.get(key, "" if key.split()[0] in ("nmcli", "flatpak", "pkcon", "dconf",
                                                                 "systemd-run") else None)

    def home(self):
        return self._home

    def data_home(self):
        return os.path.join(self._home, ".local", "share")

    def config_home(self):
        return os.path.join(self._home, ".config")

    def apt_history(self):
        return HISTORY


def home_with_orca(folder):
    orca = os.path.join(folder, ".local", "share", "orca")
    os.makedirs(os.path.join(orca, "app-settings"))
    with open(os.path.join(orca, "user-settings.conf"), "w", encoding="utf-8") as f:
        json.dump({"general": {"enableEchoByWord": True}}, f)
    with open(os.path.join(orca, "app-settings", "soffice.conf"), "w", encoding="utf-8") as f:
        f.write("{}")
    sd = os.path.join(folder, ".config", "speech-dispatcher")
    os.makedirs(sd)
    with open(os.path.join(sd, "speechd.conf"), "w", encoding="utf-8") as f:
        f.write("DefaultRate 20\n")


class Copy(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = os.path.join(self.tmp.name, "home")
        home_with_orca(self.home)

    def tearDown(self):
        self.tmp.cleanup()

    def test_dconf_without_this_computer(self):
        kept = copy.keep_dconf(DCONF)
        self.assertIn("screen-reader-enabled=true", kept)
        self.assertIn("close=['<Alt>F4']", kept)
        for gone in ("initial-size", "window-size", "last-panel"):
            self.assertNotIn(gone, kept)

    def test_programs_a_person_installed(self):
        found = copy.user_packages(HISTORY, {"gimp", "audacity", "grub-efi", "vabaxos-doctor"})
        self.assertEqual(found, ["gimp", "audacity"])

    def test_make_write_read(self):
        system = Fake(self.home)
        data = copy.make(copy.PARTS, system)
        self.assertEqual(data["voice"]["orca"]["app-settings/soffice.conf"], "{}")
        self.assertEqual(data["voice"]["speech-dispatcher"]["speechd.conf"], "DefaultRate 20\n")
        self.assertEqual(data["wifi"]["networks"],
                         [{"name": "Casa", "ssid": "CasaNet", "key-mgmt": "wpa-psk", "psk": "segreta:123"}])
        self.assertEqual(data["programs"], {"flatpak": ["org.gnome.Podcasts"], "debian": ["gimp", "audacity"]})
        path = os.path.join(self.tmp.name, "copy.json")
        copy.write(path, data)
        # It may hold Wi-Fi passwords: only its owner reads it.
        self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o600)
        self.assertEqual(copy.read(path), data)
        self.assertEqual(copy.parts_in(data), list(copy.PARTS))
        with open(os.path.join(self.tmp.name, "other.json"), "w", encoding="utf-8") as f:
            f.write('{"something": 1}')
        self.assertIsNone(copy.read(os.path.join(self.tmp.name, "other.json")))

    def test_restore(self):
        data = copy.make(copy.PARTS, Fake(self.home))
        data["voice"]["orca"]["../../evil"] = "no"
        other = os.path.join(self.tmp.name, "other")
        os.makedirs(other)
        system = Fake(other, {"flatpak list --app --columns=application": ""})
        lines = copy.restore(data, copy.PARTS, system)
        with open(os.path.join(other, ".local", "share", "orca", "user-settings.conf"), encoding="utf-8") as f:
            self.assertTrue(json.load(f)["general"]["enableEchoByWord"])
        self.assertFalse(os.path.exists(os.path.join(self.tmp.name, "evil")))
        self.assertIn("screen-reader-enabled=true", system.stdin["dconf load /"])
        self.assertIn("nmcli connection add type wifi con-name Casa ssid CasaNet wifi-sec.key-mgmt wpa-psk "
                      "wifi-sec.psk segreta:123", system.ran)
        # audacity is already there: only gimp is installed.
        self.assertIn("pkcon --noninteractive install gimp", system.ran)
        self.assertIn("flatpak install --user -y --noninteractive flathub org.gnome.Podcasts", system.ran)
        self.assertEqual(len(lines), 4)

    def test_restore_only_some_parts(self):
        data = copy.make(copy.PARTS, Fake(self.home))
        system = Fake(os.path.join(self.tmp.name, "only"))
        copy.restore(data, ["desktop"], system)
        self.assertFalse([c for c in system.ran if c.startswith(("nmcli connection add", "pkcon", "flatpak"))])

    def test_auto_save_keeps_seven(self):
        system = Fake(self.home)
        folder = copy.auto_dir(system)
        os.makedirs(folder)
        for day in range(1, 10):
            copy.write(os.path.join(folder, f"2026-09-0{day}.json"), {"vabaxos-settings-copy": 1})
        path = copy.auto_save(system)
        copies = copy.auto_copies(system)
        self.assertEqual(len(copies), copy.AUTO_KEPT)
        self.assertEqual(copies[0], path)
        self.assertNotIn("wifi", copy.read(path))


CHILD = r'''
import importlib.machinery, importlib.util, sys
sys.path.insert(0, sys.argv[2])
loader = importlib.machinery.SourceFileLoader("settings_copy", sys.argv[1])
spec = importlib.util.spec_from_loader("settings_copy", loader)
program = importlib.util.module_from_spec(spec)
loader.exec_module(program)
from gi.repository import Gtk
Application, Window = program.window()

def walk(widget):
    yield widget
    child = widget.get_first_child()
    while child is not None:
        yield from walk(child)
        child = child.get_next_sibling()

def check(application):
    window = Window(application)
    window.present()
    print("SWITCHES:" + "|".join(r.get_title() for r in window.switches.values()), flush=True)
    print("AUTO:" + "|".join(r.get_title() for r in window.auto_rows), flush=True)
    unnamed = [type(w).__name__ for w in walk(window) if isinstance(w, Gtk.Button) and w.get_mapped()
               and not w.get_label() and not w.get_tooltip_text()
               and not any(w.get_ancestor(k) for k in (Gtk.WindowControls,))]
    print("UNNAMED:" + ",".join(unnamed), flush=True)
    window.switches["wifi"].set_active(False)
    print("CHOSEN:" + ",".join(window.chosen()), flush=True)
    application.quit()

app = Application()
app.connect("activate", check)
app.run([])
'''


def free_display():
    for number in range(180, 220):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", 8080 + number)) != 0:
                return number
    raise RuntimeError("no free Broadway display")


@unittest.skipUnless(shutil.which("gtk4-broadwayd"), "gtk4-broadwayd (libgtk-4-bin) is not installed")
class Window(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        data = os.path.join(cls.tmp.name, "data")
        os.makedirs(os.path.join(data, "vabaxos", "settings-copies"))
        copy.write(os.path.join(data, "vabaxos", "settings-copies", "2026-10-02.json"),
                   {"vabaxos-settings-copy": 1})
        display = free_display()
        cls.broadway = subprocess.Popen(["gtk4-broadwayd", f":{display}"], stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL)
        time.sleep(1)
        env = dict(os.environ, GDK_BACKEND="broadway", BROADWAY_DISPLAY=f":{display}",
                   GSETTINGS_BACKEND="memory", NO_AT_BRIDGE="1", LANGUAGE="C", LANG="C.UTF-8",
                   XDG_DATA_HOME=data, PYTHONDONTWRITEBYTECODE="1")
        result = subprocess.run([sys.executable, "-c", CHILD, PROGRAM, LIB], env=env, capture_output=True,
                                text=True, timeout=60)
        cls.out = dict(line.split(":", 1) for line in result.stdout.splitlines() if ":" in line)
        cls.err = result.stderr[-2000:]

    @classmethod
    def tearDownClass(cls):
        cls.broadway.terminate()
        cls.broadway.wait()
        cls.tmp.cleanup()

    def test_parts(self):
        self.assertEqual(self.out.get("SWITCHES"), "Voice and screen reader|Desktop settings and keys|"
                         "Wi-Fi networks, with their passwords|Programs you installed", self.err)
        self.assertEqual(self.out.get("CHOSEN"), "voice,desktop,programs", self.err)

    def test_automatic_copies(self):
        self.assertEqual(self.out.get("AUTO"), "2026-10-02", self.err)

    def test_every_button_has_a_name(self):
        self.assertEqual(self.out.get("UNNAMED"), "", self.err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
