"""The system restore in the text console, read by Speakup (ADR-0027).

    sudo vabaxos-restore --console     (the command "ripristino")

For the computer whose desktop does not start: from the VabaxOS USB
stick, recovery mode (R), or from the text console of the installed
system (Ctrl+Alt+F3). Short lines, one question at a time, answers with
numbers: easy to follow with the voice of the console.

From the USB stick the copies are on the disk of the computer: an
encrypted disk is opened first (its password is asked), then each disk is
looked at with Timeshift.
"""

import json
import os
import subprocess

from . import _, live_system

HELPER = os.environ.get("VABAXOS_RESTORE_HELPER", "/usr/lib/vabaxos/restore/helper")


def run(command, **kwargs):
    return subprocess.run(command, capture_output=True, text=True, check=False, **kwargs)


def block_devices(runner=run):
    """[(path, fstype)] of the partitions and volumes, from lsblk."""
    out = runner(["lsblk", "-rpno", "NAME,FSTYPE"]).stdout
    found = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 2:
            found.append((parts[0], parts[1]))
    return found


def candidates(devices):
    """The volumes that can hold a system and its copies."""
    return [path for path, fstype in devices if fstype in ("ext4", "ext3", "btrfs", "xfs")]


def encrypted(devices):
    return [path for path, fstype in devices if fstype == "crypto_LUKS"]


def copies_on(device, runner=run):
    result = runner([HELPER, "list", "--device", device])
    if result.returncode != 0:
        return []
    try:
        return json.loads(result.stdout)
    except ValueError:
        return []


def ask(prompt, read=input, write=print):
    write(prompt)
    try:
        return read("> ").strip()
    except EOFError:
        return ""


def choose(items, read=input, write=print):
    """Says each item with its number; returns the index chosen, or None."""
    for number, item in enumerate(items, start=1):
        write(f"{number}. {item}")
    answer = ask(_("Type the number and press Enter. 0 to go out."), read, write)
    if answer.isdigit() and 1 <= int(answer) <= len(items):
        return int(answer) - 1
    return None


def open_encrypted(runner=run, write=print, opener=subprocess.run):
    """Opens the encrypted disks of the computer: cryptsetup asks the
    password itself, on the console. Then the volumes inside (LVM)."""
    locked = encrypted(block_devices(runner))
    for number, path in enumerate(locked, start=1):
        write(_("The disk {disk} is encrypted. Type its password, then press Enter.").format(disk=path))
        opener(["cryptsetup", "open", path, f"vabaxos-restore-{number}"], check=False)
    if locked:
        runner(["vgchange", "-ay"])


def main(read=input, write=print, runner=run):
    write(_("VabaxOS system restore."))
    if os.geteuid() != 0:
        write(_("It needs the administrator: write sudo ripristino, then press Enter."))
        return 1
    if live_system():
        open_encrypted(runner, write)
        found = [(device, copies_on(device, runner)) for device in candidates(block_devices(runner))]
        found = [(device, items) for device, items in found if items]
    else:
        items = _installed_copies(runner)
        found = [("", items)] if items else []
    if not found:
        write(_("No copy of the system was found."))
        return 1
    device, items = found[0]
    if len(found) > 1:
        write(_("Copies were found on more disks. Which one?"))
        index = choose([d for d, _i in found], read, write)
        if index is None:
            return 0
        device, items = found[index]
    write(_("Copies of the system, the newest last:"))
    index = choose([item["title"] for item in items], read, write)
    if index is None:
        write(_("Nothing changed."))
        return 0
    item = items[index]
    write(_("The system goes back to: {copy}.").format(copy=item["title"]))
    write(_("Documents and personal folders do not change. Then the computer restarts."))
    answer = ask(_("Type yes and press Enter to restore, anything else to go out."), read, write)
    if answer.lower() not in ("si", "sì", "yes", "s", "y"):
        write(_("Nothing changed."))
        return 0
    write(_("Restoring. It takes some minutes; do not turn the computer off."))
    command = [HELPER, "restore", item["name"]] + (["--device", device] if device else [])
    result = runner(command)
    if result.returncode != 0:
        write(_("The restore failed."))
        return 1
    return 0


def _installed_copies(runner):
    result = runner([HELPER, "list"])
    if result.returncode != 0:
        return []
    try:
        return json.loads(result.stdout)
    except ValueError:
        return []
