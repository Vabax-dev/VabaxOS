"""What was installed, updated and removed: the history of APT
(/var/log/apt/history.log, readable by every user), newest first."""

import gzip
import os
import re

LOG = "/var/log/apt/history.log"
_PACKAGE = re.compile(r"([^\s,()]+) \(([^)]*)\)")
ACTIONS = ("Install", "Upgrade", "Remove", "Purge", "Downgrade")


class Entry:

    def __init__(self, date, command, changes):
        self.date = date
        self.command = command
        self.changes = changes  # {"Upgrade": ["openssl", ...], ...}

    def total(self, action):
        return len(self.changes.get(action, []))


def parse(text):
    entries = []
    for block in re.split(r"\n\s*\n", text.strip()):
        fields = {}
        for line in block.splitlines():
            if ": " in line:
                key, value = line.split(": ", 1)
                fields[key.strip()] = value.strip()
        if "Start-Date" not in fields:
            continue
        changes = {}
        for action in ACTIONS:
            if action in fields:
                changes[action] = [name.split(":", 1)[0] for name, _v in _PACKAGE.findall(fields[action])]
        entries.append(Entry(fields["Start-Date"], fields.get("Commandline", ""), changes))
    return entries


def read(path=LOG, limit=30):
    """The newest entries, also from the rotated logs (history.log.1.gz...)."""
    texts = []
    for i in range(0, 4):
        name = path if i == 0 else f"{path}.{i}.gz"
        try:
            if name.endswith(".gz"):
                with gzip.open(name, "rt", encoding="utf-8", errors="replace") as f:
                    texts.append(f.read())
            elif os.path.exists(name):
                with open(name, encoding="utf-8", errors="replace") as f:
                    texts.append(f.read())
        except OSError:
            continue
        if sum(len(parse(t)) for t in texts) >= limit:
            break
    # history.log is the newest file; inside a file the newest entry is last.
    entries = []
    for text in texts:
        entries += reversed(parse(text))
    return entries[:limit]
