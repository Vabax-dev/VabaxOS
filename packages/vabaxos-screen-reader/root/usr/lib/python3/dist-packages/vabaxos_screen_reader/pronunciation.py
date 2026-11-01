"""The pronunciation dictionary of the screen reader (Orca 50:
org.gnome.Orca.Pronunciations "entries", a{ss}, word -> how to say it).

VabaxOS starts it with the words eSpeak NG reads badly: file types and
other abbreviations, written as separate capital letters so every language
spells them ("txt" -> "T X T"), and a few names. The user changes it in
the window vabaxos-pronunciation. Words are kept in lower case: Orca
matches them in any case.
"""

import re

GROUP = "pronunciations"
KEY = "entries"

# Abbreviations read letter by letter; not those said as a word in Italian
# or English (IVA, SPID, ISO, ZIP, LAN, PIN, GIF, JSON, FAQ...).
_LETTERS = ["txt", "pdf", "docx", "odt", "ods", "odp", "xls", "xlsx", "ppt", "pptx", "rtf", "csv",
            "html", "htm", "css", "xml", "jpg", "png", "svg", "mp3", "mp4", "mkv", "wav", "usb", "url",
            "http", "https", "www", "pc", "cpu", "gpu", "ssd", "hdd", "dvd", "cd", "tv", "gtk", "ssh",
            "vpn", "dns", "ip", "otp", "cie", "sms", "gps", "nvda", "kde", "id"]
# Names: only those that sound right in every language of VabaxOS.
NAMES = {
    "vabaxos": "Vabax O S",
}


def spelled(word):
    return " ".join(word.upper())


def defaults():
    entries = {word: spelled(word) for word in _LETTERS}
    entries.update(NAMES)
    return dict(sorted(entries.items()))


def clean_word(word):
    """The word as a key: trimmed, lower case; None if it cannot be one."""
    word = (word or "").strip().lower()
    if not word or len(word) > 60 or re.search(r"\s", word):
        return None
    return word


def add(entries, word, saying):
    key = clean_word(word)
    saying = (saying or "").strip()
    if key is None:
        raise ValueError("one word, without spaces")
    if not saying:
        raise ValueError("how to say it is empty")
    result = dict(entries)
    result[key] = saying
    return result


def remove(entries, word):
    result = dict(entries)
    result.pop((word or "").strip().lower(), None)
    return result


def variant_text(entries):
    """entries as GVariant text, for a dconf keyfile."""
    def quote(text):
        return "'" + text.replace("\\", "\\\\").replace("'", "\\'") + "'"
    return "{" + ", ".join(f"{quote(k)}: {quote(v)}" for k, v in sorted(entries.items())) + "}"


def dconf_defaults():
    return ("# Written by vabaxos_screen_reader.pronunciation --dconf when the package is built:\n"
            "# the pronunciation dictionary VabaxOS starts with (block of 2026-11-01).\n"
            "[org/gnome/orca/default/pronunciations]\n"
            f"entries={variant_text(defaults())}\n")


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["--dconf"]:
        sys.stdout.write(dconf_defaults())
    else:
        sys.exit("usage: python3 -m vabaxos_screen_reader.pronunciation --dconf")
