"""The firewall group of the VabaxOS setup, Network page (ADR-0021).

    Firewall                       on, and the kind of each network
    Kind of network: <name>        Private (home, work) / Public (café...)
    File sharing, Remote desktop,  switches: allowed in private networks
    Remote terminal (SSH)

Every change is said (announce); if it fails, for example when the
administrator password is not given, the row goes back as it was and the
reason is said.
"""

import threading

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk  # noqa: E402

import vabaxos_firewall as fw  # noqa: E402
from vabaxos_firewall import _  # noqa: E402

KIND_LABELS = [("private", lambda: _("Private: home or work")), ("public", lambda: _("Public: café, hotel, train"))]


class FirewallGroup:

    def __init__(self, announce, firewall=None, networks=None):
        self.announce = announce
        self.box = Adw.PreferencesGroup(
            title=_("Firewall"),
            description=_("Like in Windows: everything going out is allowed. In a private network "
                          "devices, printers, shared folders and the phone are found; in a public "
                          "one nothing comes in."))
        self.rows = []
        try:
            self.firewall = firewall or fw.Firewall()
            self.running = self.firewall.running()
        except Exception:  # noqa: BLE001 - no system bus
            self.firewall, self.running = None, False
        try:
            self.networks = networks or fw.Networks()
        except Exception:  # noqa: BLE001 - no NetworkManager
            self.networks = None
        self.busy = False
        self.refresh()

    def add(self, row):
        self.box.add(row)
        self.rows.append(row)

    def refresh(self):
        for row in self.rows:
            self.box.remove(row)
        self.rows = []
        default = self.firewall.default_zone() if self.running else fw.DEFAULT_ZONE
        active = self.networks.active() if self.networks else []
        kinds = [(name, fw.kind(zone, default)) for _c, name, zone in active]
        state = Adw.ActionRow(title=fw.describe(self.running, kinds))
        state.set_focusable(True)
        self.add(state)
        if not self.running:
            return
        for connection, name, zone in active:
            row = Adw.ComboRow(title=_("Kind of network: {name}").format(name=name),
                               subtitle=_("Choose Public in places you do not know"))
            row.set_model(Gtk.StringList.new([label() for _k, label in KIND_LABELS]))
            values = [k for k, _l in KIND_LABELS]
            row.set_selected(values.index(fw.kind(zone, default)))
            row.connect("notify::selected", self.kind_changed, connection, name, values)
            self.add(row)
        for service, title, description in fw.APPS:
            row = Adw.SwitchRow(title=title(), subtitle=description())
            try:
                row.set_active(self.firewall.allowed(service))
            except Exception:  # noqa: BLE001
                row.set_sensitive(False)
            row.connect("notify::active", self.app_changed, service, title())
            self.add(row)

    def kind_changed(self, row, _pspec, connection, name, values):
        if self.busy:
            return
        which = values[row.get_selected()]

        def done(ok, error):
            if ok:
                text = (_("{name} is now a public network.") if which == "public"
                        else _("{name} is now a private network.")).format(name=name)
            else:
                text = _("The kind of network did not change: {error}").format(error=error)
                self.busy = True
                row.set_selected(1 - row.get_selected())
                self.busy = False
            self.announce(text)
        self.networks.set_kind(connection, which, done)

    def app_changed(self, row, _pspec, service, title):
        if self.busy:
            return
        allowed = row.get_active()
        row.set_sensitive(False)

        def work():
            try:
                self.firewall.set_allowed(service, allowed)
                error = None
            except Exception as problem:  # noqa: BLE001 - said to the user
                error = problem
            GLib.idle_add(finished, error)

        def finished(error):
            row.set_sensitive(True)
            if error is None:
                text = (_("{program} allowed in private networks.") if allowed
                        else _("{program} blocked.")).format(program=title)
            else:
                text = _("{program} did not change: {error}").format(program=title, error=error)
                self.busy = True
                row.set_active(not allowed)
                self.busy = False
            self.announce(text)
            return False
        # The password window of polkit may take a while: not in the main loop.
        threading.Thread(target=work, daemon=True).start()
