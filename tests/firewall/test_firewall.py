#!/usr/bin/env python3
"""Tests for vabaxos-firewall (ADR-0021): the two zones, the library with
made-up firewalld and NetworkManager, the command, and the group of the
setup on a hidden Broadway display. No firewall is touched.

    python3 tests/firewall/test_firewall.py
"""

import contextlib
import importlib.machinery
import importlib.util
import io
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import xml.dom.minidom

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ROOT = os.path.join(REPO, "packages", "vabaxos-firewall", "root")
LIB = os.path.join(ROOT, "usr", "lib", "python3", "dist-packages")
PROGRAM = os.path.join(ROOT, "usr", "bin", "vabaxos-firewall")
ZONES = os.path.join(ROOT, "usr", "lib", "firewalld", "zones")
sys.path.insert(0, LIB)

import vabaxos_firewall as fw  # noqa: E402

# Services of firewalld used by the zones and the switches: all present in
# firewalld for years (config/services of firewalld, checked 2026-11-01).
KNOWN_SERVICES = {"dhcpv6-client", "mdns", "llmnr", "upnp-client", "ipp-client", "samba-client",
                  "kdeconnect", "samba", "rdp", "ssh"}


def zone_services(name):
    dom = xml.dom.minidom.parse(os.path.join(ZONES, name + ".xml"))
    return [s.getAttribute("name") for s in dom.getElementsByTagName("service")]


class FakeFirewalld:
    """Answers the D-Bus calls of vabaxos_firewall.Firewall, as firewalld."""

    def __init__(self, running=True):
        self.running = running
        self.runtime = {fw.PRIVATE: zone_services(fw.PRIVATE), fw.PUBLIC: zone_services(fw.PUBLIC)}
        self.permanent = {zone: list(services) for zone, services in self.runtime.items()}
        self.calls = []

    def call_sync(self, name, path, interface, method, args, reply, flags, timeout, cancellable):
        from gi.repository import GLib, Gio
        if not self.running:
            raise GLib.Error("org.freedesktop.DBus.Error.ServiceUnknown")
        assert flags & Gio.DBusCallFlags.ALLOW_INTERACTIVE_AUTHORIZATION, "polkit must be able to ask"
        values = args.unpack() if args is not None else ()
        self.calls.append((interface.rsplit(".", 1)[-1], method, values))
        if method == "getDefaultZone":
            return GLib.Variant("(s)", (fw.PRIVATE,))
        if method == "getZoneByName":
            return GLib.Variant("(o)", (f"/org/fedoraproject/FirewallD1/config/zone/{values[0].replace('-', '_')}",))
        if interface.endswith(".config.zone"):
            zone = fw.PRIVATE if path.endswith("private") else fw.PUBLIC
            services = self.permanent[zone]
            if method == "getServices":
                return GLib.Variant("(as)", (services,))
            if method == "addService":
                services.append(values[0])
            if method == "removeService":
                services.remove(values[0])
            return None
        if method == "getServices":
            return GLib.Variant("(as)", (self.runtime[values[0]],))
        if method == "addService":
            self.runtime[values[0]].append(values[1])
            return GLib.Variant("(s)", (values[0],))
        if method == "removeService":
            self.runtime[values[0]].remove(values[1])
            return GLib.Variant("(s)", (values[0],))
        raise AssertionError(f"unexpected call {method}")


class FakeSetting:
    def __init__(self, name, zone, kind="802-11-wireless"):
        self.name, self.zone, self.kind = name, zone, kind

    def get_id(self):
        return self.name

    def get_zone(self):
        return self.zone

    def get_connection_type(self):
        return self.kind

    def set_property(self, key, value):
        assert key == "zone"
        self.zone = value


class FakeConnection:
    def __init__(self, setting, fail=False):
        self.setting, self.fail, self.saved = setting, fail, False

    def get_setting_connection(self):
        return self.setting

    def commit_changes_async(self, save, cancellable, callback):
        self.saved = save
        callback(self, None)

    def commit_changes_finish(self, result):
        if self.fail:
            raise RuntimeError("not authorized")
        return True


class FakeActive:
    def __init__(self, connection):
        self.connection = connection

    def get_connection(self):
        return self.connection


class FakeClient:
    def __init__(self, connections):
        self.connections = connections

    def get_active_connections(self):
        return [FakeActive(c) for c in self.connections]


def networks(*settings):
    return fw.Networks(FakeClient([FakeConnection(s) for s in settings]))


class ZoneTest(unittest.TestCase):

    def test_zones_are_valid_and_use_known_services(self):
        for zone in (fw.PRIVATE, fw.PUBLIC):
            services = zone_services(zone)
            self.assertTrue(set(services) <= KNOWN_SERVICES, services)
            self.assertIn("dhcpv6-client", services)
        self.assertTrue(set(fw.APP_SERVICES) <= KNOWN_SERVICES)

    def test_private_finds_things_public_lets_nothing_in(self):
        private = zone_services(fw.PRIVATE)
        for service in ("mdns", "samba-client", "kdeconnect", "ipp-client"):
            self.assertIn(service, private)
        self.assertEqual(zone_services(fw.PUBLIC), ["dhcpv6-client"])
        # Nothing that serves others is open by default, as in Windows.
        for service in fw.APP_SERVICES:
            self.assertNotIn(service, private)


class LibraryTest(unittest.TestCase):

    def test_kinds(self):
        self.assertEqual(fw.kind(""), "private")
        self.assertEqual(fw.kind("", fw.PUBLIC), "public")
        self.assertEqual(fw.kind("public"), "public")
        self.assertEqual(fw.kind("home"), "private")
        self.assertEqual(fw.zone_for("public"), fw.PUBLIC)
        self.assertEqual(fw.zone_for("private"), fw.PRIVATE)

    def test_describe(self):
        self.assertEqual(fw.describe(False, []), "Firewall off.")
        self.assertEqual(fw.describe(True, [("Casa", "private"), ("Bar", "public")]),
                         "Firewall on. Casa is a private network, Bar is a public network.")

    def test_allow_and_block_now_and_for_good(self):
        bus = FakeFirewalld()
        firewall = fw.Firewall(bus)
        self.assertTrue(firewall.running())
        self.assertFalse(firewall.allowed("samba"))
        firewall.set_allowed("samba", True)
        self.assertIn("samba", bus.runtime[fw.PRIVATE])
        self.assertIn("samba", bus.permanent[fw.PRIVATE])
        self.assertNotIn("samba", bus.runtime[fw.PUBLIC])
        firewall.set_allowed("samba", True)  # again: nothing twice
        self.assertEqual(bus.runtime[fw.PRIVATE].count("samba"), 1)
        firewall.set_allowed("samba", False)
        self.assertNotIn("samba", bus.runtime[fw.PRIVATE] + bus.permanent[fw.PRIVATE])

    def test_not_running(self):
        self.assertFalse(fw.Firewall(FakeFirewalld(running=False)).running())

    def test_networks_and_their_kind(self):
        found = networks(FakeSetting("Casa", ""), FakeSetting("Bar", "vabaxos-public"),
                         FakeSetting("lo", "", "loopback"))
        self.assertEqual(found.kinds(), [("Casa", "private"), ("Bar", "public")])
        connection = found.active()[0][0]
        results = []
        found.set_kind(connection, "public", lambda ok, error: results.append((ok, error)))
        self.assertEqual(results, [(True, None)])
        self.assertEqual(connection.setting.zone, fw.PUBLIC)
        self.assertTrue(connection.saved)

    def test_refused_change_is_told(self):
        connection = FakeConnection(FakeSetting("Casa", ""), fail=True)
        results = []
        fw.Networks(FakeClient([connection])).set_kind(connection, "public",
                                                         lambda ok, error: results.append(ok))
        self.assertEqual(results, [False])


def load_program():
    loader = importlib.machinery.SourceFileLoader("vabaxos_firewall_program", PROGRAM)
    spec = importlib.util.spec_from_loader("vabaxos_firewall_program", loader)
    program = importlib.util.module_from_spec(spec)
    loader.exec_module(program)
    return program


class CommandTest(unittest.TestCase):

    def run_program(self, argv, bus=None, nets=None):
        program = load_program()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = program.main(argv, fw.Firewall(bus or FakeFirewalld()), nets or networks(FakeSetting("Casa", "")))
        return code, out.getvalue().strip()

    def test_status(self):
        self.assertEqual(self.run_program([]), (0, "Firewall on. Casa is a private network."))
        self.assertEqual(self.run_program(["--short"]), (0, "Firewall on."))
        self.assertEqual(self.run_program(["--short"], FakeFirewalld(running=False)), (0, "Firewall off."))

    def test_allow_and_block(self):
        bus = FakeFirewalld()
        self.assertEqual(self.run_program(["allow", "rdp"], bus),
                         (0, "Remote desktop allowed in private networks."))
        self.assertIn("rdp", bus.permanent[fw.PRIVATE])
        self.assertEqual(self.run_program(["block", "rdp"], bus), (0, "Remote desktop blocked."))
        self.assertEqual(self.run_program(["allow", "telnet"], bus)[0], 2)

    def test_public(self):
        nets = networks(FakeSetting("Bar", ""))
        code, out = self.run_program(["public"], nets=nets)
        self.assertEqual((code, out), (0, "Firewall on. Bar is a public network."))


CHILD = r'''
import sys, time
sys.path.insert(0, sys.argv[1])
sys.path.insert(0, sys.argv[2])
from test_firewall import FakeFirewalld, FakeSetting, networks
import vabaxos_firewall as fw
from vabaxos_firewall.page import FirewallGroup
from gi.repository import Adw, GLib, Gtk

said = []
bus = FakeFirewalld()
app = Adw.Application(application_id="org.vabaxos.FirewallTest")
def check(app):
    window = Adw.ApplicationWindow(application=app)
    page = Adw.PreferencesPage()
    group = FirewallGroup(said.append, fw.Firewall(bus), networks(FakeSetting("Casa", "")))
    page.add(group.box)
    window.set_content(page)
    window.present()
    print("ROWS:" + "|".join(r.get_title() for r in group.rows), flush=True)
    combo = group.rows[1]
    combo.set_selected(1)
    switch = group.rows[2]
    switch.set_active(True)
    def done():
        if not switch.get_sensitive():
            return True
        print("SAID:" + "|".join(said), flush=True)
        print("SAMBA:%s" % ("samba" in bus.permanent[fw.PRIVATE]), flush=True)
        app.quit()
        return False
    GLib.timeout_add(200, done)
app.connect("activate", check)
app.run([])
'''


def free_display():
    for number in range(60, 100):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", 8080 + number)) != 0:
                return number
    raise RuntimeError("no free Broadway display")


@unittest.skipUnless(shutil.which("gtk4-broadwayd"), "gtk4-broadwayd (libgtk-4-bin) is not installed")
class PageTest(unittest.TestCase):

    def test_group_of_the_setup(self):
        display = free_display()
        broadway = subprocess.Popen(["gtk4-broadwayd", f":{display}"], stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
        time.sleep(1)
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, GDK_BACKEND="broadway", BROADWAY_DISPLAY=f":{display}",
                       GSETTINGS_BACKEND="memory", NO_AT_BRIDGE="1",
                       LANGUAGE="C", LANG="C.UTF-8", PYTHONDONTWRITEBYTECODE="1")
            try:
                result = subprocess.run([sys.executable, "-c", CHILD, LIB, os.path.dirname(__file__)], env=env,
                                        capture_output=True, text=True, timeout=60)
            finally:
                broadway.terminate()
                broadway.wait()
        out = dict(line.split(":", 1) for line in result.stdout.splitlines() if ":" in line)
        err = result.stderr[-2000:]
        self.assertEqual(out.get("ROWS"), "Firewall on. Casa is a private network.|Kind of network: Casa|"
                         "File sharing|Remote desktop|Remote terminal (SSH)", err)
        self.assertEqual(out.get("SAID"), "Casa is now a public network.|File sharing allowed in private networks.",
                         err)
        self.assertEqual(out.get("SAMBA"), "True", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
