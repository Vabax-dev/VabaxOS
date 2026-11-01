"""Printers and scanners, through CUPS and SANE (vabaxos-print).

Modern printers and scanners work without drivers (IPP Everywhere,
AirPrint, eSCL): CUPS finds network printers through mDNS, ipp-usb does
the same for USB ones, sane-airscan finds scanners. So "adding" a printer
is mostly choosing it; older ones go to GNOME Settings, Printers.

Pure parsers and command lines here, tested without CUPS (tests/print).
"""

import datetime
import gettext
import os
import re


def _(text):
    return gettext.dgettext("vabaxos-print", text)


_SCANNER = re.compile(r"^device `(.+?)' is a (.+)$")


def parse_destinations(text):
    """Printer names from lpstat -e (one a line; also the driverless ones
    CUPS found and has not set up yet)."""
    return [line.strip() for line in text.splitlines() if line.strip() and " " not in line.strip()]


def parse_default(text):
    """The default printer from lpstat -d: 'system default destination: X'."""
    if ":" in text and "no system default" not in text:
        return text.split(":", 1)[1].strip() or None
    return None


def parse_scanners(text):
    """[(device, description)] from scanimage -L."""
    found = []
    for line in text.splitlines():
        match = _SCANNER.match(line.strip())
        if match:
            found.append((match.group(1), match.group(2).strip()))
    return found


def printer_title(name):
    """A CUPS queue name as words: 'HP_LaserJet_M110w' -> 'HP LaserJet M110w'."""
    return name.replace("_", " ")


def test_page_text(now=None):
    now = now or datetime.datetime.now()
    return (_("VabaxOS test page") + "\n\n" +
            _("If you can read this, the printer works.") + "\n" +
            now.strftime("%d/%m/%Y %H:%M") + "\n")


def print_command(printer, path):
    return ["lp", "-d", printer, path]


def default_command(printer):
    """The user's default printer: no administrator needed."""
    return ["lpoptions", "-d", printer]


def scan_folder():
    try:
        import gi
        gi.require_version("GLib", "2.0")
        from gi.repository import GLib
        base = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS)
    except (ImportError, ValueError):
        base = None
    return os.path.join(base or os.path.expanduser("~"), _("Scans"))


def scan_path(folder, now=None):
    now = now or datetime.datetime.now()
    return os.path.join(folder, now.strftime(_("scan %Y-%m-%d %H-%M-%S.png")))


def scan_command(device, path, resolution=300):
    """A page in grey at 300 dpi: what text recognition reads best."""
    return ["scanimage", "-d", device, "--format=png", f"--resolution={resolution}", "--mode", "Gray",
            "-o", path]
