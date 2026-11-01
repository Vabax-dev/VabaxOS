#!/usr/bin/env python3
"""Compiles a gettext .po file into a .mo file.

Used by scripts/build-packages.sh when msgfmt (package gettext) is not
installed. It handles what VabaxOS translations use: msgid and msgstr,
contexts (msgctxt), plural forms (msgid_plural, msgstr[N]), multi-line
strings and the usual escapes; fuzzy entries are left out, as msgfmt does.

    po2mo.py INPUT.po OUTPUT.mo
"""

import ast
import re
import struct
import sys


class Entry:
    def __init__(self):
        self.context = None
        self.msgid = None
        self.plural = None
        self.msgstr = {}    # index -> text; index 0 for a plain msgstr
        self.fuzzy = False

    def key(self):
        key = self.msgid if self.plural is None else self.msgid + "\0" + self.plural
        return key if self.context is None else self.context + "\x04" + key

    def value(self):
        return "\0".join(self.msgstr[i] for i in sorted(self.msgstr))

    def translated(self):
        if self.msgid is None or self.fuzzy:
            return False
        if self.msgid == "" and self.context is None:
            return True     # the header
        return bool(self.msgstr) and all(self.msgstr.values())


def parse(path):
    entries = {}
    entry = Entry()
    current = None      # ("msgid",), ("msgstr", N), ...
    fuzzy_next = False

    def flush():
        nonlocal entry
        if entry.translated():
            entries[entry.key()] = entry.value()
        entry = Entry()

    with open(path, encoding="utf-8") as f:
        for number, line in enumerate(f, 1):
            line = line.strip()
            if line.startswith("#,") and "fuzzy" in line:
                if entry.msgid is not None and entry.msgstr:
                    flush()
                fuzzy_next = True
                continue
            if not line or line.startswith("#"):
                continue
            starts_entry = line.startswith(("msgctxt ", "msgid "))
            if starts_entry and (entry.msgstr or (line.startswith("msgctxt ") and entry.msgid is not None)):
                flush()
            if starts_entry and fuzzy_next:
                entry.fuzzy, fuzzy_next = True, False
            match = re.match(r"msgstr\[(\d+)\]\s+(.*)$", line)
            if line.startswith("msgctxt "):
                entry.context = ast.literal_eval(line[8:])
                current = ("msgctxt",)
            elif line.startswith("msgid_plural "):
                entry.plural = ast.literal_eval(line[13:])
                current = ("msgid_plural",)
            elif line.startswith("msgid "):
                entry.msgid = ast.literal_eval(line[6:])
                current = ("msgid",)
            elif match:
                index = int(match.group(1))
                entry.msgstr[index] = ast.literal_eval(match.group(2))
                current = ("msgstr", index)
            elif line.startswith("msgstr "):
                entry.msgstr[0] = ast.literal_eval(line[7:])
                current = ("msgstr", 0)
            elif line.startswith('"') and current:
                text = ast.literal_eval(line)
                if current[0] == "msgctxt":
                    entry.context += text
                elif current[0] == "msgid":
                    entry.msgid += text
                elif current[0] == "msgid_plural":
                    entry.plural += text
                else:
                    entry.msgstr[current[1]] += text
            else:
                sys.exit(f"{path}:{number}: unsupported line: {line}")
    flush()
    return entries


def write_mo(entries, path):
    """The .mo format: the keys sorted by their bytes (the runtime searches
    them by bisection)."""
    pairs = sorted((k.encode("utf-8"), v.encode("utf-8")) for k, v in entries.items())
    count = len(pairs)
    ids_table = 7 * 4
    strs_table = ids_table + 8 * count
    data_start = strs_table + 8 * count
    offsets = []
    data = b""
    for item in [k for k, _v in pairs] + [v for _k, v in pairs]:
        offsets.append((len(item), data_start + len(data)))
        data += item + b"\0"
    header = struct.pack("<7I", 0x950412DE, 0, count, ids_table, strs_table, 0, data_start)
    table = b"".join(struct.pack("<2I", length, offset) for length, offset in offsets)
    with open(path, "wb") as f:
        f.write(header + table + data)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    write_mo(parse(sys.argv[1]), sys.argv[2])
