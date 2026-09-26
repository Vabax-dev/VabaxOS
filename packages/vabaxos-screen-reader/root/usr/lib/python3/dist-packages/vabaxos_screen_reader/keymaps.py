# SPDX-FileCopyrightText: 2026 Vabax and VabaxOS contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Key schemes for Orca (block 10): NVDA (the VabaxOS default), JAWS, and
Orca's own keys.

Orca 50 keeps user keys in dconf, org.gnome.Orca.Keybindings "entries":
{command: [[keysym, mask, modifiers, clicks]]}, all strings. A command has
one key: an override replaces Orca's key for that command, in both keyboard
layouts. So every scheme below chooses the key people from NVDA or JAWS
press most, also on laptops without a number pad; the number pad review
keys of Orca are already those of NVDA (7 8 9 lines, 4 5 6 words, 1 2 3
characters) and stay as they are.

A key here is (keysym, modifiers, clicks); modifiers: O the screen reader
key (Insert, or Caps Lock), C Ctrl, A Alt, S Shift.
"""

from .orca_commands import COMMANDS

S, C, A, O = 1, 4, 8, 256
# Orca's DEFAULT_MODIFIER_MASK (Shift, Ctrl, Alt, Meta3, AltGr, Orca).
MASK = "461"

# Both schemes: the lists of JAWS (Insert+F7 links, F6 headings, F5 form
# fields, Insert+Ctrl+letter) and the voice ring of NVDA (Insert+Ctrl+arrows).
COMMON = {
    "sayAllHandler": ("Down", O, 1),
    "reviewCurrentLineHandler": ("Up", O, 1),
    "whereAmIBasicHandler": ("Tab", O, 1),
    "whereAmIDetailedHandler": ("Tab", O, 2),
    "getTitleHandler": ("t", O, 1),
    "presentTimeHandler": ("F12", O, 1),
    "presentDateHandler": ("F12", O, 2),
    "flatReviewSayAllHandler": ("b", O, 1),
    "present_clipboard_contents": ("c", O, 1),
    "presentSizeAndPositionHandler": ("Delete", O, 1),
    "present_battery_status": ("b", O | S, 1),
    "whereAmILinkHandler": ("k", O, 1),
    "present_last_notification": ("n", O | S, 1),
    "show_notification_list": ("n", O | C | S, 1),
    "cycleKeyEchoHandler": ("2", O, 1),
    "cycleSpeakingPunctuationLevelHandler": ("p", O, 1),
    "enterLearnModeHandler": ("1", O, 1),
    "cycleSettingsProfileHandler": ("p", O | C, 1),
    "presentCurrentProfileHandler": ("p", O | S, 1),
    "increaseSpeechRateHandler": ("Up", O | C, 1),
    "decreaseSpeechRateHandler": ("Down", O | C, 1),
    "increaseSpeechVolumeHandler": ("Right", O | C, 1),
    "decreaseSpeechVolumeHandler": ("Left", O | C, 1),
    "increaseSpeechPitchHandler": ("Page_Up", O | C, 1),
    "decreaseSpeechPitchHandler": ("Page_Down", O | C, 1),
    "cycleCapitalizationStyleHandler": ("F8", O, 1),
    # Orca's Insert+F12 (caret navigation on and off) leaves room for the time.
    "toggle_enabled": ("F12", O | S, 1),
    "present_cpu_and_memory_usage": ("F11", O | S, 1),
    "list_links": ("F7", O, 1),
    "list_headings": ("F6", O, 1),
    "list_form_fields": ("F5", O, 1),
    "list_buttons": ("b", O | C, 1),
    "list_tables": ("t", O | C, 1),
    "list_landmarks": ("semicolon", O | C, 1),
    "list_lists": ("l", O | C, 1),
    "list_images": ("g", O | C, 1),
    "list_radio_buttons": ("r", O | C, 1),
    "list_checkboxes": ("x", O | C, 1),
    "list_comboboxes": ("c", O | C, 1),
    "list_entries": ("e", O | C, 1),
}

# The voice ring takes Insert+Ctrl+arrows, where Orca has object
# navigation: it moves to NVDA's keys, the number pad with Insert on a
# desktop keyboard, Insert+Shift+arrows on a laptop.
OBJECT_NAVIGATION = {
    "desktop": {
        "object_navigator_up": ("KP_Up", O, 1),
        "object_navigator_down": ("KP_Down", O, 1),
        "object_navigator_previous": ("KP_Left", O, 1),
        "object_navigator_next": ("KP_Right", O, 1),
        "object_navigator_perform_action": ("KP_Enter", O, 1),
        "reviewAboveHandler": ("KP_Left", O | S, 1),
        "reviewBelowHandler": ("KP_Right", O | S, 1),
    },
    "laptop": {
        "object_navigator_up": ("Up", O | S, 1),
        "object_navigator_down": ("Down", O | S, 1),
        "object_navigator_previous": ("Left", O | S, 1),
        "object_navigator_next": ("Right", O | S, 1),
        "object_navigator_perform_action": ("Return", O | S, 1),
        "whereAmISelectionHandler": ("s", O | S, 1),
    },
}

NVDA = {
    **COMMON,
    "getStatusBarHandler": ("End", O, 1),
    "toggle_presentation_mode": ("space", O, 1),
    "preferencesSettingsHandler": ("n", O, 1),
    "appPreferencesSettingsHandler": ("n", O | C, 1),
    "shutdownHandler": ("q", O, 1),
    "bypass_mode_toggle": ("F2", O, 1),
    # The quick keys of NVDA's browse mode (block 14): D landmarks, M
    # frames. Orca has M for landmarks and D for live regions, which NVDA
    # does not have: they go to J (Y stays the last live region).
    "next_landmark": ("d", 0, 1),
    "previous_landmark": ("d", S, 1),
    "next_iframe": ("m", 0, 1),
    "previous_iframe": ("m", S, 1),
    "next_live_region": ("j", 0, 1),
    "previous_live_region": ("j", S, 1),
}
NVDA_LAYOUT = {
    "desktop": {"toggle_sleep_mode": ("s", O | S, 1)},
    "laptop": {"toggle_sleep_mode": ("z", O | S, 1)},
}

JAWS = {
    **COMMON,
    "getStatusBarHandler": ("Page_Down", O, 1),
    "toggle_presentation_mode": ("z", O, 1),
    "structural_navigator_mode_cycle": ("z", O | S, 1),
    "preferencesSettingsHandler": ("j", O, 1),
    "appPreferencesSettingsHandler": ("j", O | C, 1),
    "shutdownHandler": ("F4", O, 1),
    "bypass_mode_toggle": ("3", O, 1),
    "toggle_sleep_mode": ("s", O | S, 1),
}

SCHEMES = ["nvda", "jaws", "orca"]
DEFAULT_SCHEME = "nvda"
# The screen reader key of each scheme, for the desktop layout: Insert, as
# NVDA does by default. Not Caps Lock: under Wayland Orca 50 does not ask
# Mutter to hold it back (its SetKeyGrabs lists only Insert), so every press
# also switched capital letters on (found in QEMU, 2026-09-26). It can still
# be chosen in the Keyboard page.
MODIFIERS = {
    "nvda": ["Insert", "KP_Insert"],
    "jaws": ["Insert", "KP_Insert"],
    "orca": ["Insert", "KP_Insert"],
}


# On a laptop Orca reviews the screen with the screen reader key and the
# letters (U I O, J K L, M comma period, P, semicolon): the keys that would
# take those move, or stay Orca's (None).
LAPTOP = {
    "whereAmILinkHandler": ("k", O | S, 1),
    "cycleSpeakingPunctuationLevelHandler": ("p", O | A, 1),
    "list_lists": None,
}
JAWS_LAPTOP = {
    "preferencesSettingsHandler": None,
    "appPreferencesSettingsHandler": None,
    "toggle_sleep_mode": None,
}


def overrides(scheme, layout="desktop"):
    """{command: key} a scheme changes, for a keyboard layout."""
    if scheme == "orca":
        return {}
    keys = dict(NVDA if scheme == "nvda" else JAWS)
    keys.update(OBJECT_NAVIGATION[layout])
    if scheme == "nvda":
        keys.update(NVDA_LAYOUT[layout])
    if layout == "laptop":
        keys.update(LAPTOP)
        if scheme == "jaws":
            keys.update(JAWS_LAPTOP)
    return {name: key for name, key in keys.items() if key is not None}


def entries(scheme, layout="desktop"):
    """The value of org.gnome.Orca.Keybindings entries for a scheme."""
    return {name: [[keysym, MASK, str(mods), str(clicks)]]
            for name, (keysym, mods, clicks) in overrides(scheme, layout).items()}


def defaults(layout="desktop"):
    """{command: key or None}: Orca's own keys."""
    index = 3 if layout == "desktop" else 4
    return {row[0]: row[index] for row in COMMANDS}


def effective(user_entries, layout="desktop"):
    """{command: key or None} with the user's entries over Orca's keys."""
    keys = defaults(layout)
    for name, bindings in user_entries.items():
        if name not in keys:
            continue
        if not bindings or not bindings[-1] or not bindings[-1][0]:
            keys[name] = None
        else:
            keysym, _mask, mods, clicks = bindings[-1]
            keys[name] = (keysym, int(mods), int(clicks))
    return keys


def conflicts(keys, changed=None):
    """[(key, [commands])] with the same key for more than one command.
    With changed (a set of commands), only conflicts involving them: Orca's
    own keys overlap on purpose (for example the arrows, in caret
    navigation and in its modes)."""
    by_key = {}
    for name, key in keys.items():
        if key is not None:
            by_key.setdefault(key, []).append(name)
    found = []
    for key, names in sorted(by_key.items()):
        if len(names) > 1 and (changed is None or set(names) & set(changed)):
            found.append((key, sorted(names)))
    return found


KEY_NAMES = {
    "Up": "Freccia su", "Down": "Freccia giù", "Left": "Freccia sinistra", "Right": "Freccia destra",
    "Page_Up": "Pagina su", "Page_Down": "Pagina giù", "Home": "Inizio", "End": "Fine",
    "Delete": "Canc", "Return": "Invio", "Tab": "Tab", "space": "Spazio", "BackSpace": "Backspace",
    "Escape": "Esc", "semicolon": "Punto e virgola", "comma": "Virgola", "period": "Punto",
    "slash": "Barra", "backslash": "Barra rovesciata", "equal": "Uguale", "minus": "Meno",
    "apostrophe": "Apostrofo", "bracketleft": "Parentesi quadra aperta",
    "bracketright": "Parentesi quadra chiusa", "KP_Enter": "Invio del tastierino",
    "KP_Add": "Più del tastierino", "KP_Subtract": "Meno del tastierino",
    "KP_Multiply": "Per del tastierino", "KP_Divide": "Diviso del tastierino",
    "KP_Delete": "Canc del tastierino", "KP_Insert": "Ins del tastierino",
    "KP_Up": "8 del tastierino", "KP_Down": "2 del tastierino", "KP_Left": "4 del tastierino",
    "KP_Right": "6 del tastierino", "KP_Home": "7 del tastierino", "KP_End": "1 del tastierino",
    "KP_Page_Up": "9 del tastierino", "KP_Page_Down": "3 del tastierino", "KP_Begin": "5 del tastierino",
}
KEY_NAMES_EN = {
    "Page_Up": "Page Up", "Page_Down": "Page Down", "Return": "Enter", "space": "Space",
    "KP_Enter": "keypad Enter", "KP_Add": "keypad Plus", "KP_Subtract": "keypad Minus",
    "KP_Multiply": "keypad Times", "KP_Divide": "keypad Divide", "KP_Delete": "keypad Delete",
    "KP_Up": "keypad 8", "KP_Down": "keypad 2", "KP_Left": "keypad 4", "KP_Right": "keypad 6",
    "KP_Home": "keypad 7", "KP_End": "keypad 1", "KP_Page_Up": "keypad 9",
    "KP_Page_Down": "keypad 3", "KP_Begin": "keypad 5",
}


def label(key, italian=True, orca_key=None):
    """A key as people say it: «Ins+Maiusc+T, due volte»."""
    if key is None:
        return "nessun tasto" if italian else "no key"
    keysym, mods, clicks = key
    parts = []
    if mods & O:
        parts.append(orca_key or ("Ins" if italian else "Insert"))
    if mods & C:
        parts.append("Ctrl")
    if mods & A:
        parts.append("Alt")
    if mods & S:
        parts.append("Maiusc" if italian else "Shift")
    names = KEY_NAMES if italian else KEY_NAMES_EN
    parts.append(names.get(keysym, keysym.upper() if len(keysym) == 1 else keysym))
    text = "+".join(parts)
    if clicks == 2:
        text += ", due volte" if italian else ", twice"
    elif clicks == 3:
        text += ", tre volte" if italian else ", three times"
    return text


def gvariant_entries(value):
    """entries as GVariant text, for a dconf keyfile."""
    items = ", ".join("'%s': [%s]" % (name, ", ".join("[%s]" % ", ".join("'%s'" % part for part in binding)
                                                     for binding in bindings))
                      for name, bindings in sorted(value.items()))
    return "{" + items + "}"


def dconf_defaults(scheme=DEFAULT_SCHEME):
    """The dconf keyfile that makes a scheme the default for everyone."""
    modifiers = ", ".join("'%s'" % key for key in MODIFIERS[scheme])
    return ("# VabaxOS: Orca's keys, the %s scheme (block 10), for the default profile.\n"
            "# Written by vabaxos_screen_reader.keymaps --dconf when the package is built.\n"
            "[org/gnome/orca/default/keybindings]\n"
            "entries=%s\n"
            "desktop-modifier-keys=[%s]\n" % (scheme.upper(), gvariant_entries(entries(scheme)), modifiers))


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["--dconf"]:
        sys.stdout.write(dconf_defaults())
    else:
        sys.exit("usage: python3 -m vabaxos_screen_reader.keymaps --dconf")
