"""The lessons of the keys of VabaxOS, as data, and how a key press is
checked (vabaxos-lessons).

An exercise is "press": the program hears the key and says whether it is
the right one; or "try": a key that GNOME Shell or the screen reader take
before any program (Super, Alt+Tab, Orca+T...), so the program explains
it, the user tries it, and its effect is the answer.
"""

import gettext


def _(text):
    return gettext.dgettext("vabaxos-lessons", text)


def N_(text):
    return text


class Exercise:
    def __init__(self, key, name, does, kind="press"):
        self.key = key        # a GTK accelerator, such as "<Control>c"
        self.name = name      # how the key is said, such as "Ctrl+C"
        self.does = does      # what it does
        self.kind = kind

    def instruction(self):
        if self.kind == "try":
            return _("Try {key}: {does}. Then come back here and press Enter.").format(
                key=_(self.name), does=_(self.does))
        return _("Press {key}: {does}.").format(key=_(self.name), does=_(self.does))


LESSONS = [
    (N_("Moving in a window"), [
        Exercise("Tab", N_("Tab"), N_("goes to the next control")),
        Exercise("<Shift>Tab", N_("Shift+Tab"), N_("goes back to the control before")),
        Exercise("Down", N_("Down Arrow"), N_("moves down in a list or a menu")),
        Exercise("Up", N_("Up Arrow"), N_("moves up")),
        Exercise("space", N_("Space"), N_("presses a button or changes a switch")),
        Exercise("Return", N_("Enter"), N_("opens or confirms")),
        Exercise("Escape", N_("Escape"), N_("closes a menu or a message, or goes back")),
        Exercise("F6", N_("F6"), N_("goes to the next part of the window")),
    ]),
    (N_("Writing and correcting"), [
        Exercise("Home", N_("Home"), N_("goes to the start of the line")),
        Exercise("End", N_("End"), N_("goes to the end of the line")),
        Exercise("<Control>Right", N_("Ctrl+Right Arrow"), N_("goes to the next word")),
        Exercise("<Control>Left", N_("Ctrl+Left Arrow"), N_("goes to the word before")),
        Exercise("BackSpace", N_("Backspace"), N_("deletes the letter before the cursor")),
        Exercise("Delete", N_("Delete"), N_("deletes the letter after the cursor")),
        Exercise("<Control>z", N_("Ctrl+Z"), N_("undoes the last change")),
    ]),
    (N_("Copy and paste"), [
        Exercise("<Control>a", N_("Ctrl+A"), N_("selects everything")),
        Exercise("<Control>c", N_("Ctrl+C"), N_("copies")),
        Exercise("<Control>x", N_("Ctrl+X"), N_("cuts")),
        Exercise("<Control>v", N_("Ctrl+V"), N_("pastes")),
        Exercise("<Control>s", N_("Ctrl+S"), N_("saves")),
    ]),
    (N_("Windows and the desktop"), [
        Exercise("", N_("Super"), N_("opens the Start menu; Escape closes it"), "try"),
        Exercise("", N_("Alt+Tab"), N_("goes from one window to another"), "try"),
        Exercise("", N_("Super+T"), N_("goes to the programs of the taskbar"), "try"),
        Exercise("", N_("Super+D"), N_("shows the desktop; again, the windows come back"), "try"),
        Exercise("", N_("Super+Alt+I"), N_("says time, battery, network and volume"), "try"),
        Exercise("", N_("Super+Alt+D"), N_("says where you are"), "try"),
    ]),
    (N_("The screen reader"), [
        Exercise("", N_("Insert+T"), N_("says the title of the window"), "try"),
        Exercise("", N_("Insert+Tab"), N_("says the control that has the focus"), "try"),
        Exercise("", N_("Insert+Up Arrow"), N_("reads the current line"), "try"),
        Exercise("", N_("Insert+F12"), N_("says the time"), "try"),
        Exercise("", N_("Control"), N_("stops the voice"), "try"),
        Exercise("", N_("Insert+1"), N_("learn mode: every key says what it does, Escape goes out"), "try"),
    ]),
    (N_("VabaxOS tools"), [
        Exercise("", N_("Super+H"), N_("dictation: speak, then Super+H again, and the text is written"), "try"),
        Exercise("", N_("Super+Alt+R"), N_("reads the text of the window when the screen reader finds nothing"),
                 "try"),
        Exercise("", N_("Super+Alt+N"), N_("do not disturb on and off"), "try"),
    ]),
]

MODIFIERS = ("<Control>", "<Shift>", "<Alt>", "<Super>")


def normalize(name, mods):
    """A key press as an accelerator text, as in LESSONS: the key name and
    the modifiers held (a set of "Control", "Shift", "Alt", "Super")."""
    if name == "ISO_Left_Tab":
        name, mods = "Tab", set(mods) | {"Shift"}
    if len(name) == 1:
        name = name.lower()
    prefix = "".join(f"<{m}>" for m in ("Control", "Shift", "Alt", "Super") if m in mods)
    return prefix + name


def matches(exercise, name, mods):
    return exercise.kind == "press" and normalize(name, mods) == exercise.key


def said(name, mods):
    """A key press as words, for "you pressed ..."."""
    parts = [{"Control": "Ctrl", "Shift": _("Shift"), "Alt": "Alt", "Super": "Super"}[m]
             for m in ("Control", "Shift", "Alt", "Super") if m in mods]
    names = {"Return": _("Enter"), "space": _("Space"), "Escape": _("Escape"), "BackSpace": _("Backspace"),
             "Delete": _("Delete"), "Up": _("Up Arrow"), "Down": _("Down Arrow"), "Left": _("Left Arrow"),
             "Right": _("Right Arrow"), "Home": _("Home"), "End": _("End"), "Tab": "Tab",
             "ISO_Left_Tab": "Tab"}
    return "+".join(parts + [names.get(name, name.upper() if len(name) == 1 else name)])
