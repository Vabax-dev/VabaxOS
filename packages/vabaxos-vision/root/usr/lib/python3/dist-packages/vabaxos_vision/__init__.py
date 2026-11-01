"""Seeing the screen better: GNOME's zoom, contrast, text size, pointer
and colours, changed with one key and said aloud (Vabax, 2026-11-02:
"zoom, high contrast, large pointer, with one key").

Every change goes to GNOME's own settings, so GNOME's Accessibility
settings and the first setup show the same values. A setting missing on
this system is left alone (Gio.Settings.new would close the program).

    Vision().zoom_in() ... each returns the sentence to say
"""

import gettext

_translation = gettext.translation("vabaxos-vision", fallback=True)
_ = _translation.gettext

APPLICATIONS = "org.gnome.desktop.a11y.applications"
MAGNIFIER = "org.gnome.desktop.a11y.magnifier"
A11Y = "org.gnome.desktop.a11y.interface"
INTERFACE = "org.gnome.desktop.interface"
MAX_ZOOM = 16.0
TEXT_SIZES = (1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0)
POINTERS = (24, 48, 64, 96)


def number(value):
    """2.0 -> '2', 1.5 -> '1,5' in Italian."""
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return text.replace(".", _translation.pgettext("decimal separator", "."))


def zoom_steps(factor, up):
    """The next zoom level: half steps up to 4, whole ones after."""
    step = 0.5 if (factor < 4 or (not up and factor <= 4)) else 1.0
    return min(MAX_ZOOM, factor + step) if up else max(1.0, factor - step)


class Vision:

    def __init__(self, settings=None):
        self._settings = {}
        self._factory = settings

    def settings(self, schema):
        if schema not in self._settings:
            if self._factory is not None:
                self._settings[schema] = self._factory(schema)
            else:
                from gi.repository import Gio
                source = Gio.SettingsSchemaSource.get_default()
                found = source.lookup(schema, True) if source else None
                self._settings[schema] = Gio.Settings.new(schema) if found else None
        return self._settings[schema]

    def get(self, schema, key, default=None):
        gs = self.settings(schema)
        if gs is None or key not in gs.list_keys():
            return default
        return gs.get_value(key).unpack()

    def set(self, schema, key, value):
        from gi.repository import GLib
        gs = self.settings(schema)
        if gs is None or key not in gs.list_keys():
            return False
        gs.set_value(key, GLib.Variant(gs.get_value(key).get_type_string(), value))
        return True

    # -- zoom ------------------------------------------------------------

    def zoom_on(self):
        return bool(self.get(APPLICATIONS, "screen-magnifier-enabled", False))

    def zoom_in(self):
        factor = float(self.get(MAGNIFIER, "mag-factor", 2.0))
        if not self.zoom_on():
            factor = max(factor, 1.5)
            self.set(APPLICATIONS, "screen-magnifier-enabled", True)
        else:
            factor = zoom_steps(factor, True)
        self.set(MAGNIFIER, "mag-factor", factor)
        return _("Zoom {factor} times.").format(factor=number(factor))

    def zoom_out(self):
        if not self.zoom_on():
            return _("Zoom is off.")
        factor = zoom_steps(float(self.get(MAGNIFIER, "mag-factor", 2.0)), False)
        if factor <= 1.0:
            self.set(APPLICATIONS, "screen-magnifier-enabled", False)
            self.set(MAGNIFIER, "mag-factor", 1.5)
            return _("Zoom off.")
        self.set(MAGNIFIER, "mag-factor", factor)
        return _("Zoom {factor} times.").format(factor=number(factor))

    def zoom_toggle(self):
        if self.zoom_on():
            self.set(APPLICATIONS, "screen-magnifier-enabled", False)
            return _("Zoom off.")
        return self.zoom_in()

    # -- contrast, text, pointer, colours -----------------------------

    def toggle(self, schema, key, on_text, off_text):
        value = not bool(self.get(schema, key, False))
        if not self.set(schema, key, value):
            return _("This setting is not on this system.")
        return on_text if value else off_text

    def contrast(self):
        return self.toggle(A11Y, "high-contrast", _("High contrast on."), _("High contrast off."))

    def text(self, up):
        current = float(self.get(INTERFACE, "text-scaling-factor", 1.0))
        bigger = [s for s in TEXT_SIZES if s > current + 0.01]
        smaller = [s for s in TEXT_SIZES if s < current - 0.01]
        size = (bigger[0] if bigger else TEXT_SIZES[-1]) if up else (smaller[-1] if smaller else TEXT_SIZES[0])
        self.set(INTERFACE, "text-scaling-factor", size)
        if size == 1.0:
            return _("Text of normal size.")
        return _("Text {size} times bigger.").format(size=number(size))

    def pointer(self):
        current = int(self.get(INTERFACE, "cursor-size", 24))
        bigger = [p for p in POINTERS if p > current]
        size = bigger[0] if bigger else POINTERS[0]
        self.set(INTERFACE, "cursor-size", size)
        return _("Normal pointer.") if size == POINTERS[0] else _("Pointer {times} times bigger.").format(
            times=number(size / POINTERS[0]))

    def invert(self):
        """Light letters on dark: GNOME inverts what the zoom shows, so with
        the zoom off it turns on at 1 time, the whole screen as it is."""
        value = not bool(self.get(MAGNIFIER, "invert-lightness", False))
        self.set(MAGNIFIER, "invert-lightness", value)
        if value and not self.zoom_on():
            self.set(MAGNIFIER, "mag-factor", 1.0)
            self.set(APPLICATIONS, "screen-magnifier-enabled", True)
        return _("Colours inverted.") if value else _("Colours normal.")

    def greyscale(self):
        grey = float(self.get(MAGNIFIER, "color-saturation", 1.0)) > 0.0
        self.set(MAGNIFIER, "color-saturation", 0.0 if grey else 1.0)
        if grey and not self.zoom_on():
            self.set(MAGNIFIER, "mag-factor", 1.0)
            self.set(APPLICATIONS, "screen-magnifier-enabled", True)
        return _("Black and white.") if grey else _("Colours back.")

    def crosshairs(self):
        return self.toggle(MAGNIFIER, "show-cross-hairs", _("Cross-hairs on."), _("Cross-hairs off."))

    def status(self):
        parts = [_("Zoom {factor} times.").format(factor=number(float(self.get(MAGNIFIER, "mag-factor", 1.0))))
                 if self.zoom_on() else _("Zoom off.")]
        parts.append(_("High contrast on.") if self.get(A11Y, "high-contrast", False) else _("High contrast off."))
        size = float(self.get(INTERFACE, "text-scaling-factor", 1.0))
        parts.append(_("Text of normal size.") if size == 1.0 else
                     _("Text {size} times bigger.").format(size=number(size)))
        return " ".join(parts)
