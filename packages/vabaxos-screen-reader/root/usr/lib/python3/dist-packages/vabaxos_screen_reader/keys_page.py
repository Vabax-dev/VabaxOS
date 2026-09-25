# SPDX-FileCopyrightText: 2026 Vabax and VabaxOS contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""The Keys page of the screen reader settings (block 10): the key scheme
(NVDA, JAWS, Orca's own), then every command of Orca with its key and a
Change button. A new key is chosen with switches (screen reader key, Ctrl,
Alt, Shift), the name of the key and how many presses: pressing the keys
would not work, because Orca itself takes the keys held with Insert.
"""

import gettext

from gi.repository import Adw, Gtk

from . import keymaps
from .orca_commands import COMMANDS

_ = gettext.gettext
ITALIAN_NAMES = {name.lower(): keysym for keysym, name in keymaps.KEY_NAMES.items()}
ENGLISH_NAMES = {name.lower(): keysym for keysym, name in keymaps.KEY_NAMES_EN.items()}
KEYSYMS = {row[3][0] for row in COMMANDS if row[3]} | {row[4][0] for row in COMMANDS if row[4]} | \
    set(keymaps.KEY_NAMES) | {f"F{n}" for n in range(1, 13)}


def orca_text(text, context=None):
    """Orca's own translation of one of its strings."""
    if context:
        translated = gettext.dpgettext("orca", context, text)
        if translated != text:
            return translated
    return gettext.dgettext("orca", text)


def key_from_text(text):
    """The keysym for what a person writes: a letter or digit, F1-F12,
    a key name in Italian or English (Freccia su, Page Up), or a keysym."""
    text = text.strip()
    if not text:
        return None
    lower = text.lower()
    if len(text) == 1:
        return lower
    if lower in ITALIAN_NAMES:
        return ITALIAN_NAMES[lower]
    if lower in ENGLISH_NAMES:
        return ENGLISH_NAMES[lower]
    if lower.startswith("f") and lower[1:].isdigit() and 1 <= int(lower[1:]) <= 12:
        return "F" + lower[1:]
    for keysym in KEYSYMS:
        if keysym.lower() == lower:
            return keysym
    return None


def italian():
    return _("Screen reader settings") != "Screen reader settings"


class KeysPage:
    """Builds the page; refresh() after a change of profile."""

    def __init__(self, window):
        self.window = window
        self.rows = []
        self.page = Adw.PreferencesPage(title=_("Keys"), description=_("The keys of the screen reader"))

        schemes = Adw.PreferencesGroup(
            title=_("Key scheme"),
            description=_("NVDA and JAWS schemes use the keys of those screen readers; "
                          "Orca uses its own. Insert+1 then F2 lists every key."))
        self.scheme_row = Adw.ComboRow(title=_("Keys like"))
        self.scheme_labels = [_("NVDA (the default)"), _("JAWS"), _("Orca's own keys"), _("Personalized")]
        self.scheme_row.set_model(Gtk.StringList.new(self.scheme_labels))
        self.scheme_handler = self.scheme_row.connect("notify::selected", self.scheme_chosen)
        schemes.add(self.scheme_row)
        self.search = Adw.EntryRow(title=_("Search a command"))
        self.search.connect("changed", lambda *_a: self.filter())
        schemes.add(self.search)
        self.page.add(schemes)

        self.groups = {}
        for name, group, description, _desktop, _laptop in COMMANDS:
            if group not in self.groups:
                box = Adw.PreferencesGroup(title=orca_text(group, "keybindings"))
                self.groups[group] = box
                self.page.add(box)
            title = orca_text(description)
            row = Adw.ActionRow(title=title, activatable=True)
            button = Gtk.Button(label=_("Change"), valign=Gtk.Align.CENTER)
            button.update_property([Gtk.AccessibleProperty.LABEL], [_("Change the key: {name}").format(name=title)])
            button.connect("clicked", lambda _b, n=name, t=title: self.change(n, t))
            row.add_suffix(button)
            row.connect("activated", lambda _r, n=name, t=title: self.change(n, t))
            self.groups[group].add(row)
            self.rows.append((row, name, title.lower()))
        self.refresh()

    # -- values --------------------------------------------------------------

    @property
    def store(self):
        return self.window.store

    def layout(self):
        return self.store.get("keybindings", "keyboard-layout") or "desktop"

    def entries(self):
        return dict(self.store.get("keybindings", "entries") or {})

    def current_scheme(self):
        entries, layout = self.entries(), self.layout()
        for index, scheme in enumerate(keymaps.SCHEMES):
            if entries == keymaps.entries(scheme, layout):
                return index
        return len(keymaps.SCHEMES)

    def refresh(self):
        keys = keymaps.effective(self.entries(), self.layout())
        for row, name, _title in self.rows:
            row.set_subtitle(keymaps.label(keys.get(name), italian()))
        self.scheme_row.handler_block(self.scheme_handler)
        self.scheme_row.set_selected(self.current_scheme())
        self.scheme_row.handler_unblock(self.scheme_handler)

    def filter(self):
        text = self.search.get_text().strip().lower()
        shown = set()
        for row, _name, title in self.rows:
            show = text in title or text in row.get_subtitle().lower()
            row.set_visible(show)
            if show:
                shown.add(row.get_ancestor(Adw.PreferencesGroup))
        for box in self.groups.values():
            box.set_visible(box in shown)

    # -- changes -------------------------------------------------------------

    def save(self, entries, message):
        self.store.set("keybindings", "entries", entries)
        self.store.pending_reload = True
        self.store.reload_orca_if_needed()
        self.refresh()
        self.window.say(message)

    def apply_scheme(self, scheme):
        self.store.set("keybindings", "desktop-modifier-keys", keymaps.MODIFIERS[scheme])
        self.save(keymaps.entries(scheme, self.layout()),
                  _("The keys are now: {scheme}.").format(scheme=self.scheme_labels[keymaps.SCHEMES.index(scheme)]))

    def scheme_chosen(self, *_a):
        index = self.scheme_row.get_selected()
        if 0 <= index < len(keymaps.SCHEMES):
            self.apply_scheme(keymaps.SCHEMES[index])
        else:
            self.refresh()

    def layout_changed(self, old_layout):
        """The keyboard layout changed: a scheme follows it."""
        entries = self.entries()
        for scheme in keymaps.SCHEMES:
            if entries == keymaps.entries(scheme, old_layout):
                self.store.set("keybindings", "entries", keymaps.entries(scheme, self.layout()))
                break
        self.refresh()

    def change(self, name, title):
        keys = keymaps.effective(self.entries(), self.layout())
        current = keys.get(name)
        dialog = Adw.AlertDialog(heading=_("New key for: {name}").format(name=title),
                                 body=_("Now: {key}. Choose the keys to hold, the key to press and how "
                                        "many times.").format(key=keymaps.label(current, italian())))
        box = Adw.PreferencesGroup()
        switches = []
        for label, mask in ((_("Screen reader key"), keymaps.O), (_("Ctrl"), keymaps.C),
                            (_("Alt"), keymaps.A), (_("Shift"), keymaps.S)):
            row = Adw.SwitchRow(title=label, active=bool(current and current[1] & mask))
            switches.append((row, mask))
            box.add(row)
        key_row = Adw.EntryRow(title=_("Key: a letter, a digit, F1 to F12, or a name such as Up Arrow"))
        if current:
            key_row.set_text(keymaps.label((current[0], 0, 1), italian()))
        box.add(key_row)
        presses = Adw.ComboRow(title=_("How many times"))
        presses.set_model(Gtk.StringList.new([_("Once"), _("Twice"), _("Three times")]))
        presses.set_selected((current[2] - 1) if current else 0)
        box.add(presses)
        dialog.set_extra_child(box)
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("original", _("Orca's own key"))
        dialog.add_response("none", _("No key"))
        dialog.add_response("save", _("Save"))
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("save")
        dialog.set_close_response("cancel")
        dialog.connect("response", self.change_done, name, title, switches, key_row, presses)
        dialog.present(self.window)

    def change_done(self, _dialog, response, name, title, switches, key_row, presses):
        entries = self.entries()
        if response == "original":
            entries.pop(name, None)
            self.save(entries, _("{name}: Orca's own key again.").format(name=title))
            return
        if response == "none":
            entries[name] = []
            self.save(entries, _("{name}: no key.").format(name=title))
            return
        if response != "save":
            return
        keysym = key_from_text(key_row.get_text())
        if keysym is None:
            self.window.say(_("Key not recognized: write a letter, a digit, F1 to F12, or a key name."))
            return
        mods = sum(mask for row, mask in switches if row.get_active())
        key = (keysym, mods, presses.get_selected() + 1)
        keys = keymaps.effective(entries, self.layout())
        keys[name] = key
        others = [n for n, k in keys.items() if k == key and n != name]
        if others:
            other = next((orca_text(row[2]) for row in COMMANDS if row[0] == others[0]), others[0])
            self.window.say(_("{key} is already used for: {other}. Choose another key, or change that "
                              "command first.").format(key=keymaps.label(key, italian()), other=other))
            return
        entries[name] = [[keysym, keymaps.MASK, str(mods), str(key[2])]]
        self.save(entries, _("{name}: {key}.").format(name=title, key=keymaps.label(key, italian())))
