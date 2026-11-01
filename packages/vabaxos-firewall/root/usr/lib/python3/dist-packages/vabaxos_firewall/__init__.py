"""The VabaxOS firewall (ADR-0021): firewalld with two kinds of network,
private and public, like Windows.

Each network connection of NetworkManager has a zone (connection.zone):
vabaxos-private or vabaxos-public. A connection without a zone uses the
default zone, vabaxos-private ("not too strict", Vabax, 2026-11-01).
Programs the user allows (file sharing, remote desktop, SSH) are added to
the private zone only, at once and for good; changing them asks for the
administrator password (polkit, read by Orca).
"""

import gettext


def _(text):
    """Translated in the domain of this package, whichever program uses it."""
    return gettext.dgettext("vabaxos-firewall", text)

PRIVATE = "vabaxos-private"
PUBLIC = "vabaxos-public"
DEFAULT_ZONE = PRIVATE
# firewalld's own zones that count as public: they trust nobody.
PUBLIC_ZONES = {PUBLIC, "public", "external", "dmz", "block", "drop"}

# Programs that can be allowed in private networks: firewalld service,
# then the words for the user. None is allowed by default, as in Windows.
APPS = [
    ("samba", lambda: _("File sharing"),
     lambda: _("Other computers open the folders you share (Windows and Mac too)")),
    ("rdp", lambda: _("Remote desktop"),
     lambda: _("Someone you trust uses this computer from another one, to help you")),
    ("ssh", lambda: _("Remote terminal (SSH)"),
     lambda: _("Commands from another computer, for those who know them")),
]
APP_SERVICES = [service for service, _t, _d in APPS]

BUS_NAME = "org.fedoraproject.FirewallD1"
PATH = "/org/fedoraproject/FirewallD1"
CONFIG_PATH = "/org/fedoraproject/FirewallD1/config"


def kind(zone, default_zone=DEFAULT_ZONE):
    """'private' or 'public' for a zone; an empty zone is the default."""
    zone = zone or default_zone
    return "public" if zone in PUBLIC_ZONES else "private"


def zone_for(kind_name):
    return PUBLIC if kind_name == "public" else PRIVATE


def describe(running, kinds):
    """One sentence: the state of the firewall and of the networks in use.
    kinds: [(connection name, 'private' or 'public')]."""
    if not running:
        return _("Firewall off.")
    if not kinds:
        return _("Firewall on.")
    parts = []
    for name, which in kinds:
        if which == "public":
            parts.append(_("{name} is a public network").format(name=name))
        else:
            parts.append(_("{name} is a private network").format(name=name))
    return _("Firewall on.") + " " + ", ".join(parts) + "."


class Firewall:
    """firewalld through D-Bus. Every change is made at once (runtime) and
    for good (permanent); polkit asks for the password when needed."""

    def __init__(self, bus=None):
        from gi.repository import Gio
        self.Gio = Gio
        self.bus = bus or Gio.bus_get_sync(Gio.BusType.SYSTEM, None)

    def _call(self, path, interface, method, args=None, reply=None):
        from gi.repository import GLib
        flags = self.Gio.DBusCallFlags.ALLOW_INTERACTIVE_AUTHORIZATION
        result = self.bus.call_sync(BUS_NAME, path, interface, method, args,
                                    GLib.VariantType(reply) if reply else None, flags, 120000, None)
        return result.unpack() if result is not None else None

    def running(self):
        try:
            self.default_zone()
            return True
        except Exception:  # noqa: BLE001 - not installed, not running
            return False

    def default_zone(self):
        return self._call(PATH, BUS_NAME, "getDefaultZone", None, "(s)")[0]

    def services(self, zone=PRIVATE):
        from gi.repository import GLib
        return list(self._call(PATH, BUS_NAME + ".zone", "getServices", GLib.Variant("(s)", (zone,)), "(as)")[0])

    def allowed(self, service, zone=PRIVATE):
        return service in self.services(zone)

    def set_allowed(self, service, allowed, zone=PRIVATE):
        from gi.repository import GLib
        path = self._call(CONFIG_PATH, BUS_NAME + ".config", "getZoneByName", GLib.Variant("(s)", (zone,)), "(o)")[0]
        now = self.allowed(service, zone)
        if allowed and not now:
            self._call(PATH, BUS_NAME + ".zone", "addService", GLib.Variant("(ssi)", (zone, service, 0)), "(s)")
        elif not allowed and now:
            self._call(PATH, BUS_NAME + ".zone", "removeService", GLib.Variant("(ss)", (zone, service)), "(s)")
        permanent = service in self._call(path, BUS_NAME + ".config.zone", "getServices", None, "(as)")[0]
        if allowed and not permanent:
            self._call(path, BUS_NAME + ".config.zone", "addService", GLib.Variant("(s)", (service,)))
        elif not allowed and permanent:
            self._call(path, BUS_NAME + ".config.zone", "removeService", GLib.Variant("(s)", (service,)))


class Networks:
    """The network connections in use, and their kind, through
    NetworkManager (libnm)."""

    def __init__(self, client=None):
        if client is None:
            import gi
            gi.require_version("NM", "1.0")
            from gi.repository import NM
            client = NM.Client.new(None)
        self.client = client

    def active(self):
        """[(connection, name, zone)] of the connections in use, without
        the loopback and the virtual ones."""
        found = []
        for active in self.client.get_active_connections():
            connection = active.get_connection()
            if connection is None:
                continue
            setting = connection.get_setting_connection()
            if setting is None or setting.get_connection_type() in ("loopback", "bridge", "tun", "veth"):
                continue
            found.append((connection, setting.get_id(), setting.get_zone() or ""))
        return found

    def kinds(self, default_zone=DEFAULT_ZONE):
        return [(name, kind(zone, default_zone)) for _c, name, zone in self.active()]

    def set_kind(self, connection, kind_name, callback=None):
        """Saves the zone in the connection; NetworkManager tells firewalld
        at once. callback(ok, error) when done (asynchronous)."""
        setting = connection.get_setting_connection()
        setting.set_property("zone", zone_for(kind_name))

        def done(conn, result):
            try:
                conn.commit_changes_finish(result)
            except Exception as error:  # noqa: BLE001 - told to the caller
                if callback:
                    callback(False, error)
                return
            if callback:
                callback(True, None)
        connection.commit_changes_async(True, None, done)
