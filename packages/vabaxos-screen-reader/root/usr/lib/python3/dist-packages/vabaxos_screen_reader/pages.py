# SPDX-FileCopyrightText: 2026 Vabax and VabaxOS contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""The pages of the screen reader settings (block 9), as data.

Every row is one Orca setting: (kind, group, key, title, subtitle, extra).
kind: "switch" (a true or false key), "number" (extra = (lower, upper,
step, digits)), "choice" (extra = [(label, value)]). The group is the dconf
folder of the setting (store.SCHEMAS); ("voice", "voices/uppercase") means
the voice used for capital letters. Labels are English; gettext translates
them (N_ marks them for xgettext).
"""


def N_(text):
    return text


SPEAK = "speech"
VOICE = ("voice", "voices/default")
UPPER = ("voice", "voices/uppercase")

PROGRESS_CHOICES = [(N_("Every program"), "all"), (N_("Only the program in use"), "application"),
                    (N_("Only the window in use"), "window")]

# Each page: (id, title, icon, description, [(group title, [rows])]).
PAGES = [
    ("voice", N_("Voice"), "audio-speakers-symbolic", N_("How the screen reader sounds"), [
        (N_("Voice"), [
            ("choice", SPEAK, "synthesizer", N_("Kind of voice"),
             N_("eSpeak NG answers at once; the natural voice sounds human but needs a fast computer"),
             [(N_("eSpeak NG, the default"), ""), (N_("Natural voice (Kokoro)"), "kokoro")]),
            ("number", VOICE, "rate", N_("Speed"), N_("From 0, slowest, to 100, fastest"), (0, 100, 5, 0)),
            ("number", VOICE, "pitch", N_("Pitch"), N_("From 0, lowest, to 10, highest"), (0, 10, 0.5, 1)),
            ("number", VOICE, "volume", N_("Volume"), N_("From 0, silent, to 10, loudest"), (0, 10, 0.5, 1)),
            ("number", UPPER, "pitch", N_("Pitch of capital letters"),
             N_("A higher pitch tells capital letters apart, as in NVDA"), (0, 10, 0.5, 1)),
        ]),
        (N_("Speaking"), [
            ("switch", SPEAK, "enable", N_("Speech"), N_("Turn off to use only braille"), None),
            ("switch", SPEAK, "insert-pauses-between-utterances", N_("Pauses between phrases"),
             N_("A short pause between one piece of information and the next"), None),
            ("switch", SPEAK, "auto-language-switching", N_("Change language by itself"),
             N_("Read each text with the voice of its language"), None),
            ("switch", SPEAK, "use-pronunciation-dictionary", N_("Pronunciation dictionary"),
             N_("Say words the way you taught the screen reader"), None),
        ]),
    ]),
    ("reading", N_("Reading"), "format-justify-left-symbolic", N_("How much the screen reader says"), [
        (N_("Amount of speech"), [
            ("choice", SPEAK, "verbosity-level", N_("Detail"), N_("Brief says less about each control"),
             [(N_("Brief"), "brief"), (N_("Detailed"), "verbose")]),
            ("choice", SPEAK, "punctuation-level", N_("Punctuation"), N_("Which punctuation marks are read"),
             [(N_("None"), "none"), (N_("Some"), "some"), (N_("Most"), "most"), (N_("All"), "all")]),
            ("choice", SPEAK, "capitalization-style", N_("Capital letters"),
             N_("How a capital letter is told apart when moving letter by letter"),
             [(N_("Nothing"), "none"), (N_("Say “capital”"), "spell"), (N_("A sound"), "icon")]),
            ("switch", SPEAK, "messages-are-detailed", N_("Detailed messages"),
             N_("Longer messages when a setting changes"), None),
            ("switch", SPEAK, "speak-tutorial-messages", N_("Usage hints"),
             N_("How to use a control, after its name"), None),
        ]),
        (N_("What is read"), [
            ("switch", SPEAK, "speak-description", N_("Descriptions"), N_("The description of a control, if it has one"), None),
            ("switch", SPEAK, "speak-position-in-set", N_("Position in lists"), N_("For example: 3 of 10"), None),
            ("switch", SPEAK, "speak-widget-mnemonic", N_("Access keys"), N_("The Alt letter that activates a control"), None),
            ("switch", SPEAK, "speak-numbers-as-digits", N_("Numbers as digits"), N_("1234 as one two three four"), None),
            ("switch", SPEAK, "use-color-names", N_("Color names"), N_("Names instead of codes"), None),
            ("switch", SPEAK, "speak-blank-lines", N_("Blank lines"), N_("Say “blank” on empty lines"), None),
            ("switch", SPEAK, "speak-misspelled-indicator", N_("Spelling mistakes"), N_("Say when a word is misspelled"), None),
            ("switch", SPEAK, "speak-indentation-and-justification", N_("Indentation"),
             N_("Spaces at the start of a line, useful for code"), None),
            ("switch", SPEAK, "only-speak-displayed-text", N_("Only the text on the screen"),
             N_("Do not say roles, states and other information"), None),
            ("number", SPEAK, "repeated-character-limit", N_("Repeated characters"),
             N_("From how many identical characters the screen reader counts them"), (0, 50, 1, 0)),
        ]),
    ]),
    ("typing", N_("Typing"), "input-keyboard-symbolic", N_("What is said while you type"), [
        (N_("Echo"), [
            ("switch", "typing-echo", "key-echo", N_("Keys"), N_("Say each key you press"), None),
            ("switch", "typing-echo", "character-echo", N_("Characters"), N_("Say each character written"), None),
            ("switch", "typing-echo", "word-echo", N_("Words"), N_("Say each word when it is complete"), None),
            ("switch", "typing-echo", "sentence-echo", N_("Sentences"), N_("Say each sentence when it is complete"), None),
        ]),
        (N_("Which keys"), [
            ("switch", "typing-echo", "alphabetic-keys", N_("Letters"), None, None),
            ("switch", "typing-echo", "numeric-keys", N_("Numbers"), None, None),
            ("switch", "typing-echo", "punctuation-keys", N_("Punctuation"), None, None),
            ("switch", "typing-echo", "space", N_("Space"), None, None),
            ("switch", "typing-echo", "modifier-keys", N_("Modifiers"), N_("Shift, Ctrl, Alt, Super"), None),
            ("switch", "typing-echo", "function-keys", N_("Function keys"), N_("F1 to F12"), None),
            ("switch", "typing-echo", "action-keys", N_("Action keys"), N_("Enter, Tab, Backspace, Delete, Escape"), None),
            ("switch", "typing-echo", "navigation-keys", N_("Movement keys"), N_("Arrows, Home, End, Page Up, Page Down"), None),
            ("switch", "typing-echo", "diacritical-keys", N_("Accent keys"), None, None),
        ]),
    ]),
    ("documents", N_("Documents and web"), "text-html-symbolic", N_("Web pages, documents and e-mail"), [
        (N_("Opening a page"), [
            ("switch", "document", "say-all-on-load", N_("Read the page when it opens"), None, None),
            ("switch", "document", "page-summary-on-load", N_("Summary of the page"),
             N_("How many headings, links and forms, when it opens"), None),
        ]),
        (N_("Browse and focus mode"), [
            ("switch", "document", "native-nav-triggers-focus-mode", N_("Focus mode with Tab"),
             N_("Tab to a form field starts focus mode, to type"), None),
            ("switch", "document", "auto-sticky-focus-mode", N_("Web applications in focus mode"),
             N_("Pages that behave like programs stay in focus mode"), None),
            ("switch", "caret-navigation", "enabled", N_("Browse with the arrows"),
             N_("The arrows move through the text of the page"), None),
            ("switch", "caret-navigation", "layout-mode", N_("Lines as on the screen"),
             N_("A line is what is on one line of the screen"), None),
            ("switch", "structural-navigation", "enabled", N_("Quick keys"),
             N_("H headings, K links, T tables and more, in browse mode"), None),
            ("switch", "structural-navigation", "wraps", N_("Quick keys start again"),
             N_("After the last heading, go back to the first"), None),
            ("switch", "table-navigation", "enabled", N_("Table navigation"), None, None),
            ("switch", "table-navigation", "skip-blank-cells", N_("Skip empty cells"), None, None),
        ]),
        (N_("Read all"), [
            ("choice", "say-all", "style", N_("Read all by"), None,
             [(N_("Sentence"), "sentence"), (N_("Line"), "line")]),
            ("switch", "say-all", "rewind-and-fast-forward", N_("Rewind and fast forward"),
             N_("Left and right arrows while reading all"), None),
            ("switch", "say-all", "structural-navigation", N_("Quick keys while reading all"), None, None),
        ]),
        (N_("Say the structure"), [
            ("switch", SPEAK, "announce-landmark", N_("Landmarks"), N_("Main, navigation, search..."), None),
            ("switch", SPEAK, "announce-list", N_("Lists"), None, None),
            ("switch", SPEAK, "announce-table", N_("Tables"), None, None),
            ("switch", SPEAK, "announce-form", N_("Forms"), None, None),
            ("switch", SPEAK, "announce-blockquote", N_("Quotations"), None, None),
            ("switch", SPEAK, "announce-grouping", N_("Groups"), None, None),
            ("switch", "live-regions", "enabled", N_("Live updates"),
             N_("Messages the page shows by itself, such as chats"), None),
        ]),
    ]),
    ("tables", N_("Tables"), "x-office-spreadsheet-symbolic", N_("Tables and spreadsheets"), [
        (N_("Tables"), [
            ("switch", SPEAK, "speak-row-in-gui-table", N_("Whole row in program lists"), None, None),
            ("switch", SPEAK, "speak-row-in-document-table", N_("Whole row in document tables"), None, None),
            ("switch", SPEAK, "speak-row-in-spreadsheet", N_("Whole row in spreadsheets"), None, None),
            ("switch", SPEAK, "announce-cell-headers", N_("Column and row headers"), None, None),
            ("switch", SPEAK, "announce-cell-coordinates", N_("Cell position in tables"), None, None),
            ("switch", SPEAK, "announce-spreadsheet-cell-coordinates", N_("Cell name in spreadsheets"),
             N_("For example: B4"), None),
            ("switch", SPEAK, "announce-cell-span", N_("Merged cells"), None, None),
            ("switch", SPEAK, "always-announce-selected-range-in-spreadsheet", N_("Selected range"), None, None),
        ]),
    ]),
    ("sounds", N_("Sounds and progress"), "audio-volume-high-symbolic", N_("Sounds and progress bars"), [
        (N_("Sounds"), [
            ("switch", "sound", "enabled", N_("Screen reader sounds"), None, None),
            ("number", "sound", "volume", N_("Sound volume"), N_("From 0 to 1"), (0, 1, 0.1, 1)),
        ]),
        (N_("Progress bars"), [
            ("switch", SPEAK, "speak-progress-bar-updates", N_("Say the progress"), N_("For example: 40 percent"), None),
            ("number", SPEAK, "progress-bar-speech-interval", N_("Every how many seconds"), None, (0, 100, 1, 0)),
            ("switch", "sound", "beep-progress-bar-updates", N_("Beep the progress"),
             N_("A tone that rises with the progress, as in NVDA"), None),
            ("number", "sound", "progress-bar-beep-interval", N_("Beep every how many seconds"), None, (0, 100, 1, 0)),
            ("choice", SPEAK, "progress-bar-speech-verbosity", N_("Progress bars of"), None, PROGRESS_CHOICES),
        ]),
    ]),
    ("braille", N_("Braille"), "input-dialpad-symbolic", N_("Braille displays"), [
        (N_("Braille"), [
            ("switch", "braille", "enabled", N_("Braille"), N_("Show text on a braille display"), None),
            ("choice", "braille", "verbosity-level", N_("Detail"), None,
             [(N_("Brief"), "brief"), (N_("Detailed"), "verbose")]),
            ("choice", "braille", "rolename-style", N_("Kind of control"), None,
             [(N_("Short"), "brief"), (N_("Full"), "verbose")]),
            ("switch", "braille", "contracted-braille", N_("Contracted braille"), None, None),
            ("switch", "braille", "computer-braille-at-cursor", N_("Computer braille at the cursor"), None, None),
            ("switch", "braille", "word-wrap", N_("Word wrap"), N_("Do not cut words at the end of the display"), None),
            ("switch", "braille", "end-of-line-indicator", N_("End of line mark"), None, None),
            ("switch", "braille", "display-ancestors", N_("Where the control is"), N_("The window and group around it"), None),
        ]),
        (N_("Messages"), [
            ("switch", "braille", "flash-messages", N_("Messages on the display"), None, None),
            ("number", "braille", "flash-message-duration", N_("How long, in milliseconds"), None, (1000, 30000, 500, 0)),
            ("switch", "braille", "flash-messages-persistent", N_("Messages stay until a key is pressed"), None, None),
        ]),
    ]),
    ("mouse", N_("Mouse"), "input-mouse-symbolic", N_("What is under the mouse pointer"), [
        (N_("Mouse"), [
            ("switch", "mouse-review", "enabled", N_("Read under the pointer"), None, None),
            ("switch", "mouse-review", "present-tooltips", N_("Tooltips"), None, None),
        ]),
    ]),
    ("time", N_("Time and date"), "preferences-system-time-symbolic", N_("How time and date are said"), [
        (N_("Time and date"), [
            ("choice", "system-information", "time-format", N_("Time"), None,
             [(N_("As the language of the computer"), "%X"), (N_("Hours and minutes"), "%H:%M"),
              (N_("12 hours, with AM or PM"), "%I:%M %p")]),
            ("choice", "system-information", "date-format", N_("Date"), None,
             [(N_("As the language of the computer"), "%x"), (N_("Day, month and year in words"), "%A %d %B %Y"),
              (N_("Day and month in words"), "%A %d %B")]),
        ]),
    ]),
    ("keyboard", N_("Keyboard"), "input-keyboard-symbolic", N_("The screen reader key"), [
        (N_("Screen reader key"), [
            ("choice", "keybindings", "keyboard-layout", N_("Keyboard"),
             N_("Laptop uses Caps Lock as the screen reader key and the letters for reviewing; for now each press of Caps Lock also switches capital letters"),
             [(N_("Desktop, with number pad"), "desktop"), (N_("Laptop"), "laptop")]),
            ("choice", "keybindings", "desktop-modifier-keys", N_("Screen reader key"),
             N_("The key held with the screen reader commands. With Caps Lock, for now each press also switches capital letters on or off"),
             [(N_("Insert"), ["Insert", "KP_Insert"]), (N_("Insert or Caps Lock, as in NVDA"),
                                                      ["Insert", "KP_Insert", "Caps_Lock"]),
              (N_("Caps Lock"), ["Caps_Lock"])]),
        ]),
    ]),
]

# Ready-made profiles: {(group, sub): {key: value}} over a copy of the current one.
PRESETS = [
    ("beginner", N_("Beginner"), N_("Slower, with hints and every detail"), {
        ("voice", "voices/default"): {"rate": 40},
        ("speech", None): {"verbosity-level": "verbose", "speak-tutorial-messages": True,
                           "messages-are-detailed": True, "speak-position-in-set": True},
        ("typing-echo", None): {"key-echo": True, "character-echo": True, "word-echo": True},
    }),
    ("fast", N_("Fast"), N_("Quick and brief, for expert users"), {
        ("voice", "voices/default"): {"rate": 80},
        ("speech", None): {"verbosity-level": "brief", "speak-tutorial-messages": False,
                           "messages-are-detailed": False, "punctuation-level": "some"},
        ("typing-echo", None): {"key-echo": False, "character-echo": True, "word-echo": False},
    }),
    ("study", N_("Study"), N_("For long texts: every punctuation mark, reading by sentence"), {
        ("voice", "voices/default"): {"rate": 55},
        ("speech", None): {"punctuation-level": "all", "speak-misspelled-indicator": True},
        ("say-all", None): {"style": "sentence"},
        ("document", None): {"say-all-on-load": False, "page-summary-on-load": True},
    }),
]

# Programs with their own settings: (Orca's name for the program, label).
PROGRAMS = [
    ("ptyxis", N_("Terminal")),
    ("soffice", N_("LibreOffice")),
    ("firefox-esr", N_("Firefox")),
    ("thunderbird", N_("Thunderbird")),
    ("nautilus", N_("Files")),
    ("gnome-text-editor", N_("Text Editor")),
    ("vabaxos-reader", N_("VabaxOS document reader")),
]
