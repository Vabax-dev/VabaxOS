# SPDX-FileCopyrightText: 2026 Vabax and VabaxOS contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""What the VabaxOS Start menu contains, and its search (block 12).

Categories, in order: Favorites, Programs (divided as in Windows: Office,
Internet, Music and video...), VabaxOS tools, Settings (the pages of GNOME
Settings), Folders, Recent files, Power. Every entry is an Entry: a name,
what it is ("program", "setting"...), and how it opens. The search looks
in names, then in generic names, keywords and descriptions.
"""

import gettext
import os
import subprocess
import unicodedata

from gi.repository import Gio, GLib

_ = gettext.gettext


def N_(text):
    return text


# freedesktop main categories -> the VabaxOS subcategories of Programs.
PROGRAM_GROUPS = [
    ("office", N_("Office"), ("Office",)),
    ("internet", N_("Internet"), ("Network", "WebBrowser", "Email", "Chat")),
    ("media", N_("Music and video"), ("AudioVideo", "Audio", "Video")),
    ("graphics", N_("Graphics"), ("Graphics",)),
    ("accessibility", N_("Accessibility"), ("Accessibility",)),
    ("games", N_("Games"), ("Game",)),
    ("education", N_("Education"), ("Education", "Science")),
    ("development", N_("Development"), ("Development",)),
    ("accessories", N_("Accessories"), ("Utility", "TextEditor", "Archiving", "Calculator")),
    ("system", N_("System"), ("System", "Settings", "Monitor", "TerminalEmulator", "PackageManager")),
]
OTHER_GROUP = ("other", N_("Other programs"))

FOLDERS = [
    (N_("Home folder"), None),
    (N_("Desktop"), GLib.UserDirectory.DIRECTORY_DESKTOP),
    (N_("Documents"), GLib.UserDirectory.DIRECTORY_DOCUMENTS),
    (N_("Downloads"), GLib.UserDirectory.DIRECTORY_DOWNLOAD),
    (N_("Music"), GLib.UserDirectory.DIRECTORY_MUSIC),
    (N_("Pictures"), GLib.UserDirectory.DIRECTORY_PICTURES),
    (N_("Videos"), GLib.UserDirectory.DIRECTORY_VIDEOS),
]

POWER = [
    ("lock", N_("Lock"), ["gdbus", "call", "--session", "--dest", "org.gnome.ScreenSaver", "--object-path",
                          "/org/gnome/ScreenSaver", "--method", "org.gnome.ScreenSaver.Lock"]),
    ("logout", N_("Log out"), ["gnome-session-quit", "--logout"]),
    ("suspend", N_("Suspend"), ["systemctl", "suspend"]),
    ("restart", N_("Restart"), ["gnome-session-quit", "--reboot"]),
    ("poweroff", N_("Power off"), ["gnome-session-quit", "--power-off"]),
]


class Entry:
    """One thing the menu can open, or a category with children."""

    def __init__(self, name, kind, open_=None, children=None, search_text="", ident=None):
        self.name = name
        self.kind = kind  # translated: "program", "setting", "folder"...
        self.open = open_
        self.children = children
        self.search_text = search_text
        self.ident = ident or name

    @property
    def is_category(self):
        return self.children is not None

    def __repr__(self):
        return f"Entry({self.name!r}, {self.kind!r}, {len(self.children) if self.children else ''})"


def fold(text):
    """Lower case, without accents: «perché» finds «perche»."""
    text = unicodedata.normalize("NFD", text or "").lower()
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def launcher(app):
    return lambda context=None: app.launch([], context)


def app_entry(app, kind):
    words = [app.get_generic_name() or "", " ".join(app.get_keywords() or []), app.get_description() or "",
             app.get_id() or ""]
    return Entry(app.get_display_name(), kind, launcher(app), search_text=fold(" ".join(words)),
                 ident=app.get_id())


def uri_opener(uri):
    return lambda context=None: Gio.AppInfo.launch_default_for_uri(uri, context)


def command_runner(command):
    return lambda context=None: subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def all_apps():
    return [a for a in Gio.AppInfo.get_all() if isinstance(a, Gio.DesktopAppInfo) and a.should_show()]


def settings_panels():
    """The pages of GNOME Settings, from their launchers (hidden in menus)."""
    panels = []
    for app in Gio.AppInfo.get_all():
        ident = app.get_id() or ""
        if isinstance(app, Gio.DesktopAppInfo) and ident.startswith("gnome-") and ident.endswith("-panel.desktop"):
            panels.append(app)
    return sorted(panels, key=lambda a: fold(a.get_display_name()))


def program_group(app):
    categories = set((app.get_categories() or "").split(";"))
    for ident, title, names in PROGRAM_GROUPS:
        if ident == "accessibility" and "Accessibility" in categories:
            return ident, title
    for ident, title, names in PROGRAM_GROUPS:
        if categories & set(names):
            return ident, title
    return OTHER_GROUP


def favorites(apps):
    source = Gio.SettingsSchemaSource.get_default()
    if source is None or source.lookup("org.gnome.shell", True) is None:
        return []  # without the schema Gio.Settings would abort the program
    wanted = list(Gio.Settings.new("org.gnome.shell").get_strv("favorite-apps"))
    by_id = {a.get_id(): a for a in apps}
    return [by_id[i] for i in wanted if i in by_id]


def recent_files(limit=15):
    try:
        import gi
        gi.require_version("Gtk", "4.0")
        from gi.repository import Gtk
        items = Gtk.RecentManager.get_default().get_items()
    except (ImportError, ValueError):
        return []
    items = [i for i in items if i.exists()]
    items.sort(key=lambda i: i.get_modified().to_unix(), reverse=True)
    return items[:limit]


def build(apps=None, panels=None, recent=None):
    """The categories of the menu: a list of Entry with children."""
    apps = all_apps() if apps is None else apps
    panels = settings_panels() if panels is None else panels
    recent = recent_files() if recent is None else recent
    program, setting = _("program"), _("setting")

    vabaxos = [a for a in apps if (a.get_id() or "").startswith("org.vabaxos.")]
    groups = {}
    for app in apps:
        ident, title = program_group(app)
        groups.setdefault((ident, title), []).append(app_entry(app, program))
    order = [(i, t) for i, t, _n in PROGRAM_GROUPS] + [OTHER_GROUP]
    program_categories = [Entry(_(title), _("category"), children=sorted(groups[(ident, title)],
                                                                       key=lambda e: fold(e.name)),
                                ident="programs/" + ident)
                          for ident, title in order if (ident, title) in groups]

    folders = []
    for title, special in FOLDERS:
        path = GLib.get_home_dir() if special is None else GLib.get_user_special_dir(special)
        if path and os.path.isdir(path):
            folders.append(Entry(_(title), _("folder"), uri_opener(GLib.filename_to_uri(path)),
                                 search_text=fold(os.path.basename(path)), ident="folder:" + path))
    folders.append(Entry(_("Trash"), _("folder"), uri_opener("trash:///"), ident="folder:trash"))

    categories = [
        Entry(_("Favorites"), _("category"), children=[app_entry(a, program) for a in favorites(apps)],
              ident="favorites"),
        Entry(_("Programs"), _("category"), children=program_categories, ident="programs"),
        Entry(_("VabaxOS tools"), _("category"), children=sorted((app_entry(a, program) for a in vabaxos),
                                                                  key=lambda e: fold(e.name)), ident="vabaxos"),
        Entry(_("Settings"), _("category"), children=[app_entry(p, setting) for p in panels], ident="settings"),
        Entry(_("Folders"), _("category"), children=folders, ident="folders"),
        Entry(_("Recent files"), _("category"),
              children=[Entry(i.get_display_name(), _("file"), uri_opener(i.get_uri()),
                              search_text=fold(i.get_display_name()), ident="recent:" + i.get_uri())
                        for i in recent], ident="recent"),
        Entry(_("Power"), _("category"), children=[Entry(_(title), _("command"), command_runner(command),
                                                         ident="power:" + ident)
                                                   for ident, title, command in POWER], ident="power"),
    ]
    return [c for c in categories if c.children]


def leaves(entries):
    for entry in entries:
        if entry.is_category:
            yield from leaves(entry.children)
        else:
            yield entry


def search(categories, text, limit=30):
    """Entries matching text: the name starts with it, then a word of the
    name starts with it, then the name contains it, then the other words."""
    query = fold(text).strip()
    if not query:
        return []
    ranked, seen = [], set()
    for entry in leaves(categories):
        if entry.ident in seen:
            continue
        name = fold(entry.name)
        if name.startswith(query):
            rank = 0
        elif any(word.startswith(query) for word in name.split()):
            rank = 1
        elif query in name:
            rank = 2
        elif query in entry.search_text:
            rank = 3
        else:
            continue
        seen.add(entry.ident)
        ranked.append((rank, name, entry))
    ranked.sort(key=lambda item: (item[0], item[1]))
    return [entry for _rank, _name, entry in ranked[:limit]]
