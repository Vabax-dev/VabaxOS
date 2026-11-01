"""Installing, removing and opening a program.

Debian programs go through PackageKit (GObject introspection), which asks
the administrator password in a GNOME window that Orca reads; Flathub
programs with flatpak for this user only. Every action is slow: the
window runs it in a thread; progress(percent) is called every 25 percent.
"""

import os
import subprocess

from . import App


class ActionError(RuntimeError):
    pass


class PackageKit:

    def __init__(self, client=None, pk=None):
        if client is None:
            import gi
            gi.require_version("PackageKitGlib", "1.0")
            from gi.repository import PackageKitGlib
            pk, client = PackageKitGlib, PackageKitGlib.Client()
        self.pk, self.client = pk, client

    def _ids(self, package, installed):
        filters = 1 << int(self.pk.FilterEnum.INSTALLED if installed else self.pk.FilterEnum.NOT_INSTALLED)
        results = self.client.resolve(filters, [package], None, lambda *a: None, None)
        ids = [p.get_id() for p in results.get_package_array()]
        if not ids:
            raise ActionError(package)
        # name;version;arch;repository: the computer's own architecture first.
        native = subprocess.run(["dpkg", "--print-architecture"], capture_output=True, text=True,
                                check=False).stdout.strip()
        ids.sort(key=lambda i: (i.split(";")[2] not in (native, "all") if i.count(";") >= 3 else True))
        return ids[:1]

    def _progress(self, progress):
        state = {"step": -1}

        def callback(prog, kind, _data=None):
            if progress is None or kind != self.pk.ProgressType.PERCENTAGE:
                return
            percent = prog.props.percentage
            if 25 <= percent < 100 and percent // 25 > state["step"]:
                state["step"] = percent // 25
                progress(state["step"] * 25)
        return callback

    def refresh(self):
        """Downloads the lists of programs (with them, Debian's catalog of
        applications)."""
        self.client.refresh_cache(False, None, lambda *a: None, None)

    def install(self, package, progress=None):
        flags = 1 << int(self.pk.TransactionFlagEnum.ONLY_TRUSTED)
        self.client.install_packages(flags, self._ids(package, False), None, self._progress(progress), None)

    def remove(self, package, progress=None):
        flags = 1 << int(self.pk.TransactionFlagEnum.ONLY_TRUSTED)
        # allow_deps False: never remove other programs with it.
        self.client.remove_packages(flags, self._ids(package, True), False, True, None,
                                    self._progress(progress), None)


class Actions:

    def __init__(self, packagekit=None, run=subprocess.run):
        self._packagekit = packagekit
        self.run = run

    @property
    def packagekit(self):
        if self._packagekit is None:
            self._packagekit = PackageKit()
        return self._packagekit

    def _flatpak(self, *args):
        result = self.run(["flatpak", *args], capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise ActionError(result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "flatpak")

    def refresh(self):
        self.packagekit.refresh()

    def install(self, app: App, progress=None):
        if app.source == "flathub":
            self._flatpak("install", "--user", "-y", "--noninteractive", "flathub", app.package)
        else:
            self.packagekit.install(app.package, progress)

    def remove(self, app: App, progress=None):
        if app.protected:
            raise ActionError("protected")
        if app.source == "flathub":
            self._flatpak("uninstall", "--user", "-y", "--noninteractive", app.package)
        else:
            self.packagekit.remove(app.package, progress)

    def launcher(self, app: App):
        """The desktop file id that opens the program, or None."""
        from gi.repository import Gio
        candidates = [app.id, app.id + ".desktop", app.package + ".desktop"]
        if app.id.endswith(".desktop"):
            candidates.insert(0, app.id)
        for candidate in candidates:
            try:
                info = Gio.DesktopAppInfo.new(candidate)
            except TypeError:
                info = None
            if info is not None:
                return info
        return None

    def open(self, app: App):
        info = self.launcher(app)
        if info is not None:
            info.launch([], None)
            return True
        if app.source == "flathub":
            subprocess.Popen(["flatpak", "run", app.package], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             env=dict(os.environ))
            return True
        return False
