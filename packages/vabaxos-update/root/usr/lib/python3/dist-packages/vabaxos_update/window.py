"""Interfaccia grafica di VabaxOS Update."""

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Adw, Gio, GLib, Gtk

from . import UpdateManager, UpdatePriority, format_size, speak


class UpdateRow(Adw.ExpanderRow):
    """Riga per un aggiornamento."""

    def __init__(self, update, **kwargs):
        super().__init__(**kwargs)
        self.update = update
        self.selected = False

        # Titolo e sottotitolo
        self.set_title(update.name)
        subtitle = f"{update.current_version} → {update.new_version}"
        if update.is_security:
            subtitle += " • SICUREZZA"
        self.set_subtitle(subtitle)

        # Icona priorità
        icon_name, css_class = self._get_priority_icon()
        icon = Gtk.Image.new_from_icon_name(icon_name)
        icon.add_css_class(css_class)
        self.add_prefix(icon)

        # Checkbox per selezione
        self.check = Gtk.CheckButton()
        self.check.set_active(True)
        self.check.connect("toggled", self._on_toggled)
        self.add_prefix(self.check)
        self.selected = True

        # Descrizione
        if update.description:
            desc_label = Gtk.Label(label=update.description)
            desc_label.set_wrap(True)
            desc_label.set_xalign(0)
            desc_label.set_margin_top(6)
            desc_label.set_margin_bottom(6)
            desc_label.set_margin_start(12)
            desc_label.set_margin_end(12)
            self.add_row(desc_label)

        # Dettagli
        details = []
        details.append(f"Dimensione: {format_size(update.size)}")
        details.append(f"Fonte: {update.source.value}")
        if update.requires_reboot:
            details.append("⚠ Richiede riavvio")

        details_label = Gtk.Label(label=" • ".join(details))
        details_label.set_wrap(True)
        details_label.set_xalign(0)
        details_label.set_margin_top(6)
        details_label.set_margin_bottom(6)
        details_label.set_margin_start(12)
        details_label.set_margin_end(12)
        details_label.add_css_class("dim-label")
        self.add_row(details_label)

        # Changelog
        if update.changelog:
            changelog_label = Gtk.Label(label=update.changelog)
            changelog_label.set_wrap(True)
            changelog_label.set_xalign(0)
            changelog_label.set_margin_top(6)
            changelog_label.set_margin_bottom(6)
            changelog_label.set_margin_start(12)
            changelog_label.set_margin_end(12)
            changelog_label.add_css_class("monospace")
            self.add_row(changelog_label)

    def _get_priority_icon(self):
        """Restituisce icona e classe CSS per la priorità."""
        if self.update.is_security:
            return "security-high-symbolic", "error"
        elif self.update.priority == UpdatePriority.IMPORTANT:
            return "dialog-warning-symbolic", "warning"
        elif self.update.priority == UpdatePriority.BUGFIX:
            return "tools-symbolic", "accent"
        return "package-x-generic-symbolic", ""

    def _on_toggled(self, check):
        """Gestisce il cambio di selezione."""
        self.selected = check.get_active()


class UpdateWindow(Adw.ApplicationWindow):
    """Finestra principale di VabaxOS Update."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_default_size(800, 600)
        self.set_title("Aggiornamenti VabaxOS")

        self.manager = UpdateManager()
        self.update_rows = []
        self.checking = False
        self.installing = False

        self._build_ui()

        # Controlla aggiornamenti all'avvio
        GLib.timeout_add(100, self._initial_check)

    def _build_ui(self):
        """Costruisce l'interfaccia."""
        # Header bar
        header = Adw.HeaderBar()

        # Pulsante aggiorna
        self.refresh_button = Gtk.Button.new_from_icon_name("view-refresh-symbolic")
        self.refresh_button.set_tooltip_text("Controlla aggiornamenti")
        self.refresh_button.connect("clicked", self._on_refresh_clicked)
        header.pack_start(self.refresh_button)

        # Pulsante installa
        self.install_button = Gtk.Button(label="Installa")
        self.install_button.add_css_class("suggested-action")
        self.install_button.set_sensitive(False)
        self.install_button.connect("clicked", self._on_install_clicked)
        header.pack_end(self.install_button)

        # Toolbox principale
        toolbox = Adw.ToolbarView()
        toolbox.add_top_bar(header)

        # Stack per le diverse viste
        self.stack = Gtk.Stack()
        self.stack.set_vexpand(True)
        self.stack.set_hexpand(True)

        # Vista: controllo in corso
        checking_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        checking_box.set_valign(Gtk.Align.CENTER)
        checking_box.set_halign(Gtk.Align.CENTER)

        self.checking_spinner = Gtk.Spinner()
        self.checking_spinner.set_size_request(48, 48)
        self.checking_spinner.start()
        checking_box.append(self.checking_spinner)

        checking_label = Gtk.Label(label="Controllo aggiornamenti in corso...")
        checking_label.add_css_class("title-2")
        checking_box.append(checking_label)

        self.stack.add_named(checking_box, "checking")

        # Vista: nessun aggiornamento
        no_updates_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        no_updates_box.set_valign(Gtk.Align.CENTER)
        no_updates_box.set_halign(Gtk.Align.CENTER)

        no_updates_icon = Gtk.Image.new_from_icon_name("emblem-ok-symbolic")
        no_updates_icon.set_pixel_size(64)
        no_updates_icon.add_css_class("success")
        no_updates_box.append(no_updates_icon)

        no_updates_label = Gtk.Label()
        no_updates_label.set_markup("<big><b>Il sistema è aggiornato</b></big>")
        no_updates_box.append(no_updates_label)

        self.last_check_label = Gtk.Label()
        self.last_check_label.add_css_class("dim-label")
        no_updates_box.append(self.last_check_label)

        self.stack.add_named(no_updates_box, "no-updates")

        # Vista: aggiornamenti disponibili
        updates_scrolled = Gtk.ScrolledWindow()
        updates_scrolled.set_vexpand(True)

        updates_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        updates_box.set_margin_top(12)
        updates_box.set_margin_bottom(12)
        updates_box.set_margin_start(12)
        updates_box.set_margin_end(12)

        # Banner riepilogo
        self.summary_banner = Adw.Banner()
        self.summary_banner.set_revealed(False)
        updates_box.append(self.summary_banner)

        # Lista aggiornamenti
        self.updates_list = Gtk.ListBox()
        self.updates_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.updates_list.add_css_class("boxed-list")
        updates_box.append(self.updates_list)

        updates_scrolled.set_child(updates_box)
        self.stack.add_named(updates_scrolled, "updates")

        # Vista: installazione in corso
        installing_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        installing_box.set_valign(Gtk.Align.CENTER)
        installing_box.set_halign(Gtk.Align.CENTER)
        installing_box.set_margin_top(48)
        installing_box.set_margin_bottom(48)
        installing_box.set_margin_start(48)
        installing_box.set_margin_end(48)

        installing_label = Gtk.Label()
        installing_label.set_markup("<big><b>Installazione in corso...</b></big>")
        installing_box.append(installing_label)

        self.progress_label = Gtk.Label(label="Inizializzazione...")
        self.progress_label.add_css_class("dim-label")
        installing_box.append(self.progress_label)

        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        installing_box.append(self.progress_bar)

        self.stack.add_named(installing_box, "installing")

        toolbox.set_content(self.stack)
        self.set_content(toolbox)

    def _initial_check(self):
        """Controllo iniziale degli aggiornamenti."""
        self._check_updates()
        return False

    def _on_refresh_clicked(self, button):
        """Ricontrolla gli aggiornamenti."""
        self._check_updates(use_cache=False)

    def _check_updates(self, use_cache=True):
        """Controlla gli aggiornamenti."""
        if self.checking:
            return

        self.checking = True
        self.refresh_button.set_sensitive(False)
        self.install_button.set_sensitive(False)
        self.stack.set_visible_child_name("checking")

        def check():
            updates = self.manager.check_updates(use_cache=use_cache)
            GLib.idle_add(self._show_updates, updates)

        import threading
        threading.Thread(target=check, daemon=True).start()

    def _show_updates(self, updates):
        """Mostra gli aggiornamenti trovati."""
        self.checking = False
        self.refresh_button.set_sensitive(True)

        # Pulisce la lista
        child = self.updates_list.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.updates_list.remove(child)
            child = next_child
        self.update_rows = []

        if not updates:
            # Nessun aggiornamento
            if self.manager.last_check:
                self.last_check_label.set_text(
                    f"Ultimo controllo: {self.manager.last_check.strftime('%H:%M:%S')}"
                )
            self.stack.set_visible_child_name("no-updates")

            # Leggi a voce
            speak("Nessun aggiornamento disponibile. Il sistema è aggiornato.")
            return

        # Mostra riepilogo
        summary = self.manager.get_summary()
        summary_text = f"{summary['total']} aggiornamenti disponibili"
        if summary['security'] > 0:
            summary_text += f" • {summary['security']} di sicurezza"
        summary_text += f" • {format_size(summary['total_size'])}"

        self.summary_banner.set_title(summary_text)
        self.summary_banner.set_revealed(True)

        # Aggiungi aggiornamenti alla lista
        for update in updates:
            row = UpdateRow(update)
            self.updates_list.append(row)
            self.update_rows.append(row)

        self.install_button.set_sensitive(True)
        self.stack.set_visible_child_name("updates")

        # Leggi riepilogo a voce
        speak(self.manager.get_speech_summary())

    def _on_install_clicked(self, button):
        """Installa gli aggiornamenti selezionati."""
        if self.installing:
            return

        # Raccoglie aggiornamenti selezionati
        selected = [row.update for row in self.update_rows if row.selected]

        if not selected:
            # Nessun aggiornamento selezionato
            dialog = Adw.MessageDialog.new(self)
            dialog.set_heading("Nessun aggiornamento selezionato")
            dialog.set_body("Seleziona almeno un aggiornamento da installare.")
            dialog.add_response("ok", "OK")
            dialog.present()
            return

        # Conferma installazione
        summary = f"Verranno installati {len(selected)} aggiornamenti"
        if any(u.requires_reboot for u in selected):
            summary += ".\n\nAlcuni aggiornamenti richiedono il riavvio del sistema."

        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading("Conferma installazione")
        dialog.set_body(summary)
        dialog.add_response("cancel", "Annulla")
        dialog.add_response("install", "Installa")
        dialog.set_response_appearance("install", Adw.ResponseAppearance.SUGGESTED)
        dialog.connect("response", self._on_install_confirmed, selected)
        dialog.present()

    def _on_install_confirmed(self, dialog, response, selected):
        """Installazione confermata."""
        if response != "install":
            return

        self.installing = True
        self.refresh_button.set_sensitive(False)
        self.install_button.set_sensitive(False)
        self.stack.set_visible_child_name("installing")

        speak("Installazione in corso")

        def progress_callback(name, current, total):
            GLib.idle_add(self._update_progress, name, current, total)

        def install():
            success, message = self.manager.install_updates(selected, progress_callback)
            GLib.idle_add(self._installation_done, success, message, selected)

        import threading
        threading.Thread(target=install, daemon=True).start()

    def _update_progress(self, package_name, current, total):
        """Aggiorna la barra di avanzamento."""
        fraction = current / total
        self.progress_bar.set_fraction(fraction)
        self.progress_bar.set_text(f"{current} di {total}")
        self.progress_label.set_text(f"Installazione: {package_name}")

        # Leggi a voce (ogni 5 pacchetti)
        if current % 5 == 0 or current == total:
            speak(f"{current} di {total}")

    def _installation_done(self, success, message, installed_updates):
        """Installazione completata."""
        self.installing = False
        self.refresh_button.set_sensitive(True)

        if success:
            # Successo
            dialog = Adw.MessageDialog.new(self)
            dialog.set_heading("Installazione completata")
            dialog.set_body(message)

            # Controlla se serve riavvio
            if any(u.requires_reboot for u in installed_updates):
                dialog.add_response("later", "Riavvia più tardi")
                dialog.add_response("reboot", "Riavvia ora")
                dialog.set_response_appearance("reboot", Adw.ResponseAppearance.SUGGESTED)
                dialog.connect("response", self._on_reboot_response)
            else:
                dialog.add_response("ok", "OK")

            dialog.present()

            speak("Installazione completata con successo")

            # Ricontrolla aggiornamenti
            GLib.timeout_add(1000, lambda: self._check_updates(use_cache=True))
        else:
            # Errore
            dialog = Adw.MessageDialog.new(self)
            dialog.set_heading("Errore durante l'installazione")
            dialog.set_body(message)
            dialog.add_response("ok", "OK")
            dialog.present()

            speak("Errore durante l'installazione")

            self.stack.set_visible_child_name("updates")

    def _on_reboot_response(self, dialog, response):
        """Gestisce la risposta al riavvio."""
        if response == "reboot":
            # Riavvia il sistema
            subprocess.run(["systemctl", "reboot"], check=False)


class UpdateApplication(Adw.Application):
    """Applicazione VabaxOS Update."""

    def __init__(self):
        super().__init__(
            application_id="org.vabaxos.Update",
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )

    def do_activate(self):
        """Attiva l'applicazione."""
        win = self.get_active_window()
        if not win:
            win = UpdateWindow(application=self)
        win.present()


def main():
    """Entry point dell'applicazione."""
    import sys
    app = UpdateApplication()
    return app.run(sys.argv)
