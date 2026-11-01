"""Wi-Fi through NetworkManager's D-Bus API.

    wifi = Wifi()                    the system bus (or a test bus)
    wifi.device()                    the first Wi-Fi card, or None
    wifi.networks()                  [Network], strongest first, one per name
    wifi.connect(net, password)      -> the active connection path
    wifi.result(active)              "activated", "failed" or "waiting"
    wifi.forget(net), wifi.set_enabled(on), wifi.status()
"""

import uuid
from dataclasses import dataclass

from . import _, call, get, pgettext, set_prop, strength_word

NM = "org.freedesktop.NetworkManager"
NM_PATH = "/org/freedesktop/NetworkManager"
SETTINGS = "/org/freedesktop/NetworkManager/Settings"
DEVICE = NM + ".Device"
WIRELESS = NM + ".Device.Wireless"
AP = NM + ".AccessPoint"
ACTIVE = NM + ".Connection.Active"
CONNECTION = NM + ".Settings.Connection"
DEVICE_TYPE_WIFI = 2

# NM80211ApFlags and NM80211ApSecurityFlags
PRIVACY = 0x1
KEY_MGMT_PSK = 0x100
KEY_MGMT_8021X = 0x200
KEY_MGMT_SAE = 0x400
KEY_MGMT_OWE = 0x800
KEY_MGMT_EAP_SUITE_B = 0x2000
# NMActiveConnectionState
ACTIVATED, DEACTIVATING, DEACTIVATED = 2, 3, 4


def security(flags, wpa, rsn):
    """'open', 'owe' (open but encrypted), 'wep', 'psk', 'sae' (WPA3) or
    'enterprise' (a user name and a password, as at universities)."""
    both = wpa | rsn
    if both & (KEY_MGMT_8021X | KEY_MGMT_EAP_SUITE_B):
        return "enterprise"
    if both & KEY_MGMT_PSK:
        return "psk"
    if both & KEY_MGMT_SAE:
        return "sae"
    if both & KEY_MGMT_OWE:
        return "owe"
    if flags & PRIVACY:
        return "wep"
    return "open"


@dataclass
class Network:
    ssid: str
    strength: int
    security: str
    ap: str = "/"
    connection: str = ""   # the saved connection, when the network is known
    active: bool = False
    frequency: int = 0

    @property
    def protected(self):
        return self.security not in ("open", "owe")

    @property
    def known(self):
        return bool(self.connection)

    def describe(self):
        """'Casa, connected, protected, excellent signal'."""
        parts = [self.ssid]
        if self.active:
            parts.append(pgettext("network", "connected"))
        elif self.known:
            parts.append(pgettext("network", "saved"))
        parts.append({"open": _("open, not protected"), "owe": _("open, encrypted"), "wep": _("old protection (WEP)"),
                      "enterprise": _("protected with a user name")}.get(self.security, _("protected")))
        parts.append(strength_word(self.strength))
        return ", ".join(parts)


def connection_settings(ssid, kind, password=None, hidden=False):
    """The settings of a new connection, as AddAndActivateConnection wants."""
    from gi.repository import GLib
    settings = {
        "connection": {"id": GLib.Variant("s", ssid), "uuid": GLib.Variant("s", str(uuid.uuid4())),
                       "type": GLib.Variant("s", "802-11-wireless")},
        "802-11-wireless": {"ssid": GLib.Variant("ay", ssid.encode("utf-8")), "mode": GLib.Variant("s", "infrastructure")},
    }
    if hidden:
        settings["802-11-wireless"]["hidden"] = GLib.Variant("b", True)
    if kind in ("psk", "sae"):
        settings["802-11-wireless-security"] = {"key-mgmt": GLib.Variant("s", "sae" if kind == "sae" else "wpa-psk"),
                                                "psk": GLib.Variant("s", password or "")}
    elif kind == "owe":
        settings["802-11-wireless-security"] = {"key-mgmt": GLib.Variant("s", "owe")}
    elif kind == "wep":
        settings["802-11-wireless-security"] = {"key-mgmt": GLib.Variant("s", "none"),
                                                "wep-key0": GLib.Variant("s", password or ""),
                                                "wep-key-type": GLib.Variant("u", 1)}
    return settings


class WifiError(RuntimeError):
    pass


class Wifi:

    def __init__(self, bus=None):
        if bus is None:
            from gi.repository import Gio
            bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        self.bus = bus

    def _call(self, path, interface, method, args=None, reply=None, timeout=25000):
        return call(self.bus, NM, path, interface, method, args, reply, timeout)

    def _get(self, path, interface, prop):
        return get(self.bus, NM, path, interface, prop)

    # -- the card --------------------------------------------------------

    def device(self):
        try:
            devices = self._call(NM_PATH, NM, "GetDevices", reply="(ao)")
        except Exception:  # noqa: BLE001 - no NetworkManager
            return None
        for path in devices:
            if self._get(path, DEVICE, "DeviceType") == DEVICE_TYPE_WIFI:
                return path
        return None

    def enabled(self):
        return bool(self._get(NM_PATH, NM, "WirelessEnabled"))

    def hardware_enabled(self):
        return bool(self._get(NM_PATH, NM, "WirelessHardwareEnabled"))

    def set_enabled(self, on):
        from gi.repository import GLib
        set_prop(self.bus, NM, NM_PATH, NM, "WirelessEnabled", GLib.Variant("b", on))

    def scan(self):
        """Asks the card for a new search; NetworkManager refuses it when it
        has just searched, which is fine."""
        from gi.repository import GLib
        device = self.device()
        if device:
            try:
                self._call(device, WIRELESS, "RequestScan", GLib.Variant("(a{sv})", ({},)))
            except Exception:  # noqa: BLE001 - scanned a moment ago
                pass

    # -- the networks ----------------------------------------------------

    def saved(self):
        """{ssid: connection path} of the saved Wi-Fi connections."""
        known = {}
        for path in self._call(SETTINGS, NM + ".Settings", "ListConnections", reply="(ao)"):
            try:
                settings = self._call(path, CONNECTION, "GetSettings", reply="(a{sa{sv}})")
            except Exception:  # noqa: BLE001 - not readable by this user
                continue
            wireless = settings.get("802-11-wireless")
            if wireless and wireless.get("ssid"):
                known[bytes(wireless["ssid"]).decode("utf-8", "replace")] = path
        return known

    def active_connection(self, device):
        active = self._get(device, DEVICE, "ActiveConnection")
        if not active or active == "/":
            return None, None
        try:
            return active, self._get(active, ACTIVE, "Connection")
        except Exception:  # noqa: BLE001 - it has just gone
            return None, None

    def networks(self):
        device = self.device()
        if not device:
            return []
        known = self.saved()
        _active, active_connection = self.active_connection(device)
        found = {}
        for ap in self._call(device, WIRELESS, "GetAllAccessPoints", reply="(ao)"):
            try:
                props = call(self.bus, NM, ap, "org.freedesktop.DBus.Properties", "GetAll",
                             _variant("(s)", (AP,)), "(a{sv})")
            except Exception:  # noqa: BLE001 - the network has just gone
                continue
            ssid = bytes(props.get("Ssid", b"")).decode("utf-8", "replace").strip("\x00")
            if not ssid:
                continue   # hidden networks: "Hidden network" asks the name
            network = Network(ssid, int(props.get("Strength", 0)),
                              security(props.get("Flags", 0), props.get("WpaFlags", 0), props.get("RsnFlags", 0)),
                              ap, known.get(ssid, ""), frequency=int(props.get("Frequency", 0)))
            network.active = bool(network.connection) and network.connection == active_connection
            old = found.get(ssid)
            if old is None or (network.active and not old.active) or \
                    (not old.active and network.strength > old.strength):
                found[ssid] = network
        return sorted(found.values(), key=lambda n: (not n.active, not n.known, -n.strength, n.ssid.lower()))

    # -- connecting ------------------------------------------------------

    def connect(self, network, password=None):
        """Starts the connection; the active connection path is returned at
        once, result() says later how it went."""
        device = self.device()
        if not device:
            raise WifiError(_("There is no Wi-Fi card."))
        if network.security == "enterprise" and not network.known:
            raise WifiError(_("This network needs a user name: connect it once from the GNOME Settings, "
                              "Wi-Fi page."))
        if network.known and password is None:
            return self._call(NM_PATH, NM, "ActivateConnection",
                              _variant("(ooo)", (network.connection, device, network.ap)), "(o)")
        if network.known:
            self.forget(network)
        settings = connection_settings(network.ssid, network.security, password)
        _path, active = self._call(NM_PATH, NM, "AddAndActivateConnection",
                                   _variant("(a{sa{sv}}oo)", (settings, device, network.ap)), "(oo)")
        return active

    def connect_hidden(self, ssid, kind, password=None):
        device = self.device()
        if not device:
            raise WifiError(_("There is no Wi-Fi card."))
        settings = connection_settings(ssid, kind, password, hidden=True)
        _path, active = self._call(NM_PATH, NM, "AddAndActivateConnection",
                                   _variant("(a{sa{sv}}oo)", (settings, device, "/")), "(oo)")
        return active

    def result(self, active):
        """'activated', 'failed' or 'waiting' for an active connection."""
        try:
            state = self._get(active, ACTIVE, "State")
        except Exception:  # noqa: BLE001 - NetworkManager removed it: it failed
            return "failed"
        if state == ACTIVATED:
            return "activated"
        if state in (DEACTIVATING, DEACTIVATED):
            return "failed"
        return "waiting"

    def disconnect(self):
        device = self.device()
        active, _connection = self.active_connection(device) if device else (None, None)
        if active:
            self._call(NM_PATH, NM, "DeactivateConnection", _variant("(o)", (active,)))

    def forget(self, network):
        if network.connection:
            self._call(network.connection, CONNECTION, "Delete")
            network.connection = ""

    # -- in one sentence -------------------------------------------------

    def status(self):
        device = self.device()
        if not device:
            return _("There is no Wi-Fi card.")
        if not self.hardware_enabled():
            return _("Wi-Fi is turned off by a switch or by the airplane mode.")
        if not self.enabled():
            return _("Wi-Fi is off.")
        for network in self.networks():
            if network.active:
                return _("Connected to {network}, {signal}.").format(network=network.ssid,
                                                                     signal=strength_word(network.strength))
        return _("Wi-Fi is on, not connected.")


def _variant(signature, value):
    from gi.repository import GLib
    return GLib.Variant(signature, value)
