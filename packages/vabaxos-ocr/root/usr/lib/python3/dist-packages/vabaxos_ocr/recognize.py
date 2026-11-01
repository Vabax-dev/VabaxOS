"""Text out of a picture of the screen, for the screen reader.

Screens are not scanned pages: the letters are small, often light on a dark
background, with icons and lines between them. Before tesseract the picture
is made grey, enlarged three times (tesseract wants letters about 30 pixels
high, as on a page at 300 dpi) and, if the background is dark, inverted, so
the letters are dark on light; known advice of the tesseract users, checked
on our own test pictures (tests/ocr).

The result keeps the order of the screen, top to bottom, left to right, one
line of text for each line on the screen, with an empty line between
blocks: Orca reads it line by line with the arrows.
"""

import os
import shutil
import subprocess
import tempfile

SCALE = 3
# Below this median brightness (0 black, 255 white) the background is dark.
DARK = 110
# Words recognized with less confidence than this (0-100) are left out:
# on a screen they are mostly icons read as letters.
MIN_CONFIDENCE = 40
LANGUAGES = {"it": "ita+eng", "en": "eng+ita"}


def languages(lang=None):
    """Tesseract languages, the user's first, among those installed."""
    lang = (lang or user_language())[:2]
    wanted = LANGUAGES.get(lang, "eng+ita").split("+")
    have = installed_languages()
    chosen = [w for w in wanted if w in have] if have else wanted
    return "+".join(chosen or ["eng"])


def installed_languages():
    if not shutil.which("tesseract"):
        return set()
    out = subprocess.run(["tesseract", "--list-langs"], capture_output=True, text=True, check=False).stdout
    return {line.strip() for line in out.splitlines()[1:] if line.strip()}


def user_language():
    for name in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(name, "")
        if value and value not in ("C", "POSIX") and not value.startswith("C."):
            return value.split(":")[0][:2]
    return "en"


def prepare(path, out_path):
    """Grey, three times larger, dark letters on light. Returns True if
    the picture was inverted."""
    from PIL import Image, ImageOps
    with Image.open(path) as image:
        grey = ImageOps.grayscale(image.convert("RGB"))
    values = sorted(grey.getdata()) if grey.width * grey.height <= 4_000_000 else \
        sorted(grey.resize((grey.width // 4 or 1, grey.height // 4 or 1)).getdata())
    median = values[len(values) // 2]
    inverted = median < DARK
    if inverted:
        grey = ImageOps.invert(grey)
    grey = grey.resize((grey.width * SCALE, grey.height * SCALE), Image.Resampling.LANCZOS)
    grey = ImageOps.autocontrast(grey)
    grey.save(out_path)
    return inverted


def lines_from_tsv(tsv, min_confidence=MIN_CONFIDENCE):
    """Tesseract's TSV output as lines of text, in reading order, with an
    empty line between blocks."""
    rows = tsv.splitlines()
    if not rows:
        return []
    header = rows[0].split("\t")
    index = {name: i for i, name in enumerate(header)}
    words = {}
    order = []
    for row in rows[1:]:
        cells = row.split("\t")
        if len(cells) < len(header):
            continue
        text = cells[index["text"]].strip()
        try:
            confidence = float(cells[index["conf"]])
        except ValueError:
            continue
        if not text or confidence < min_confidence:
            continue
        key = (int(cells[index["block_num"]]), int(cells[index["par_num"]]), int(cells[index["line_num"]]))
        if key not in words:
            words[key] = []
            order.append(key)
        words[key].append(text)
    lines = []
    previous_block = None
    for key in order:
        if previous_block is not None and key[0] != previous_block:
            lines.append("")
        lines.append(" ".join(words[key]))
        previous_block = key[0]
    return lines


def recognize(path, lang=None):
    """The text of the picture at path, as a list of lines."""
    if not shutil.which("tesseract"):
        raise RuntimeError("tesseract is not installed")
    with tempfile.TemporaryDirectory(prefix="vabaxos-ocr-") as tmp:
        ready = os.path.join(tmp, "ready.png")
        prepare(path, ready)
        result = subprocess.run(["tesseract", ready, "-", "-l", languages(lang), "--psm", "3", "tsv"],
                                capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "tesseract failed")
    return lines_from_tsv(result.stdout)
