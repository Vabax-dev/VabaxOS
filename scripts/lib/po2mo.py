#!/usr/bin/env python3
"""Compiles a gettext .po file into a .mo file.

Used by scripts/build-packages.sh when msgfmt (package gettext) is not
installed. It handles what VabaxOS translations use: msgid and msgstr,
multi-line strings and the usual escapes; no plural forms, no contexts.

    po2mo.py INPUT.po OUTPUT.mo
"""

import ast
import struct
import sys


def parse(path):
    entries = {}
    msgid = msgstr = None
    current = None
    fuzzy = False

    def flush():
        nonlocal msgid, msgstr, fuzzy
        if msgid is not None and msgstr is not None and (msgstr or msgid == "") and not fuzzy:
            entries[msgid] = msgstr
        msgid = msgstr = None
        fuzzy = False

    with open(path, encoding="utf-8") as f:
        for number, line in enumerate(f, 1):
            line = line.strip()
            if line.startswith("#,") and "fuzzy" in line:
                flush()
                fuzzy = True
            elif not line or line.startswith("#"):
                continue
            elif line.startswith("msgid "):
                if msgid is not None and msgstr is not None:
                    keep_fuzzy = fuzzy
                    flush()
                    fuzzy = keep_fuzzy
                msgid = ast.literal_eval(line[6:])
                current = "msgid"
            elif line.startswith("msgstr "):
                msgstr = ast.literal_eval(line[7:])
                current = "msgstr"
            elif line.startswith('"'):
                text = ast.literal_eval(line)
                if current == "msgid":
                    msgid += text
                elif current == "msgstr":
                    msgstr += text
            else:
                sys.exit(f"{path}:{number}: unsupported line: {line}")
    flush()
    return entries


def write_mo(entries, path):
    keys = sorted(entries)
    ids = [k.encode("utf-8") for k in keys]
    strs = [entries[k].encode("utf-8") for k in keys]
    count = len(keys)
    ids_table = 7 * 4
    strs_table = ids_table + 8 * count
    data_start = strs_table + 8 * count
    offsets = []
    data = b""
    for item in ids + strs:
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
