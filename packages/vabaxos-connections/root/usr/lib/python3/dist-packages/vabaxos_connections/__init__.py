"""Wi-Fi and Bluetooth said aloud: the networks and the devices, as
sentences that Orca reads well, and the D-Bus calls to NetworkManager and
BlueZ (wifi.py, bluetooth.py), without libnm or gnome-bluetooth, so the
same code is tested against python-dbusmock.
"""

import gettext

_translation = gettext.translation("vabaxos-connections", fallback=True)
_ = _translation.gettext
pgettext = _translation.pgettext


def call(bus, name, path, interface, method, args=None, reply=None, timeout=25000):
    """A D-Bus call; the result unpacked, or None for no result."""
    from gi.repository import Gio, GLib
    result = bus.call_sync(name, path, interface, method, args, GLib.VariantType(reply) if reply else None,
                           Gio.DBusCallFlags.NONE, timeout, None)
    if result is None:
        return None
    values = result.unpack()
    return values[0] if len(values) == 1 else values


def get(bus, name, path, interface, prop):
    from gi.repository import GLib
    return call(bus, name, path, "org.freedesktop.DBus.Properties", "Get",
                GLib.Variant("(ss)", (interface, prop)), "(v)")


def get_all(bus, name, path, interface):
    from gi.repository import GLib
    return call(bus, name, path, "org.freedesktop.DBus.Properties", "GetAll", GLib.Variant("(s)", (interface,)),
                "(a{sv})")


def set_prop(bus, name, path, interface, prop, value):
    from gi.repository import GLib
    call(bus, name, path, "org.freedesktop.DBus.Properties", "Set", GLib.Variant("(ssv)", (interface, prop, value)))


def error_text(error):
    """The useful part of a D-Bus error: without 'GDBus.Error:name: '."""
    text = getattr(error, "message", None) or str(error)
    if text.startswith("GDBus.Error:"):
        text = text.split(": ", 1)[-1]
    return text


def strength_word(strength):
    """0-100 -> a word: what a person needs, not a number."""
    if strength >= 70:
        return _("excellent signal")
    if strength >= 50:
        return _("good signal")
    if strength >= 30:
        return _("fair signal")
    return _("weak signal")
