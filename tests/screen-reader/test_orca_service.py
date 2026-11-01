#!/usr/bin/env python3
"""Tests for vabaxos_screen_reader.store.OrcaService against a made-up
Orca 51 on a private D-Bus: the modules are found by introspection, a
setting is written and read back as a D-Bus property of the right type,
the profile is changed, and messages reach PresentMessage.

    python3 tests/screen-reader/test_orca_service.py
"""

import os
import shutil
import subprocess
import sys
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LIBRARY = os.path.join(REPO, "packages", "vabaxos-screen-reader", "root", "usr", "lib", "python3", "dist-packages")

# Orca 51's D-Bus layout, as dbus_service.OrcaRemoteController publishes it.
CHILD = r'''
import sys, threading
sys.path.insert(0, sys.argv[1])
from gi.repository import Gio, GLib

SERVICE = """<node><interface name="org.gnome.Orca1.Service">
  <method name="PresentMessage"><arg type="s" direction="in"/><arg type="b" direction="out"/></method>
</interface></node>"""
SPEECH = """<node><interface name="org.gnome.Orca1.SpeechManager">
  <property name="Rate" type="u" access="readwrite"/>
  <property name="SpeechIsEnabled" type="b" access="readwrite"/>
  <property name="CurrentServer" type="s" access="read"/>
</interface></node>"""
TYPING = """<node><interface name="org.gnome.Orca1.TypingEchoPresenter">
  <property name="KeyEchoEnabled" type="b" access="readwrite"/>
</interface></node>"""
PROFILES = """<node><interface name="org.gnome.Orca1.ProfileManager">
  <property name="ActiveProfile" type="s" access="readwrite"/>
</interface></node>"""
state = {"Rate": GLib.Variant("u", 50), "SpeechIsEnabled": GLib.Variant("b", True),
         "CurrentServer": GLib.Variant("s", "speechd"), "KeyEchoEnabled": GLib.Variant("b", True),
         "ActiveProfile": GLib.Variant("s", "default")}
said = []

def method(conn, sender, path, iface, name, params, invocation):
    said.append(params.unpack()[0])
    invocation.return_value(GLib.Variant("(b)", (True,)))

def get(conn, sender, path, iface, name):
    return state[name]

def put(conn, sender, path, iface, name, value):
    state[name] = value
    return True

conn = Gio.bus_get_sync(Gio.BusType.SESSION, None)
base = "/org/gnome/Orca1/Service"
conn.register_object(base, Gio.DBusNodeInfo.new_for_xml(SERVICE).interfaces[0], method, None, None)
for name, xml in (("SpeechManager", SPEECH), ("TypingEchoPresenter", TYPING), ("ProfileManager", PROFILES)):
    conn.register_object(f"{base}/{name}", Gio.DBusNodeInfo.new_for_xml(xml).interfaces[0], None, get, put)
Gio.bus_own_name_on_connection(conn, "org.gnome.Orca1.Service", Gio.BusNameOwnerFlags.NONE, None, None)
loop = GLib.MainLoop()

def client():
    from vabaxos_screen_reader import store
    orca = store.OrcaService()
    setters = orca.setters()
    print("SETTERS:" + ",".join(sorted(setters)), flush=True)
    print("RATE-TYPE:" + setters["Rate"][0][2], flush=True)
    print("SET:" + str(orca.set_live("voice", "rate", 63, "voices/default")), flush=True)
    print("GET:" + str(orca.get_property("Rate", "Speech")), flush=True)
    print("ECHO:" + str(orca.set_live("typing-echo", "key-echo", False)), flush=True)
    print("BRAILLE:" + str(orca.set_live("braille", "verbosity-level", 1)), flush=True)
    print("PROFILE:" + str(orca.set_profile("studio")) + " " + state["ActiveProfile"].unpack(), flush=True)
    print("PRESENT:" + str(orca.present("Ciao")), flush=True)
    GLib.idle_add(loop.quit)

GLib.timeout_add(300, lambda: threading.Thread(target=client, daemon=True).start() and False)
GLib.timeout_add(20000, loop.quit)
loop.run()
print("SAID:" + "|".join(said), flush=True)
print("ECHOSTATE:" + str(state["KeyEchoEnabled"].unpack()), flush=True)
'''


@unittest.skipUnless(shutil.which("dbus-run-session"), "dbus-run-session is not installed")
class OrcaServiceTest(unittest.TestCase):

    def test_orca_51_service(self):
        result = subprocess.run(["dbus-run-session", "--", sys.executable, "-c", CHILD, LIBRARY],
                                capture_output=True, text=True, timeout=60, check=False)
        out = dict(line.split(":", 1) for line in result.stdout.splitlines() if ":" in line)
        err = result.stderr[-2000:]
        self.assertEqual(out.get("SETTERS"), "ActiveProfile,KeyEchoEnabled,Rate,SpeechIsEnabled", err)
        self.assertEqual(out.get("RATE-TYPE"), "u", err)
        self.assertEqual(out.get("SET"), "True", err)
        self.assertEqual(out.get("GET"), "63", err)
        self.assertEqual(out.get("ECHO"), "True", err)
        self.assertEqual(out.get("ECHOSTATE"), "False", err)
        self.assertEqual(out.get("BRAILLE"), "False", err)
        self.assertEqual(out.get("PROFILE"), "True studio", err)
        self.assertEqual(out.get("PRESENT"), "(True,)", err)
        self.assertEqual(out.get("SAID"), "Ciao", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
