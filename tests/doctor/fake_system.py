"""A made-up computer for the tests of vabaxos-doctor: command outputs,
files and disks come from dictionaries, and every command run is kept."""

import json


class FakeSystem:

    def __init__(self, outputs=None, files=None, disks=None, home="/home/user"):
        # A healthy computer, changed by each test.
        self.outputs = {
            "wpctl get-volume @DEFAULT_AUDIO_SINK@": "Volume: 0.70\n",
            "spd-say -O": "OUTPUT MODULES\nespeak-ng\ndummy\n",
            "gsettings get org.gnome.desktop.a11y.applications screen-reader-enabled": "true\n",
            "pgrep -u {uid} -x orca": "1234\n",
            "systemctl is-active espeakup.service": "active\n",
            "systemctl is-active triggerhappy.service vabaxos-voice-rescue.path": "active\nactive\n",
            "nmcli -t -f CONNECTIVITY general": "full\n",
            "systemctl is-active ufw.service": "active\n",
            "systemctl --failed --no-legend --plain": "",
            "systemctl --user --failed --no-legend --plain": "",
        }
        self.outputs.update(outputs or {})
        self.files = {
            "/proc/asound/cards": " 0 [Intel          ]: HDA-Intel - HDA Intel PCH\n",
            "/proc/meminfo": "MemTotal: 8000000 kB\nMemAvailable: 4096000 kB\n",
            "/home/user/.local/share/orca/user-settings.conf": json.dumps(
                {"general": {"enableSpeech": True}, "profiles": {"default": {}}}),
        }
        self.files.update(files or {})
        self.disks = {"/": (50000, 100000)}
        self.disks.update(disks or {})
        self._home = home
        self.ran = []

    def _key(self, command):
        import os
        return " ".join(command).replace(str(os.getuid()), "{uid}")

    def output(self, command, timeout=5):
        key = self._key(command)
        self.ran.append(key)
        return self.outputs.get(key)

    def run(self, command, timeout=60):
        key = self._key(command)
        self.ran.append(key)
        return self.outputs.get(key, "") is not None

    def read(self, path):
        return self.files.get(path)

    def exists(self, path):
        return path in self.files

    def disk(self, path):
        if path not in self.disks:
            return self.disks["/"]
        return self.disks[path]

    def home(self):
        return self._home
