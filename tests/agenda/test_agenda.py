#!/usr/bin/env python3
"""Tests for vabaxos-agenda: appointments in sentences, the days, the
summary, a new appointment from a sentence, the announcements 15 minutes
before; a real Evolution Data Server on a private D-Bus (when installed);
and the window on Broadway with made-up calendars.

    python3 tests/agenda/test_agenda.py
"""

import datetime
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ROOT = os.path.join(REPO, "packages", "vabaxos-agenda", "root")
LIB = os.path.join(ROOT, "usr", "lib", "python3", "dist-packages")
REMINDERS = os.path.join(REPO, "packages", "vabaxos-reminders", "root", "usr", "lib", "python3", "dist-packages")
PROGRAM = os.path.join(ROOT, "usr", "bin", "vabaxos-agenda")
sys.path[:0] = [LIB, REMINDERS]

import vabaxos_agenda as va  # noqa: E402

ZONE = datetime.timezone(datetime.timedelta(hours=1))
NOW = datetime.datetime(2026, 11, 2, 9, 0, tzinfo=ZONE)          # a Monday


def event(title, day, hour, minutes=60, **kwargs):
    start = (NOW + datetime.timedelta(days=day)).replace(hour=hour, minute=0)
    return va.Event(title, start, start + datetime.timedelta(minutes=minutes), **kwargs)


class SentencesTest(unittest.TestCase):

    def test_describe(self):
        self.assertEqual(va.describe(event("Dentista", 1, 10, location="Via Roma 3", calendar="Personale"), NOW),
                         "Tomorrow at 10:00, Dentista, one hour, Via Roma 3, Personale")
        self.assertEqual(va.describe(event("Riunione", 0, 15, 90), NOW), "Today at 15:00, Riunione, 1 h 30 min")
        self.assertEqual(va.describe(event("Caffè", 3, 8, 20), NOW), "Thursday at 08:00, Caffè, 20 minutes")
        whole = va.Event("Compleanno di Anna", datetime.datetime(2026, 11, 20, tzinfo=ZONE),
                         datetime.datetime(2026, 11, 21, tzinfo=ZONE), all_day=True)
        self.assertEqual(va.describe(whole, NOW), "Friday 20 November, all day, Compleanno di Anna")
        self.assertEqual(va.describe(whole, NOW, with_day=False), "All day, Compleanno di Anna")

    def test_days_and_summary(self):
        events = [event("B", 1, 9), event("A", 0, 11), event("C", 1, 8), event("D", 5, 8)]
        groups = va.group_by_day(events, NOW)
        self.assertEqual([(label, [e.title for e in es]) for label, es in groups],
                         [("Today", ["A"]), ("Tomorrow", ["C", "B"]), ("Saturday", ["D"])])
        self.assertEqual(va.summary(events, NOW), "3 appointments. Today at 11:00, A, one hour. Tomorrow at "
                                                  "08:00, C, one hour. Tomorrow at 09:00, B, one hour.")
        self.assertEqual(va.summary([event("D", 5, 8)], NOW), "No appointments today and tomorrow.")

    def test_from_sentence(self):
        new = va.from_sentence("domani alle 10:30 dentista", NOW, "Via Roma 3")
        self.assertEqual((new.title, new.start.hour, new.start.minute, new.location), ("Dentista", 10, 30,
                                                                                        "Via Roma 3"))
        self.assertEqual(new.end - new.start, datetime.timedelta(hours=1))
        self.assertIsNone(va.from_sentence("dentista", NOW))

    def test_announcements(self):
        soon = event("Dentista", 0, 9, location="Via Roma 3")
        soon.start = NOW + datetime.timedelta(minutes=15)
        later = event("Pranzo", 0, 13)
        whole = va.Event("Festa", NOW, NOW + datetime.timedelta(days=1), all_day=True)
        said = set()
        self.assertEqual([s for _e, s in va.due_announcements([soon, later, whole], NOW, said)],
                         ["In 15 minutes: Dentista, Via Roma 3."])
        self.assertEqual(va.due_announcements([soon], NOW, said), [], "said once")
        now_event = event("Chiamata", 0, 9, 30)
        now_event.start = NOW + datetime.timedelta(seconds=20)
        self.assertEqual(va.due_announcements([now_event], NOW, said)[0][1], "Now: Chiamata.")


EDS_CHILD = r'''
import sys, datetime
sys.path[:0] = sys.argv[1:3]
import vabaxos_agenda as va
from vabaxos_agenda.calendars import Calendars
now = datetime.datetime.now().astimezone()
cals = Calendars()
print("NAMES:" + "|".join(n for _u, n in cals.names()))
cals.add(va.from_sentence("domani alle 10:30 dentista", now, "Via Roma 3"))
events = cals.events(7)
print("EVENTS:" + "|".join(va.describe(e, now) for e in events))
cals.remove(events[0])
print("AFTER:" + str(len(cals.events(7))), flush=True)
import os
os._exit(0)      # the clients of Evolution Data Server would keep the exit waiting for a minute
'''


def eds_ready():
    if not shutil.which("dbus-run-session"):
        return False
    try:
        import gi
        gi.require_version("ECal", "2.0")
        gi.require_version("EDataServer", "1.2")
        return True
    except (ImportError, ValueError):
        return False


@unittest.skipUnless(eds_ready(), "Evolution Data Server or dbus-run-session is not installed")
class EvolutionDataServerTest(unittest.TestCase):

    def test_add_read_remove(self):
        home = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, home)
        env = dict(os.environ, HOME=home, XDG_DATA_HOME=os.path.join(home, "data"),
                   XDG_CONFIG_HOME=os.path.join(home, "config"), XDG_CACHE_HOME=os.path.join(home, "cache"),
                   LANGUAGE="C", GSETTINGS_BACKEND="memory")
        result = subprocess.run(["dbus-run-session", "--", sys.executable, "-c", EDS_CHILD, LIB, REMINDERS],
                                env=env, capture_output=True, text=True, timeout=120, check=False)
        out = dict(line.split(":", 1) for line in result.stdout.splitlines() if ":" in line)
        err = result.stderr[-2000:]
        self.assertIn("Personal", out.get("NAMES", ""), err)
        self.assertRegex(out.get("EVENTS", ""), r"^Tomorrow at 10:30, Dentista, one hour, Via Roma 3, Personal$",
                         err)
        self.assertEqual(out.get("AFTER"), "0", err)


CHILD = r'''
import importlib.machinery, importlib.util, sys, datetime
loader = importlib.machinery.SourceFileLoader("agendaprog", sys.argv[1])
spec = importlib.util.spec_from_loader("agendaprog", loader)
program = importlib.util.module_from_spec(spec)
loader.exec_module(program)
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk
import vabaxos_agenda as va

ZONE = datetime.timezone(datetime.timedelta(hours=1))
NOW = datetime.datetime(2026, 11, 2, 9, 0, tzinfo=ZONE)
said, opened = [], []

class FakeCalendars:
    def __init__(self):
        start = NOW + datetime.timedelta(days=1, hours=1)
        self.list = [va.Event("Dentista", start, start + datetime.timedelta(hours=1), "Via Roma 3", "Personale",
                              uid="1", source="local")]
        self.removed = []
    def names(self): return [("local", "Personale"), ("google", "Google")]
    def default_uid(self): return "local"
    def events(self, days): return list(self.list)
    def add(self, event, uid):
        event.uid, event.source, event.calendar = "2", uid, dict(self.names())[uid]
        self.list.append(event)
        return event
    def remove(self, event):
        self.removed.append(event.title)
        self.list = [e for e in self.list if e.uid != event.uid]

App, Window = program.window_classes(speak=said.append, factory=FakeCalendars,
                                     accounts=lambda: opened.append(1), clock=lambda: NOW)
app = Adw.Application(application_id="org.vabaxos.AgendaTest")

def check(app):
    window = Window(app)
    window.present()
    def step1():
        print("START:" + said[-1] + " / " + "|".join(r.get_title() + " - " + r.get_subtitle()
                                                    for _e, r in window.rows), flush=True)
        print("GROUPS:" + "|".join(g.get_title() for g in window.groups), flush=True)
        window.confirm(va.from_sentence("dopodomani alle 18 riunione", NOW), "google")
        print("CONFIRM:" + window.dialog.get_body(), flush=True)
        window.dialog.emit("response", "yes")
        GLib.timeout_add(400, step2)
        return False
    def step2():
        print("ADDED:" + said[-2], flush=True)
        window.remove(window.cals.list[0])
        GLib.timeout_add(400, step3)
        return False
    def step3():
        print("REMOVED:" + said[-2] + " " + repr(window.cals.removed), flush=True)
        app.quit()
        return False
    GLib.timeout_add(400, step1)

app.connect("activate", check)
app.hold()
app.run([])
'''


def free_display():
    for number in range(60, 100):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", 8080 + number)) != 0:
                return number
    raise RuntimeError("no free Broadway display")


@unittest.skipUnless(shutil.which("gtk4-broadwayd"), "gtk4-broadwayd (libgtk-4-bin) is not installed")
class WindowTest(unittest.TestCase):

    def test_window(self):
        display = free_display()
        broadway = subprocess.Popen(["gtk4-broadwayd", f":{display}"], stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
        time.sleep(1)
        env = dict(os.environ, GDK_BACKEND="broadway", BROADWAY_DISPLAY=f":{display}", GSETTINGS_BACKEND="memory",
                   NO_AT_BRIDGE="1", PYTHONPATH=os.pathsep.join([LIB, REMINDERS]), LANGUAGE="C", LANG="C.UTF-8",
                   PYTHONDONTWRITEBYTECODE="1")
        try:
            result = subprocess.run([sys.executable, "-c", CHILD, PROGRAM], env=env, capture_output=True, text=True,
                                    timeout=60, check=False)
        finally:
            broadway.terminate()
            broadway.wait()
        out = dict(line.split(":", 1) for line in result.stdout.splitlines() if ":" in line)
        err = result.stderr[-3000:]
        self.assertEqual(out.get("START"), "1 appointment in the next two weeks. Ctrl+N adds one. / 10:00, Dentista - "
                                           "one hour, Via Roma 3, Personale", err)
        self.assertEqual(out.get("GROUPS"), "Tomorrow", err)
        self.assertEqual(out.get("CONFIRM"), "The day after tomorrow at 18:00, Riunione, one hour.", err)
        self.assertEqual(out.get("ADDED"), "Added: The day after tomorrow at 18:00, Riunione, one hour, Google.", err)
        self.assertEqual(out.get("REMOVED"), "Deleted: Dentista. ['Dentista']", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
