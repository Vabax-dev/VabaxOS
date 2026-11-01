"""The window of VabaxOS updates (ADR-0020).

Three pages, chosen with the tabs at the top (Ctrl+Page Down and Ctrl+Page
Up, or Alt+1, Alt+2, Alt+3):

- Updates: the state in one line (said by Orca when the window opens and
  after each check), the buttons Check, Update now, Update at restart, the
  progress, and four groups (security, system, applications, firmware) that
  open with Enter or the Right arrow and list every update.
- History: what was installed, updated and removed, newest first.
- Settings: how often VabaxOS checks by itself, and what it announces.

Long work (PackageKit, Flatpak, fwupd) runs in a thread; every message is
also a toast, which Orca reads wherever the focus is in the window.
"""

import gettext
import sys
import threading
import time

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib, Gtk  # noqa: E402

from vabaxos_update import core, history, settings  # noqa: E402

_ = gettext.gettext
ngettext = gettext.ngettext

GROUP_TITLES = {
    core.SECURITY: lambda: _("Security"),
    core.SYSTEM: lambda: _("System"),
    core.APPS: lambda: _("Applications"),
    core.FIRMWARE: lambda: _("Firmware"),
}
FREQUENCY_LABELS = [("daily", lambda: _("Every day")), ("weekly", lambda: _("Every week")),
                    ("never", lambda: _("Never"))]
NOTIFY_LABELS = [("security", lambda: _("Only security updates")), ("all", lambda: _("All updates"))]


def when(timestamp, now=None):
    if not timestamp:
        return _("never")
    now = now or time.time()
    moment = time.localtime(timestamp)
    if time.localtime(now)[:3] == moment[:3]:
        return _("today at {time}").format(time=time.strftime("%H:%M", moment))
    return time.strftime("%d/%m/%Y %H:%M", moment)


def state_text(updates):
    if not updates:
        return _("VabaxOS is up to date.")
    security = core.count(updates, core.SECURITY)
    total = len(updates)
    text = ngettext("{count} update", "{count} updates", total).format(count=total)
    if security:
        text += ", " + ngettext("{count} for security", "{count} for security", security).format(count=security)
    return text + "."


def history_title(entry):
    parts = []
    for action, label in (("Upgrade", _("updated")), ("Install", _("installed")),
                          ("Remove", _("removed")), ("Purge", _("removed")), ("Downgrade", _("downgraded"))):
        if entry.total(action):
            parts.append(f"{entry.total(action)} {label}")
    return entry.date.replace("  ", " ") + ": " + (", ".join(parts) or _("no packages"))


class UpdateWindow(Adw.ApplicationWindow):

    def __init__(self, app, program, updater_factory=None, history_path=history.LOG):
        """program: the vabaxos-update module (Updater, the Flatpak and
        firmware updates, the note about the sources)."""
        super().__init__(application=app, title=_("Update VabaxOS"))
        self.set_default_size(760, 640)
        self.program = program
        self.updater_factory = updater_factory or (lambda: program.Updater(on_step=self.step))
        self.updates = []
        self.busy = False
        self.cancellable = None
        self.history_path = history_path

        self.toasts = Adw.ToastOverlay()
        self.stack = Adw.ViewStack()
        self.stack.add_titled_with_icon(self.updates_page(), "updates", _("Updates"),
                                        "software-update-available-symbolic")
        self.stack.add_titled_with_icon(self.history_page(), "history", _("History"),
                                        "document-open-recent-symbolic")
        self.stack.add_titled_with_icon(self.settings_page(), "settings", _("Settings"),
                                        "preferences-system-symbolic")
        header = Adw.HeaderBar()
        switcher = Adw.ViewSwitcher(stack=self.stack, policy=Adw.ViewSwitcherPolicy.WIDE)
        header.set_title_widget(switcher)
        view = Adw.ToolbarView()
        view.add_top_bar(header)
        view.set_content(self.stack)
        self.toasts.set_child(view)
        self.set_content(self.toasts)
        self.add_shortcuts()
        self.connect("close-request", self.closing)

    # -- pages ----------------------------------------------------------------

    def updates_page(self):
        page = Adw.PreferencesPage()
        state = Adw.PreferencesGroup(title=_("State"))
        self.state_row = Adw.ActionRow(title=_("Not checked yet"), subtitle=self.last_check_text())
        self.state_row.set_focusable(True)
        state.add(self.state_row)
        if self.program.unchecked_sources():
            note = Adw.ActionRow(title=_("Test version"),
                                 subtitle=_("Updates come straight from Debian testing, not yet "
                                            "checked by VabaxOS."))
            note.set_focusable(True)
            state.add(note)
        page.add(state)

        actions = Adw.PreferencesGroup()
        buttons = Gtk.Box(spacing=8, homogeneous=False)
        self.check_button = self.button(buttons, _("Check"), _("Look for updates (F5)"), self.check)
        self.now_button = self.button(buttons, _("Update now"), _("Download and install now"),
                                      lambda: self.install(False))
        self.restart_button = self.button(buttons, _("Update at restart"),
                                          _("Download now, install at the next start: the safest way"),
                                          lambda: self.install(True))
        self.cancel_button = self.button(buttons, _("Cancel"), _("Stop the check or the download"), self.cancel)
        self.now_button.add_css_class("suggested-action")
        actions.add(buttons)
        self.progress = Gtk.ProgressBar(show_text=True, visible=False, margin_top=8)
        self.progress.update_property([Gtk.AccessibleProperty.LABEL], [_("Progress")])
        actions.add(self.progress)
        page.add(actions)

        self.groups = Adw.PreferencesGroup(title=_("What there is to update"))
        self.expanders = {}
        for kind in core.KINDS:
            row = Adw.ExpanderRow(title=GROUP_TITLES[kind](), subtitle=_("Not checked yet"))
            row.set_enable_expansion(False)
            self.expanders[kind] = (row, [])
            self.groups.add(row)
        page.add(self.groups)
        self.set_busy(False)
        return page

    def history_page(self):
        page = Adw.PreferencesPage()
        self.history_group = Adw.PreferencesGroup(
            title=_("History"), description=_("What was installed, updated and removed, newest first."))
        page.add(self.history_group)
        self.history_rows = []
        self.fill_history()
        return page

    def settings_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title=_("Automatic check"),
                                     description=_("VabaxOS looks for updates by itself, in silence, and "
                                                   "never installs anything without asking."))
        config = settings.load()
        self.frequency_row = self.combo(_("Check for updates"), FREQUENCY_LABELS, config["frequency"],
                                        "frequency")
        self.notify_row = self.combo(_("Announce"), NOTIFY_LABELS, config["notify"], "notify")
        group.add(self.frequency_row)
        group.add(self.notify_row)
        page.add(group)
        return page

    # -- building -------------------------------------------------------------

    def button(self, box, label, tooltip, action):
        button = Gtk.Button(label=label)
        button.set_tooltip_text(tooltip)
        button.connect("clicked", lambda *_a: action())
        box.append(button)
        return button

    def combo(self, title, labels, value, key):
        row = Adw.ComboRow(title=title)
        row.set_model(Gtk.StringList.new([label() for _v, label in labels]))
        values = [v for v, _l in labels]
        row.set_selected(values.index(value) if value in values else 0)

        def changed(combo, _pspec):
            config = settings.load()
            config[key] = values[combo.get_selected()]
            settings.save(config)
        row.connect("notify::selected", changed)
        return row

    def add_shortcuts(self):
        controller = Gtk.ShortcutController(scope=Gtk.ShortcutScope.MANAGED)
        pages = ["updates", "history", "settings"]
        keys = {"F5": self.check, "<Control>r": self.check}
        for i, name in enumerate(pages, start=1):
            keys[f"<Alt>{i}"] = lambda n=name: self.stack.set_visible_child_name(n)
        keys["<Control>Page_Down"] = lambda: self.next_page(1)
        keys["<Control>Page_Up"] = lambda: self.next_page(-1)
        for accel, action in keys.items():
            callback = Gtk.CallbackAction.new(lambda *_a, act=action: act() or True)
            controller.add_shortcut(Gtk.Shortcut.new(Gtk.ShortcutTrigger.parse_string(accel), callback))
        self.add_controller(controller)

    def next_page(self, step):
        pages = ["updates", "history", "settings"]
        current = pages.index(self.stack.get_visible_child_name() or "updates")
        self.stack.set_visible_child_name(pages[(current + step) % len(pages)])

    def say(self, text):
        """A message for Orca: a toast is announced wherever the focus is."""
        self.toasts.add_toast(Adw.Toast.new(text))
        return False

    def last_check_text(self):
        return _("Last check: {when}").format(when=when(settings.last_check()))

    # -- state ----------------------------------------------------------------

    def set_busy(self, busy):
        self.busy = busy
        has = bool(self.updates)
        self.check_button.set_sensitive(not busy)
        self.now_button.set_sensitive(not busy and has)
        self.restart_button.set_sensitive(not busy and has)
        self.cancel_button.set_visible(busy)
        self.progress.set_visible(busy)
        return False

    def show_updates(self, updates):
        self.updates = updates
        for kind in core.KINDS:
            row, children = self.expanders[kind]
            for child in children:
                row.remove(child)
            children.clear()
            mine = [u for u in updates if u.kind == kind]
            row.set_subtitle(_("Nothing to update") if not mine else
                             ngettext("{count} update", "{count} updates", len(mine)).format(count=len(mine)))
            row.set_enable_expansion(bool(mine))
            row.set_expanded(False)
            for update in mine:
                child = Adw.ActionRow(title=update.name,
                                      subtitle=" ".join(p for p in (update.version, update.summary) if p))
                child.set_focusable(True)
                row.add_row(child)
                children.append(child)
        text = state_text(updates)
        self.state_row.set_title(text)
        self.state_row.set_subtitle(self.last_check_text())
        self.say(text)
        self.set_busy(False)
        return False

    def fill_history(self):
        for row in self.history_rows:
            self.history_group.remove(row)
        self.history_rows = []
        entries = history.read(self.history_path)
        if not entries:
            row = Adw.ActionRow(title=_("No updates installed yet"))
            row.set_focusable(True)
            self.history_group.add(row)
            self.history_rows.append(row)
            return
        for entry in entries:
            row = Adw.ExpanderRow(title=history_title(entry))
            for action, names in entry.changes.items():
                label = {"Upgrade": _("Updated"), "Install": _("Installed"), "Remove": _("Removed"),
                         "Purge": _("Removed"), "Downgrade": _("Downgraded")}[action]
                child = Adw.ActionRow(title=label, subtitle=", ".join(names))
                child.set_focusable(True)
                row.add_row(child)
            self.history_group.add(row)
            self.history_rows.append(row)

    # -- work -----------------------------------------------------------------

    def step(self, percent):
        GLib.idle_add(self.say, _("Updating: {percent} percent.").format(percent=percent))

    def pulse(self):
        if not self.busy:
            return False
        self.progress.pulse()
        return True

    def start(self, text):
        self.cancellable = Gio.Cancellable()
        self.set_busy(True)
        self.progress.set_text(text)
        self.say(text)
        GLib.timeout_add(250, self.pulse)

    def check(self):
        if self.busy:
            return
        self.start(_("Looking for updates. Please wait."))
        threading.Thread(target=self._check, daemon=True).start()

    def _check(self):
        try:
            updater = self.updater_factory()
            updater.cancellable = self.cancellable
            packages = updater.packages()
            updates = core.from_packagekit(packages, updater.pk.InfoEnum.SECURITY)
        except Exception as error:  # noqa: BLE001 - said to the user
            GLib.idle_add(self.failed, _("Cannot look for updates: {error}. Check the network and try "
                                         "again.").format(error=error))
            return
        updates += core.flatpak_updates() + core.firmware_updates()
        settings.mark_checked(time.time())
        GLib.idle_add(self.show_updates, updates)

    def failed(self, text):
        self.say(text)
        self.state_row.set_title(text)
        self.set_busy(False)
        return False

    def cancel(self):
        if self.cancellable is not None:
            self.cancellable.cancel()
            self.say(_("Stopping."))

    def install(self, at_restart):
        if self.busy or not self.updates:
            return
        names = core.critical(self.updates)
        if names and not at_restart:
            self.ask_restart(names)
            return
        self.run_install(at_restart)

    def ask_restart(self, names):
        dialog = Adw.AlertDialog(
            heading=_("Better at the next start"),
            body=_("These updates change the desktop or the voice: {names}. Installed now, they can "
                   "stop the voice until the computer restarts. Install them at the next start?").format(
                names=", ".join(names[:6]) + ("…" if len(names) > 6 else "")))
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("now", _("Now anyway"))
        dialog.add_response("restart", _("At the next start"))
        dialog.set_default_response("restart")
        dialog.set_close_response("cancel")
        dialog.set_response_appearance("restart", Adw.ResponseAppearance.SUGGESTED)

        def answered(dialog, response):
            if response in ("now", "restart"):
                self.run_install(response == "restart")
        dialog.connect("response", answered)
        dialog.present(self)

    def run_install(self, at_restart):
        self.start(_("Downloading the updates.") if at_restart else _("Updating. Please wait."))
        threading.Thread(target=self._install, args=(at_restart,), daemon=True).start()

    def _install(self, at_restart):
        system = [u.ident for u in self.updates if u.kind in (core.SECURITY, core.SYSTEM)]
        try:
            updater = self.updater_factory()
            updater.cancellable = self.cancellable
            if system:
                updater.install(system, at_restart=at_restart)
            if not at_restart:
                if any(u.kind == core.APPS for u in self.updates):
                    self.program.update_flatpak()
                if any(u.kind == core.FIRMWARE for u in self.updates):
                    self.program.update_firmware()
        except Exception as error:  # noqa: BLE001
            GLib.idle_add(self.failed, _("The update stopped: {error}.").format(error=error))
            return
        GLib.idle_add(self.installed, at_restart, updater.restart)

    def installed(self, at_restart, restart):
        if at_restart:
            text = _("Ready. The updates will be installed at the next start.")
        elif restart == "system":
            text = _("Update finished. Restart the computer to complete it.")
        elif restart == "session":
            text = _("Update finished. Log out and in again to complete it.")
        else:
            text = _("Update finished.")
        self.state_row.set_title(text)
        self.say(text)
        self.fill_history()
        if not at_restart:
            self.updates = []
            self.show_updates([])
            self.state_row.set_title(text)
        self.set_busy(False)
        return False

    def closing(self, *_args):
        if self.cancellable is not None:
            self.cancellable.cancel()
        return False


class UpdateApp(Adw.Application):

    def __init__(self, program):
        super().__init__(application_id="org.vabaxos.Update")
        self.program = program
        self.connect("activate", self.on_activate)

    def on_activate(self, _app):
        window = self.get_active_window()
        if window is None:
            window = UpdateWindow(self, self.program)
            GLib.idle_add(window.check)
        window.present()


def run_window(program):
    return UpdateApp(program).run([sys.argv[0]])
