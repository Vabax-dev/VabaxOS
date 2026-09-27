#!/usr/bin/env python3
"""Lists Orca's keyboard commands as JSON (block 10, ADR-0027): handler
name -> group, description, desktop key, laptop key, from the default
script and the web script (browse mode). Groups are the English labels of
Orca's own list of shortcuts. Runs Orca's own code, so it needs Orca 48
and a session bus with the accessibility bus:

    dbus-run-session -- sh -c '/usr/libexec/at-spi-bus-launcher --launch-immediately &
        sleep 2; cd /usr/lib/python3/dist-packages && python3 .../orca-commands.py > orca48.json'

packages/vabaxos-screen-reader/.../orca_commands.py is made from its output.
"""
import json, sys
import gi
gi.require_version("Atspi", "2.0")
from orca import orca as _orca  # the import order of Orca itself
from orca import settings, settings_manager
from orca.scripts import default
from orca.scripts.web import script as web

settings_manager.get_manager().activate()
GROUPS = [  # (getter, English group label)
    ("get_where_am_i_presenter", "Object details"), ("get_speech_and_verbosity_manager", "Speech and verbosity"),
    ("get_flat_review_presenter", "Flat review"), ("get_flat_review_finder", "Find"),
    ("get_object_navigator", "Object navigation"), ("get_table_navigator", "Table navigation"),
    ("get_system_information_presenter", "System information"), ("get_notification_presenter", "Notification presenter"),
    ("get_clipboard_presenter", "Clipboard"), ("get_learn_mode_presenter", "Learn mode"),
    ("get_mouse_reviewer", "Mouse review"), ("get_action_presenter", "Actions"),
    ("get_debugging_tools_manager", "Debugging Tools"), ("get_bypass_mode_manager", "Default"),
    ("get_caret_navigation", "Caret navigation"), ("get_live_region_manager", "Live regions"),
]
out = {}
for cls in (default.Script, web.Script):
    for layout, lname in ((settings.GENERAL_KEYBOARD_LAYOUT_DESKTOP, "desktop"),
                          (settings.GENERAL_KEYBOARD_LAYOUT_LAPTOP, "laptop")):
        settings.keyboardLayout = layout
        s = cls(None)
        # Keys first: asking a module for its handlers may make new ones.
        names = {id(h): n for n, h in s.input_event_handlers.items()}
        keys = {}
        for b in s.get_key_bindings(enabled_only=False).key_bindings:
            n = names.get(id(b.handler))
            if n and b.keysymstring and n not in keys:
                keys[n] = [b.keysymstring, b.modifiers, b.click_count]
        group_of = {}
        for getter, label in GROUPS:
            f = getattr(s, getter, None)
            try:
                handlers = f().get_handlers() if f else {}
            except Exception:
                handlers = {}
            for n in handlers:
                group_of.setdefault(n, label)
        if hasattr(s, "bookmarks"):
            for n in s.bookmarks.get_handlers():
                group_of.setdefault(n, "Bookmarks")
        if hasattr(s, "structural_navigation"):
            for n in s.structural_navigation.get_handlers():
                group_of.setdefault(n, "Structural navigation")
        for n, h in s.input_event_handlers.items():
            entry = out.setdefault(n, {"group": group_of.get(n, "Default"), "description": h.description,
                                       "desktop": None, "laptop": None})
            if entry[lname] is None and n in keys:
                entry[lname] = keys[n]
json.dump(out, sys.stdout, indent=1, sort_keys=True)
