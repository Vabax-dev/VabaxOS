"""Bluetooth through BlueZ's D-Bus API, with a pairing agent of our own.

    bt = Bluetooth()               the system bus (or a test bus)
    bt.adapter()                   the first adapter, or None
    bt.devices()                   [Device], connected and paired first
    bt.pair(device)                pairs, trusts and connects (slow: a thread)
    bt.connect, bt.disconnect, bt.remove, bt.set_powered, bt.discover

GNOME has a pairing agent only while its Bluetooth settings are open, so
the window registers Agent while it is open: the questions of pairing
(the same code on both screens, a PIN to type) come to the window and are
said aloud. Headphones and speakers pair without questions.
"""

from dataclasses import dataclass

from . import _, call, get, set_prop

BLUEZ = "org.bluez"
ADAPTER = "org.bluez.Adapter1"
DEVICE = "org.bluez.Device1"
BATTERY = "org.bluez.Battery1"
AGENT_MANAGER = "org.bluez.AgentManager1"
AGENT = "org.bluez.Agent1"
AGENT_PATH = "/org/vabaxos/bluetooth/agent"

KINDS = {
    "audio-headset": "headset", "audio-headphones": "headphones", "audio-speakers": "speaker",
    "audio-card": "speaker", "input-keyboard": "keyboard", "input-mouse": "mouse", "input-tablet": "tablet",
    "input-gaming": "gamepad", "phone": "phone", "computer": "computer", "printer": "printer",
    "camera-photo": "camera", "camera-video": "camera", "multimedia-player": "player", "video-display": "display",
}


def kind_name(kind):
    return {"headset": _("headset"), "headphones": _("headphones"), "speaker": _("speaker"),
            "keyboard": _("keyboard"), "mouse": _("mouse"), "tablet": _("graphics tablet"),
            "gamepad": _("game controller"), "phone": _("phone"), "computer": _("computer"),
            "printer": _("printer"), "camera": _("camera"), "player": _("music player"),
            "display": _("screen"), "braille": _("Braille display")}.get(kind, _("device"))


def kind_of(icon, name=""):
    """The kind of a device from BlueZ's Icon; Braille displays have no icon
    of their own, so they are found by name (Focus, Brailliant, ...)."""
    lowered = name.lower()
    if any(word in lowered for word in ("braille", "focus 14", "focus 40", "focus 80", "brailliant", "orbit reader",
                                        "esys", "basic braille", "mantis", "chameleon", "hims", "braille sense",
                                        "braille edge", "vario")):
        return "braille"
    return KINDS.get(icon or "", "other")


@dataclass
class Device:
    path: str
    name: str
    kind: str = "other"
    paired: bool = False
    connected: bool = False
    trusted: bool = False
    battery: int = -1

    def describe(self):
        """'Cuffie Sony, headphones, connected, battery 80%'."""
        parts = [self.name, kind_name(self.kind)]
        if self.connected:
            parts.append(_("connected"))
        elif self.paired:
            parts.append(_("paired, not connected"))
        else:
            parts.append(_("new"))
        if self.battery >= 0:
            parts.append(_("battery {percent}%").format(percent=self.battery))
        return ", ".join(parts)


class BluetoothError(RuntimeError):
    pass


class Bluetooth:

    def __init__(self, bus=None):
        if bus is None:
            from gi.repository import Gio
            bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        self.bus = bus

    def _objects(self):
        try:
            return call(self.bus, BLUEZ, "/", "org.freedesktop.DBus.ObjectManager", "GetManagedObjects",
                        reply="(a{oa{sa{sv}}})")
        except Exception:  # noqa: BLE001 - no bluetoothd
            return {}

    def adapter(self):
        for path, interfaces in sorted(self._objects().items()):
            if ADAPTER in interfaces:
                return path
        return None

    def powered(self):
        adapter = self.adapter()
        return bool(adapter and get(self.bus, BLUEZ, adapter, ADAPTER, "Powered"))

    def set_powered(self, on):
        from gi.repository import GLib
        adapter = self.adapter()
        if not adapter:
            raise BluetoothError(_("There is no Bluetooth in this computer."))
        set_prop(self.bus, BLUEZ, adapter, ADAPTER, "Powered", GLib.Variant("b", on))

    def discover(self, on):
        """Searches for new devices (on) or stops searching."""
        adapter = self.adapter()
        if not adapter:
            return
        try:
            call(self.bus, BLUEZ, adapter, ADAPTER, "StartDiscovery" if on else "StopDiscovery")
        except Exception:  # noqa: BLE001 - already searching, or already stopped
            pass

    def devices(self):
        adapter = self.adapter()
        found = []
        for path, interfaces in self._objects().items():
            props = interfaces.get(DEVICE)
            if not props or props.get("Adapter") != adapter:
                continue
            name = props.get("Alias") or props.get("Name") or props.get("Address", "")
            battery = interfaces.get(BATTERY, {}).get("Percentage", -1)
            found.append(Device(path, name, kind_of(props.get("Icon"), name), bool(props.get("Paired")),
                                bool(props.get("Connected")), bool(props.get("Trusted")), int(battery)))
        return sorted(found, key=lambda d: (not d.connected, not d.paired, d.name.lower()))

    def _device(self, device, method, timeout=60000):
        try:
            call(self.bus, BLUEZ, device.path, DEVICE, method, timeout=timeout)
        except Exception as error:  # noqa: BLE001 - said with BlueZ's reason
            raise BluetoothError(explain(error)) from error

    def pair(self, device):
        """Pairs, trusts (so it connects again by itself) and connects."""
        from gi.repository import GLib
        if not device.paired:
            self._device(device, "Pair", timeout=90000)
        set_prop(self.bus, BLUEZ, device.path, DEVICE, "Trusted", GLib.Variant("b", True))
        if not device.connected:
            self._device(device, "Connect")

    def connect(self, device):
        self._device(device, "Connect")

    def disconnect(self, device):
        self._device(device, "Disconnect")

    def remove(self, device):
        from gi.repository import GLib
        adapter = self.adapter()
        call(self.bus, BLUEZ, adapter, ADAPTER, "RemoveDevice", GLib.Variant("(o)", (device.path,)))

    def status(self):
        if not self.adapter():
            return _("There is no Bluetooth in this computer.")
        if not self.powered():
            return _("Bluetooth is off.")
        connected = [d.name for d in self.devices() if d.connected]
        if not connected:
            return _("Bluetooth is on, nothing connected.")
        return _("Bluetooth is on, connected: {devices}.").format(devices=", ".join(connected))


def explain(error):
    """BlueZ's errors in words."""
    text = str(error)
    for name, sentence in (
            ("AuthenticationFailed", _("The pairing failed: the code was wrong or not confirmed.")),
            ("AuthenticationCanceled", _("The pairing was cancelled.")),
            ("AuthenticationRejected", _("The device refused the pairing.")),
            ("AuthenticationTimeout", _("The device did not answer in time: put it in pairing mode and try again.")),
            ("ConnectionAttemptFailed", _("The device cannot be reached: is it on and near?")),
            ("AlreadyExists", _("The device is already paired.")),
            ("InProgress", _("Wait: the device is already connecting.")),
            ("NotReady", _("Bluetooth is not ready: turn it on.")),
            ("Failed", _("The device did not connect: is it on, near, and not connected to another device?"))):
        if name in text:
            return sentence
    return text


AGENT_XML = """
<node>
  <interface name="org.bluez.Agent1">
    <method name="Release"/>
    <method name="RequestPinCode"><arg type="o" direction="in"/><arg type="s" direction="out"/></method>
    <method name="DisplayPinCode"><arg type="o" direction="in"/><arg type="s" direction="in"/></method>
    <method name="RequestPasskey"><arg type="o" direction="in"/><arg type="u" direction="out"/></method>
    <method name="DisplayPasskey"><arg type="o" direction="in"/><arg type="u" direction="in"/>
      <arg type="q" direction="in"/></method>
    <method name="RequestConfirmation"><arg type="o" direction="in"/><arg type="u" direction="in"/></method>
    <method name="RequestAuthorization"><arg type="o" direction="in"/></method>
    <method name="AuthorizeService"><arg type="o" direction="in"/><arg type="s" direction="in"/></method>
    <method name="Cancel"/>
  </interface>
</node>
"""


class Agent:
    """The pairing agent. ui answers the questions:

        ui.confirm(device_name, code, answer)   answer(True or False)
        ui.ask_pin(device_name, numeric, answer) answer(text, or None to cancel)
        ui.show_code(device_name, code)          to type on the device
        ui.cancelled()
    """

    def __init__(self, bus, ui, names=None):
        self.bus, self.ui = bus, ui
        self.names = names or (lambda path: path.rsplit("/", 1)[-1])
        self.registration = None

    def register(self):
        from gi.repository import Gio, GLib
        info = Gio.DBusNodeInfo.new_for_xml(AGENT_XML).interfaces[0]
        self.registration = self.bus.register_object(AGENT_PATH, info, self._method, None, None)
        call(self.bus, BLUEZ, "/org/bluez", AGENT_MANAGER, "RegisterAgent",
             GLib.Variant("(os)", (AGENT_PATH, "KeyboardDisplay")))
        call(self.bus, BLUEZ, "/org/bluez", AGENT_MANAGER, "RequestDefaultAgent", GLib.Variant("(o)", (AGENT_PATH,)))

    def unregister(self):
        from gi.repository import GLib
        if self.registration is None:
            return
        try:
            call(self.bus, BLUEZ, "/org/bluez", AGENT_MANAGER, "UnregisterAgent", GLib.Variant("(o)", (AGENT_PATH,)))
        except Exception:  # noqa: BLE001 - bluetoothd has gone
            pass
        self.bus.unregister_object(self.registration)
        self.registration = None

    def _name(self, path):
        try:
            return self.names(path)
        except Exception:  # noqa: BLE001
            return path.rsplit("/", 1)[-1]

    def _method(self, _bus, _sender, _path, _interface, method, params, invocation):
        from gi.repository import GLib
        args = params.unpack()
        reject = ("org.bluez.Error.Rejected", _("Refused"))
        canceled = ("org.bluez.Error.Canceled", _("Cancelled"))
        if method in ("Release", "AuthorizeService", "RequestAuthorization"):
            # Pairing started by the user from this window, or services of a
            # device the user has already paired: allowed.
            invocation.return_value(None)
        elif method == "Cancel":
            self.ui.cancelled()
            invocation.return_value(None)
        elif method == "RequestConfirmation":
            def answer(ok):
                if ok:
                    invocation.return_value(None)
                else:
                    invocation.return_dbus_error(*reject)
            self.ui.confirm(self._name(args[0]), f"{args[1]:06d}", answer)
        elif method in ("RequestPinCode", "RequestPasskey"):
            numeric = method == "RequestPasskey"

            def answer(text):
                if text is None or (numeric and not text.strip().isdigit()):
                    invocation.return_dbus_error(*canceled)
                elif numeric:
                    invocation.return_value(GLib.Variant("(u)", (int(text.strip()),)))
                else:
                    invocation.return_value(GLib.Variant("(s)", (text.strip(),)))
            self.ui.ask_pin(self._name(args[0]), numeric, answer)
        elif method == "DisplayPinCode":
            self.ui.show_code(self._name(args[0]), args[1])
            invocation.return_value(None)
        elif method == "DisplayPasskey":
            if args[2] == 0:   # called again at each key typed on the device
                self.ui.show_code(self._name(args[0]), f"{args[1]:06d}")
            invocation.return_value(None)
        else:
            invocation.return_dbus_error(*reject)
