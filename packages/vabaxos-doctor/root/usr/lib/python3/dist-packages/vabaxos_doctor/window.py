"""Interfaccia grafica di VabaxOS Doctor."""

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Adw, Gio, GLib, Gtk

from . import Doctor, Status


class DoctorWindow(Adw.ApplicationWindow):
    """Finestra principale di VabaxOS Doctor."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_default_size(700, 600)
        self.set_title("Diagnostica VabaxOS")

        self.doctor = Doctor()
        self.running = False

        self._build_ui()

    def _build_ui(self):
        """Costruisce l'interfaccia."""
        # Header bar
        header = Adw.HeaderBar()

        # Pulsante per eseguire i controlli
        self.check_button = Gtk.Button(label="Esegui controlli")
        self.check_button.add_css_class("suggested-action")
        self.check_button.connect("clicked", self._on_check_clicked)
        header.pack_end(self.check_button)

        # Toolbox principale
        toolbox = Adw.ToolbarView()
        toolbox.add_top_bar(header)

        # Contenuto scorrevole
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)

        # Box principale
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.main_box.set_margin_top(24)
        self.main_box.set_margin_bottom(24)
        self.main_box.set_margin_start(24)
        self.main_box.set_margin_end(24)

        # Messaggio iniziale
        self.status_label = Gtk.Label()
        self.status_label.set_markup(
            "<big><b>Diagnostica dell'accessibilità</b></big>\n\n"
            "Premi il pulsante per controllare che tutti i componenti "
            "di accessibilità funzionino correttamente."
        )
        self.status_label.set_wrap(True)
        self.status_label.set_justify(Gtk.Justification.CENTER)
        self.main_box.append(self.status_label)

        # Spinner (nascosto inizialmente)
        self.spinner = Gtk.Spinner()
        self.spinner.set_size_request(48, 48)
        self.spinner.set_visible(False)
        self.main_box.append(self.spinner)

        # Lista dei risultati (nascosta inizialmente)
        self.results_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.results_box.set_visible(False)
        self.main_box.append(self.results_box)

        scrolled.set_child(self.main_box)
        toolbox.set_content(scrolled)
        self.set_content(toolbox)

    def _on_check_clicked(self, button):
        """Esegue i controlli diagnostici."""
        if self.running:
            return

        self.running = True
        self.check_button.set_sensitive(False)
        self.status_label.set_markup("<big><b>Controllo in corso...</b></big>")
        self.spinner.set_visible(True)
        self.spinner.start()
        self.results_box.set_visible(False)

        # Pulisce i risultati precedenti
        child = self.results_box.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.results_box.remove(child)
            child = next_child

        # Esegue i controlli in background
        def run_checks():
            results = self.doctor.run_all_checks()
            GLib.idle_add(self._show_results, results)

        import threading
        threading.Thread(target=run_checks, daemon=True).start()

    def _show_results(self, results):
        """Mostra i risultati dei controlli."""
        self.running = False
        self.check_button.set_sensitive(True)
        self.spinner.stop()
        self.spinner.set_visible(False)

        # Riepilogo
        summary = self.doctor.get_summary()
        if summary["errors"] > 0:
            status_class = "error"
            status_text = f"<big><b>Trovati {summary['errors']} problemi</b></big>"
        elif summary["warnings"] > 0:
            status_class = "warning"
            status_text = f"<big><b>Trovati {summary['warnings']} avvisi</b></big>"
        else:
            status_class = "success"
            status_text = "<big><b>Tutti i controlli superati</b></big>"

        self.status_label.set_markup(
            f"{status_text}\n\n"
            f"OK: {summary['ok']} • "
            f"Avvisi: {summary['warnings']} • "
            f"Errori: {summary['errors']}"
        )

        # Mostra i risultati dettagliati
        for result in results:
            row = self._create_result_row(result)
            self.results_box.append(row)

        self.results_box.set_visible(True)

    def _create_result_row(self, result):
        """Crea una riga per un risultato."""
        row = Adw.ExpanderRow()
        row.set_title(result.name)
        row.set_subtitle(result.message)

        # Icona di stato
        if result.status == Status.OK:
            icon_name = "emblem-ok-symbolic"
            css_class = "success"
        elif result.status == Status.WARNING:
            icon_name = "dialog-warning-symbolic"
            css_class = "warning"
        elif result.status == Status.ERROR:
            icon_name = "dialog-error-symbolic"
            css_class = "error"
        else:  # SKIPPED
            icon_name = "media-skip-forward-symbolic"
            css_class = "dim-label"

        icon = Gtk.Image.new_from_icon_name(icon_name)
        icon.add_css_class(css_class)
        row.add_prefix(icon)

        # Dettagli (se presenti)
        if result.details:
            details_label = Gtk.Label(label=result.details)
            details_label.set_wrap(True)
            details_label.set_xalign(0)
            details_label.set_margin_top(6)
            details_label.set_margin_bottom(6)
            details_label.set_margin_start(12)
            details_label.set_margin_end(12)
            details_label.add_css_class("dim-label")
            row.add_row(details_label)

        # Comando di risoluzione (se presente)
        if result.fix_command:
            fix_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            fix_box.set_margin_top(6)
            fix_box.set_margin_bottom(6)
            fix_box.set_margin_start(12)
            fix_box.set_margin_end(12)

            fix_label = Gtk.Label(label="Soluzione:")
            fix_label.add_css_class("heading")
            fix_box.append(fix_label)

            fix_command = Gtk.Label(label=result.fix_command)
            fix_command.set_wrap(True)
            fix_command.set_xalign(0)
            fix_command.set_hexpand(True)
            fix_command.add_css_class("monospace")
            fix_box.append(fix_command)

            # Pulsante per copiare il comando
            copy_button = Gtk.Button.new_from_icon_name("edit-copy-symbolic")
            copy_button.set_tooltip_text("Copia comando")
            copy_button.connect("clicked", lambda b: self._copy_to_clipboard(result.fix_command))
            fix_box.append(copy_button)

            row.add_row(fix_box)

        return row

    def _copy_to_clipboard(self, text):
        """Copia testo negli appunti."""
        clipboard = self.get_clipboard()
        clipboard.set(text)

        # Mostra toast di conferma
        toast = Adw.Toast(title="Comando copiato")
        toast.set_timeout(2)

        # Trova il ToastOverlay (se esiste)
        widget = self.get_content()
        while widget and not isinstance(widget, Adw.ToastOverlay):
            if hasattr(widget, 'get_child'):
                widget = widget.get_child()
            else:
                break


class DoctorApplication(Adw.Application):
    """Applicazione VabaxOS Doctor."""

    def __init__(self):
        super().__init__(
            application_id="org.vabaxos.Doctor",
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )

    def do_activate(self):
        """Attiva l'applicazione."""
        win = self.get_active_window()
        if not win:
            win = DoctorWindow(application=self)
        win.present()


def main():
    """Entry point dell'applicazione."""
    import sys
    app = DoctorApplication()
    return app.run(sys.argv)
