"""Something is wrong: the first checks, and a report to send for help.

VabaxOS never sends anything by itself and offers no remote help (Vabax,
2026-11-01): it writes a text file that the user reads and attaches to a
message or to a bug report. Personal data (user and computer name, network
names and addresses, e-mail addresses) are hidden unless the user asks
otherwise.

    findings(run)                 [(key, sentence)], the problems found
    collect(description, area,
            system_log, hide, run) the text of the report
"""

import datetime
import gettext
import getpass
import ipaddress
import os
import pwd
import re
import shutil
import socket
import subprocess

_ = gettext.translation("vabaxos-trouble", fallback=True).gettext
ngettext = gettext.translation("vabaxos-trouble", fallback=True).ngettext

REPORT = "/usr/bin/vabaxos-report"
LOW_SPACE = 1 << 30       # 1 GB free on / or on the home folder
LOW_SPACE_SHARE = 0.03    # or less than 3%


def run(command, timeout=60):
    """(exit status, output) of a command, in English (the report is read by
    the developers, and the checks compare words); 127 when it is missing."""
    env = dict(os.environ, LC_ALL="C.UTF-8", LANGUAGE="")
    try:
        done = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False,
                              errors="replace", env=env)
    except FileNotFoundError:
        return 127, ""
    except subprocess.TimeoutExpired:
        return 124, ""
    return done.returncode, done.stdout + done.stderr


def _units(output):
    return [line.split()[0] for line in output.splitlines() if line.strip()]


def free_space(path):
    try:
        usage = shutil.disk_usage(path)
    except OSError:
        return None
    return usage.free, usage.total


def findings(run=run, space=free_space, home=None):
    """The problems found by the first checks: [(key, sentence)]."""
    found = []
    code, out = run(["systemctl", "--failed", "--plain", "--no-legend", "--no-pager"])
    if code == 0 and _units(out):
        units = _units(out)
        found.append(("system-services", ngettext("A system service did not start: {units}.",
                                                  "Some system services did not start: {units}.",
                                                  len(units)).format(units=", ".join(units))))
    code, out = run(["systemctl", "--user", "--failed", "--plain", "--no-legend", "--no-pager"])
    if code == 0 and _units(out):
        units = _units(out)
        found.append(("user-services", ngettext("A service of your session did not start: {units}.",
                                                "Some services of your session did not start: {units}.",
                                                len(units)).format(units=", ".join(units))))
    code, out = run(["pactl", "list", "short", "sinks"])
    if code == 0 and not out.strip():
        found.append(("no-output", _("No sound output: the sound card is not seen.")))
    elif code == 0:
        code, out = run(["pactl", "get-sink-mute", "@DEFAULT_SINK@"])
        if code == 0 and out.split(":")[-1].strip() == "yes":
            found.append(("muted", _("The sound is muted.")))
        code, out = run(["pactl", "get-sink-volume", "@DEFAULT_SINK@"])
        levels = [int(v) for v in re.findall(r"(\d+)%", out)] if code == 0 else []
        if levels and max(levels) < 10:
            found.append(("quiet", _("The volume is very low: {level}%.").format(level=max(levels))))
    elif code != 127:
        found.append(("no-sound-server", _("The sound server of the session does not answer.")))
    code, out = run(["pgrep", "-x", "orca"])
    if code == 1:
        found.append(("orca", _("Orca, the screen reader, is not running: Super+Alt+S starts it.")))
    code, out = run(["nmcli", "-t", "-f", "STATE", "general"])
    if code == 0 and out.strip().startswith("disconnected"):
        found.append(("network", _("The computer is not connected to a network.")))
    elif code == 0 and out.strip().startswith(("connected (local only)", "connected (site only)")):
        found.append(("internet", _("The network is connected, but Internet is not reached.")))
    for name, path in ((_("the system"), "/"), (_("your personal folder"), home or os.path.expanduser("~"))):
        free = space(path)
        if free and (free[0] < LOW_SPACE or free[0] < free[1] * LOW_SPACE_SHARE):
            found.append(("space", _("Little free space for {place}: {free}.").format(place=name,
                                                                                      free=size_text(free[0]))))
            break
    code, out = run(["dpkg", "--audit"])
    if code == 0 and out.strip():
        found.append(("packages", _("Some programs were installed only in part: the report says which.")))
    return found


def size_text(size):
    if size >= 1e9:
        return f"{size / 1e9:.1f} GB".replace(".", ",")
    return f"{round(size / 1e6)} MB"


# -- personal data ------------------------------------------------------------

# Names of the live system and words of every log: never hidden.
COMMON = {"root", "localhost", "debian", "vabaxos", "user", "live", "debian live user", "lo"}
UNITS = {"service", "socket", "target", "scope", "slice", "mount", "timer", "path", "device", "swap"}
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_MAC = re.compile(r"(?<![\w:])(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}(?![\w:])")
_IPV4 = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])")
_IPV6 = re.compile(r"(?<![\w:])[0-9A-Fa-f:]*:[0-9A-Fa-f:]*:[0-9A-Fa-f:]*(?![\w:])")


def personal(run=run):
    """Words that are personal: user name, real name, computer name, the
    names of the networks (Wi-Fi names are often a family name)."""
    words = set()
    try:
        entry = pwd.getpwuid(os.getuid())
        words.add(entry.pw_name)
        words.add(entry.pw_gecos.split(",")[0].strip())
    except KeyError:
        words.add(getpass.getuser())
    words.add(socket.gethostname())
    code, out = run(["nmcli", "-t", "-f", "NAME", "connection", "show"])
    if code == 0:
        words.update(line.replace("\\:", ":").strip() for line in out.splitlines())
    return {w for w in words if len(w) >= 3 and w.lower() not in COMMON}


def _email(match):
    """An e-mail address, not a systemd unit such as user@1000.service."""
    text = match.group(0)
    return text if text.rsplit(".", 1)[-1] in UNITS else "[e-mail]"


def _address(match):
    text = match.group(0)
    try:
        address = ipaddress.ip_address(text)
    except ValueError:
        return text
    if address.is_loopback or address.is_unspecified:
        return text
    return "[address]"


def hide(text, words):
    """The text with the personal words and the addresses hidden."""
    text = _EMAIL.sub(_email, text)
    text = _MAC.sub("[hardware address]", text)
    text = _IPV4.sub(_address, text)
    text = _IPV6.sub(_address, text)
    for word in sorted(words, key=len, reverse=True):
        text = re.sub(r"(?<!\w)" + re.escape(word) + r"(?!\w)", "[personal]", text)
    return text


# -- the report -----------------------------------------------------------------

def collect(description, area, system_log=False, hide_personal=True, run=run, found=None, now=None):
    """The text of the report. system_log: the whole log of this start,
    read as root through pkexec (asks the password)."""
    now = now or datetime.datetime.now().astimezone()
    found = findings(run) if found is None else found
    parts = ["VabaxOS - {} - {}".format(_("Something is wrong"), now.isoformat(timespec="seconds")), "",
             "{}: {}".format(_("Area"), area), "", "{}:".format(_("What happened")),
             (description or "").strip() or "-", "", "{}:".format(_("First checks"))]
    parts += ["- " + sentence for _key, sentence in found] or ["- " + _("No problem found.")]
    command = ["pkexec", REPORT, "-"] if system_log else [REPORT, "-"]
    code, out = run(command, timeout=300)
    if system_log and code in (126, 127):
        code, out = run([REPORT, "-"], timeout=300)
        parts += ["", _("The system log was not added: the password was not given.")]
    parts += ["", out.rstrip()]
    code, out = run(["journalctl", "--user", "-b", "--no-pager", "-p", "warning", "-n", "1000"])
    parts += ["", "===== Session warnings =====", out.rstrip()]
    text = "\n".join(parts) + "\n"
    return hide(text, personal(run)) if hide_personal else text


def default_folder():
    try:
        from gi.repository import GLib
        folder = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS)
    except Exception:  # noqa: BLE001 - no GLib: the home folder
        folder = None
    return folder if folder and os.path.isdir(folder) else os.path.expanduser("~")


def save(text, folder=None, now=None):
    now = now or datetime.datetime.now()
    path = os.path.join(folder or default_folder(), f"vabaxos-report-{now:%Y%m%d-%H%M%S}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path
