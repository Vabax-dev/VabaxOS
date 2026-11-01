"""System restore of VabaxOS (ADR-0027): Timeshift copies of the system
(rsync mode, on ext4), made before every installation of packages and
once a week, restored from a window, from the text console, or from the
recovery mode of the VabaxOS USB stick.

The functions here are pure or take the commands to run, so they are
tested without Timeshift and without root (tests/restore).
"""

import gettext
import json
import os
import re
import shutil
import subprocess


def _(text):
    return gettext.dgettext("vabaxos-restore", text)


CONFIG = os.environ.get("VABAXOS_TIMESHIFT_CONFIG", "/etc/timeshift/timeshift.json")
# Copies kept: the newest made by hand or before installing (tag O), and
# the newest weekly ones (tag W).
KEEP = {"O": 3, "W": 2}
# No copy with less free space than this, in percent of the disk.
MIN_FREE_PERCENT = 10
# One copy at most in this time before installations: one update made of
# many dpkg runs gets one copy.
MIN_INTERVAL = 3600

_ROW = re.compile(r"^\s*(\d+)\s+>\s+(\d{4}-\d\d-\d\d_\d\d-\d\d-\d\d)\s+([A-Z]+)\s*(.*?)\s*$")


class Copy:
    """One Timeshift copy (a "snapshot")."""

    def __init__(self, name, tags, comment):
        self.name = name
        self.tags = tags
        self.comment = comment

    def __repr__(self):
        return f"Copy({self.name}, {self.tags}, {self.comment!r})"

    def when(self):
        """'2026-11-01_10-00-01' -> ('2026-11-01', '10:00')."""
        day, time = self.name.split("_")
        return day, time[:5].replace("-", ":")

    def title(self):
        day, time = self.when()
        year, month, date = day.split("-")
        text = _("{day}/{month}/{year} at {time}").format(day=date, month=month, year=year, time=time)
        return f"{text}: {self.description()}"

    def description(self):
        if self.comment:
            return self.comment
        if "W" in self.tags:
            return _("weekly copy")
        return _("copy")


def parse_list(text):
    """The copies in the output of timeshift --list, oldest first."""
    copies = []
    for line in text.splitlines():
        match = _ROW.match(line)
        if match:
            copies.append(Copy(match.group(2), match.group(3), match.group(4)))
    return copies


def to_delete(copies, keep=KEEP):
    """The copies beyond those to keep, for each tag; a copy with more tags
    stays if one of them keeps it."""
    kept = set()
    for tag, count in keep.items():
        mine = [c for c in copies if tag in c.tags]
        kept.update(c.name for c in mine[-count:] if count)
    return [c for c in copies if c.name not in kept]


def config(uuid, current=None):
    """Timeshift's configuration for VabaxOS: rsync on the disk of the
    system, no schedule of its own (VabaxOS has its timer), the personal
    folders left out: a restore never touches documents."""
    data = dict(current or {})
    data.update({
        "backup_device_uuid": uuid,
        "parent_device_uuid": "",
        "do_first_run": "false",
        "btrfs_mode": "false",
        "include_btrfs_home_for_backup": "false",
        "include_btrfs_home_for_restore": "false",
        "stop_cron_emails": "true",
        "schedule_monthly": "false",
        "schedule_weekly": "false",
        "schedule_daily": "false",
        "schedule_hourly": "false",
        "schedule_boot": "false",
    })
    excludes = list(data.get("exclude", []))
    for pattern in ("/home/**", "/root/**", "/var/cache/apt/archives/*.deb", "/swapfile"):
        if pattern not in excludes:
            excludes.append(pattern)
    data["exclude"] = excludes
    data.setdefault("exclude-apps", [])
    return data


def root_uuid(run=subprocess.run):
    result = run(["findmnt", "-n", "-o", "UUID", "/"], capture_output=True, text=True, check=False)
    return result.stdout.strip()


def ensure_config(path=CONFIG, run=subprocess.run):
    """Writes the configuration if Timeshift has none or none for this disk."""
    try:
        with open(path, encoding="utf-8") as f:
            current = json.load(f)
    except (OSError, ValueError):
        current = {}
    uuid = root_uuid(run)
    if not uuid:
        raise RuntimeError(_("the disk of the system was not found"))
    if current.get("backup_device_uuid") == uuid and current.get("btrfs_mode") == "false":
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config(uuid, current), f, indent=2)
    return True


def live_system(cmdline_path="/proc/cmdline"):
    try:
        with open(cmdline_path, encoding="utf-8") as f:
            words = f.read().split()
    except OSError:
        return False
    return "boot=live" in words


def free_percent(path="/"):
    usage = shutil.disk_usage(path)
    return 100 * usage.free / usage.total if usage.total else 0


def before_install_comment(packages):
    """The words for a copy made before installing packages."""
    names = sorted({os.path.basename(p).split("_")[0] for p in packages if p.strip()})
    if not names:
        return _("Before installing")
    count = len(names)
    if count == 1:
        return _("Before installing {name}").format(name=names[0])
    shown = ", ".join(names[:3]) + ("…" if count > 3 else "")
    return _("Before installing {count} packages: {names}").format(count=count, names=shown)


def should_copy_before_install(last_copy_time, now, live, free):
    """Whether the APT hook makes a copy now: not in the live system, not
    twice in the same hour, not on an almost full disk."""
    if live:
        return False, "live"
    if free < MIN_FREE_PERCENT:
        return False, "space"
    if last_copy_time and now - last_copy_time < MIN_INTERVAL:
        return False, "recent"
    return True, ""
