#!/usr/bin/env python3
"""Tests for vabaxos-connections (Wi-Fi and Bluetooth): the sentences, the
D-Bus calls against made-up NetworkManager and BlueZ (python-dbusmock),
the pairing agent, and the window on Broadway with made-up backends.

    python3 tests/connections/test_connections.py
"""

import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ROOT = os.path.join(REPO, "packages", "vabaxos-connections", "root")
LIB = os.path.join(ROOT, "usr", "lib", "python3", "dist-packages")
PROGRAM = os.path.join(ROOT, "usr", "bin", "vabaxos-connections")
sys.path.insert(0, LIB)


from gi.repository import Gio, GLib  # noqa: E402
from vabaxos_connections import bluetooth as bt  # noqa: E402
from vabaxos_connections import wifi  # noqa: E402

try:
    import dbus
    import dbusmock
except ImportError:
    dbusmock = None

PSK = 0x100


class SentencesTest(unittest.TestCase):

    def test_security(self):
        self.assertEqual(wifi.security(0, 0, 0), "open")
        self.assertEqual(wifi.security(1, 0, 0), "wep")
        self.assertEqual(wifi.security(1, 0, 0x188), "psk")
        self.assertEqual(wifi.security(1, 0, 0x400 | 0x8), "sae")
        self.assertEqual(wifi.security(1, 0x100, 0x500), "psk", "WPA2 and WPA3 together: the password works")
        self.assertEqual(wifi.security(1, 0, 0x200), "enterprise")
        self.assertEqual(wifi.security(0, 0, 0x800), "owe")

    def test_network_describe(self):
        self.assertEqual(wifi.Network("Casa", 82, "psk", active=True, connection="/c").describe(),
                         "Casa, connected, protected, excellent signal")
        self.assertEqual(wifi.Network("Bar", 25, "open").describe(), "Bar, open, not protected, weak signal")
        self.assertEqual(wifi.Network("Uni", 55, "enterprise", connection="/c").describe(),
                         "Uni, saved, protected with a user name, good signal")

    def test_settings(self):
        settings = wifi.connection_settings("Casa", "sae", "segreta1")
        self.assertEqual(bytes(settings["802-11-wireless"]["ssid"].unpack()), b"Casa")
        self.assertEqual(settings["802-11-wireless-security"]["key-mgmt"].unpack(), "sae")
        self.assertNotIn("802-11-wireless-security", wifi.connection_settings("Bar", "open"))
        self.assertTrue(wifi.connection_settings("X", "psk", "p", hidden=True)["802-11-wireless"]["hidden"].unpack())

    def test_devices(self):
        self.assertEqual(bt.kind_of("audio-headphones"), "headphones")
        self.assertEqual(bt.kind_of(None, "Focus 40 Blue"), "braille")
        self.assertEqual(bt.kind_of("phone", "Brailliant BI 20X"), "braille")
        self.assertEqual(bt.kind_of("weird"), "other")
        self.assertEqual(bt.Device("/d", "Cuffie Sony", "headphones", True, True, battery=80).describe(),
                         "Cuffie Sony, headphones, connected, battery 80%")
        self.assertEqual(bt.Device("/d", "Tastiera", "keyboard").describe(), "Tastiera, keyboard, new")
        self.assertIn("pairing mode", bt.explain(Exception("GDBus.Error:org.bluez.Error.AuthenticationTimeout: x")))


def private_bus(address):
    return Gio.DBusConnection.new_for_address_sync(
        address, Gio.DBusConnectionFlags.AUTHENTICATION_CLIENT | Gio.DBusConnectionFlags.MESSAGE_BUS_CONNECTION,
        None, None)


@unittest.skipUnless(dbusmock, "python-dbusmock is not installed")
class NetworkManagerTest(dbusmock.DBusTestCase if dbusmock else unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.start_system_bus()

    def setUp(self):
        from dbusmock.templates.networkmanager import DeviceState
        self.server, self.mock = self.spawn_server_template("networkmanager", {}, stdout=subprocess.DEVNULL)
        self.device = self.mock.AddWiFiDevice("mock_WiFi", "wlan0", DeviceState.ACTIVATED,
                                              dbus_interface=dbusmock.MOCK_IFACE)
        for name, ssid, strength, sec in (("ap1", "Casa Rossi", 82, PSK), ("ap2", "Bar", 30, 0),
                                          ("ap3", "Casa Rossi", 40, PSK), ("ap4", "", 90, PSK)):
            self.mock.AddAccessPoint(self.device, name, ssid, "00:11:22:33:44:5" + name[-1], 2, 2425, 5400,
                                     strength, sec, dbus_interface=dbusmock.MOCK_IFACE)
        self.wifi = wifi.Wifi(private_bus(os.environ["DBUS_SYSTEM_BUS_ADDRESS"]))

    def tearDown(self):
        self.server.terminate()
        self.server.wait()

    def test_networks(self):
        self.assertEqual(self.wifi.device(), self.device)
        networks = self.wifi.networks()
        self.assertEqual([(n.ssid, n.strength) for n in networks], [("Casa Rossi", 82), ("Bar", 30)],
                         "one row per name, the strongest; hidden networks left out")
        self.assertEqual(self.wifi.status(), "Wi-Fi is on, not connected.")

    def test_connect_and_forget(self):
        casa = self.wifi.networks()[0]
        active = self.wifi.connect(casa, "segreta1")
        self.assertEqual(self.wifi.result(active), "activated")
        self.assertEqual(self.wifi.status(), "Connected to Casa Rossi, excellent signal.")
        casa = self.wifi.networks()[0]
        self.assertTrue(casa.active and casa.known)
        self.wifi.forget(casa)
        self.assertFalse(self.wifi.networks()[0].known)

    def test_enterprise_and_off(self):
        with self.assertRaises(wifi.WifiError):
            self.wifi.connect(wifi.Network("Uni", 50, "enterprise", ap="/x"))
        self.wifi.set_enabled(False)
        self.assertEqual(self.wifi.status(), "Wi-Fi is off.")

    def test_no_card(self):
        self.server.terminate()
        self.server.wait()
        self.server, self.mock = self.spawn_server_template("networkmanager", {}, stdout=subprocess.DEVNULL)
        self.assertIsNone(self.wifi.device())
        self.assertEqual(self.wifi.status(), "There is no Wi-Fi card.")
        self.assertEqual(self.wifi.networks(), [])


class AgentUI:
    def __init__(self):
        self.events = []
        self.reply = True

    def confirm(self, name, code, answer):
        self.events.append(("confirm", name, code))
        answer(self.reply)

    def ask_pin(self, name, numeric, answer):
        self.events.append(("pin", name, numeric))
        answer("123456" if self.reply else None)

    def show_code(self, name, code):
        self.events.append(("show", name, code))

    def cancelled(self):
        self.events.append(("cancel",))


@unittest.skipUnless(dbusmock, "python-dbusmock is not installed")
class BluezTest(dbusmock.DBusTestCase if dbusmock else unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.start_system_bus()

    def setUp(self):
        self.server, _obj = self.spawn_server_template("bluez5", {}, stdout=subprocess.DEVNULL)
        self.mock = dbus.Interface(self.get_dbus(system_bus=True).get_object("org.bluez", "/"), "org.bluez.Mock")
        self.mock.AddAdapter("hci0", "vabaxos")
        self.mock.AddDevice("hci0", "11:22:33:44:55:66", "Cuffie Sony")
        self.mock.AddDevice("hci0", "11:22:33:44:55:67", "Focus 40 Blue")
        self.bus = private_bus(os.environ["DBUS_SYSTEM_BUS_ADDRESS"])
        self.bt = bt.Bluetooth(self.bus)

    def tearDown(self):
        self.server.terminate()
        self.server.wait()

    def test_devices(self):
        self.assertEqual(self.bt.adapter(), "/org/bluez/hci0")
        self.assertEqual([d.describe() for d in self.bt.devices()],
                         ["Cuffie Sony, phone, new", "Focus 40 Blue, Braille display, new"])
        self.assertEqual(self.bt.status(), "Bluetooth is on, nothing connected.")

    def test_pair_connect_remove(self):
        cuffie = self.bt.devices()[0]
        self.bt.pair(cuffie)
        cuffie = self.bt.devices()[0]
        self.assertTrue(cuffie.paired and cuffie.trusted)
        self.mock.ConnectDevice("hci0", "11:22:33:44:55:66")
        self.assertEqual(self.bt.status(), "Bluetooth is on, connected: Cuffie Sony.")
        self.assertEqual(self.bt.devices()[0].describe(), "Cuffie Sony, phone, connected")
        self.bt.remove(self.bt.devices()[0])
        self.assertEqual([d.name for d in self.bt.devices()], ["Focus 40 Blue"])

    def test_powered(self):
        self.bt.set_powered(False)
        self.assertEqual(self.bt.status(), "Bluetooth is off.")

    def call_agent(self, method, args, reply=None):
        """Calls our agent as bluetoothd does, from another connection, while
        this thread runs the main loop that answers."""
        other = private_bus(os.environ["DBUS_SYSTEM_BUS_ADDRESS"])
        result = {}
        loop = GLib.MainLoop()

        def work():
            try:
                value = other.call_sync(self.bus.get_unique_name(), bt.AGENT_PATH, bt.AGENT, method, args,
                                        GLib.VariantType(reply) if reply else None, Gio.DBusCallFlags.NONE, 5000,
                                        None)
                result["value"] = value.unpack() if value is not None else None
            except Exception as error:  # noqa: BLE001
                result["error"] = str(error)
            GLib.idle_add(loop.quit)
        threading.Thread(target=work, daemon=True).start()
        loop.run()
        return result

    def test_agent(self):
        ui = AgentUI()
        agent = bt.Agent(self.bus, ui, lambda path: "Tastiera")
        agent.register()
        device = "/org/bluez/hci0/dev_11_22_33_44_55_66"
        self.assertEqual(self.call_agent("RequestConfirmation", GLib.Variant("(ou)", (device, 42))), {"value": ()})
        ui.reply = False
        self.assertIn("Rejected", self.call_agent("RequestConfirmation", GLib.Variant("(ou)", (device, 42)))["error"])
        ui.reply = True
        self.assertEqual(self.call_agent("RequestPasskey", GLib.Variant("(o)", (device,)), "(u)"),
                         {"value": (123456,)})
        self.call_agent("DisplayPasskey", GLib.Variant("(ouq)", (device, 7, 0)))
        self.call_agent("DisplayPasskey", GLib.Variant("(ouq)", (device, 7, 3)))
        self.assertEqual(ui.events, [("confirm", "Tastiera", "000042"), ("confirm", "Tastiera", "000042"),
                                     ("pin", "Tastiera", True), ("show", "Tastiera", "000007")])
        agent.unregister()


CHILD = r'''
import importlib.machinery, importlib.util, sys
loader = importlib.machinery.SourceFileLoader("connprog", sys.argv[1])
spec = importlib.util.spec_from_loader("connprog", loader)
program = importlib.util.module_from_spec(spec)
loader.exec_module(program)
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk
from vabaxos_connections.wifi import Network
from vabaxos_connections.bluetooth import Device

class FakeWifi:
    def __init__(self):
        self.on = True
        self.nets = [Network("Casa", 80, "psk", "/ap1"), Network("Bar", 30, "open", "/ap2")]
        self.connected = None
    def device(self): return "/dev"
    def enabled(self): return self.on
    def set_enabled(self, on): self.on = on
    def scan(self): pass
    def networks(self):
        for n in self.nets:
            n.active = n.ssid == self.connected
        return list(self.nets)
    def status(self): return f"Connected to {self.connected}, good signal." if self.connected else "Wi-Fi is on, not connected."
    def connect(self, network, password=None):
        self.password = password
        return "/active/" + network.ssid
    def result(self, active):
        self.connected = active.rsplit("/", 1)[-1]
        return "activated"

class FakeBluetooth:
    bus = None
    def __init__(self):
        self.devs = [Device("/d1", "Cuffie Sony", "headphones", True, False), Device("/d2", "Tastiera", "keyboard")]
    def adapter(self): return "/hci0"
    def powered(self): return True
    def devices(self): return list(self.devs)
    def status(self): return "Bluetooth is on, nothing connected."
    def discover(self, on): pass
    def pair(self, device):
        device.paired = device.connected = True

class FakeAgent:
    def __init__(self, bus, ui, names): pass
    def register(self): pass
    def unregister(self): pass

said = []
App, Window = program.window_classes(speak=said.append, wifi_factory=FakeWifi, bluetooth_factory=FakeBluetooth,
                                     agent_class=FakeAgent)
app = Adw.Application(application_id="org.vabaxos.ConnectionsTest")

def walk(widget):
    child = widget.get_first_child()
    while child:
        yield child
        yield from walk(child)
        child = child.get_next_sibling()

def inner(w):
    while w is not None:
        if type(w).__name__ in ("AdwToastWidget", "WindowControls", "AdwBackButton", "AdwViewSwitcherButton"):
            return True
        w = w.get_parent()
    return False

def check(app):
    window = Window(app, "wifi")
    window.present()
    def step1():
        print("WIFI:" + said[0], flush=True)
        print("ROWS:" + "|".join(r.get_title() + " - " + r.get_subtitle() for r in window.network_rows), flush=True)
        window.network_activated(window.networks[1])
        GLib.timeout_add(700, step2)
        return False
    def step2():
        print("OPEN:" + "|".join(said[1:]), flush=True)
        window.network_activated(window.networks[1])
        print("DIALOG:" + type(window.dialog).__name__ + " " + window.dialog.get_heading(), flush=True)
        window.dialog.close()
        window.stack.set_visible_child_name("bluetooth")
        GLib.timeout_add(300, step3)
        return False
    def step3():
        print("BT:" + said[-1], flush=True)
        print("DEVICES:" + "|".join(g.get_title() + ": " + r.get_title() for g, r in window.device_rows), flush=True)
        new = [d for d in window.devices if not d.paired][0]
        window.device_activated(new)
        GLib.timeout_add(700, step4)
        return False
    def step4():
        print("PAIRED:" + said[-1], flush=True)
        answers = []
        window.confirm("Tastiera", "012345", answers.append)
        print("CONFIRM:" + window.dialog.get_body(), flush=True)
        window.dialog.emit("response", "yes")
        print("ANSWER:" + repr(answers), flush=True)
        window.show_code("Tastiera", "000007")
        print("CODE:" + said[-1], flush=True)
        unnamed = [type(w).__name__ for w in walk(window) if isinstance(w, Gtk.Button) and w.get_mapped()
                   and not w.get_label() and not w.get_tooltip_text() and not inner(w)]
        print("UNNAMED:" + ",".join(unnamed), flush=True)
        app.quit()
        return False
    GLib.timeout_add(500, step1)

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
                   NO_AT_BRIDGE="1", PYTHONPATH=LIB, LANGUAGE="C", LANG="C.UTF-8", PYTHONDONTWRITEBYTECODE="1")
        try:
            result = subprocess.run([sys.executable, "-c", CHILD, PROGRAM], env=env, capture_output=True, text=True,
                                    timeout=60, check=False)
        finally:
            broadway.terminate()
            broadway.wait()
        out = dict(line.split(":", 1) for line in result.stdout.splitlines() if ":" in line)
        err = result.stderr[-3000:]
        self.assertEqual(out.get("WIFI"), "Wi-Fi is on, not connected.", err)
        self.assertEqual(out.get("ROWS"), "Casa - protected, excellent signal|Bar - open, not protected, fair signal",
                         err)
        self.assertEqual(out.get("OPEN"), "Bar is open: what you do on it can be seen by others.|Connecting to Bar."
                                          "|Connected to Bar.", err)
        self.assertEqual(out.get("DIALOG"), "AlertDialog Bar", err)
        self.assertEqual(out.get("BT"), "Bluetooth is on, nothing connected.", err)
        self.assertEqual(out.get("DEVICES"), "My devices: Cuffie Sony|New devices: Tastiera", err)
        self.assertEqual(out.get("PAIRED"), "Tastiera paired and connected.", err)
        self.assertEqual(out.get("CONFIRM"), "Tastiera shows the code 0 1 2 3 4 5? If it is the same, choose Yes, "
                                             "then confirm on the device too.", err)
        self.assertEqual(out.get("ANSWER"), "[True]", err)
        self.assertEqual(out.get("CODE"), "Type 0 0 0 0 0 7 on Tastiera, then Enter.", err)
        self.assertEqual(out.get("UNNAMED"), "", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
