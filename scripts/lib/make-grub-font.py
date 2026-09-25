#!/usr/bin/env python3
"""Makes a GRUB font (PF2) from a TrueType font, without grub-mkfont.

    make-grub-font.py FONT.ttf SIZE NAME OUTPUT.pf2

The boot menu uses Atkinson Hyperlegible Next, the font of the desktop, at
a larger size for readers with low vision (block 5):

    make-grub-font.py AtkinsonHyperlegibleNext-Bold.ttf 26 \
        "Atkinson Hyperlegible Next Bold 26" \
        image/config/bootloaders/grub-pc/live-theme/atkinson-26.pf2

Covers printable ASCII, Latin-1 and the other letters of Latin Extended-A,
enough for the menu in English and Italian and the language names. Needs
python3-pil. The PF2 format: sections of a 4-byte name and a big-endian
length; glyphs as 1-bit bitmaps, rows packed without padding (GRUB's
font.c).
"""

import struct
import sys

from PIL import Image, ImageDraw, ImageFont

CHARS = list(range(0x20, 0x7F)) + list(range(0xA0, 0x180)) + [0x2026, 0x2013, 0x2014, 0x2018, 0x2019,
                                                              0x201C, 0x201D, 0x20AC, 0x2190, 0x2191,
                                                              0x2192, 0x2193]


def section(name, data):
    return name.encode("ascii") + struct.pack(">I", len(data)) + data


def glyph(font, code, ascent):
    char = chr(code)
    advance = round(font.getlength(char))
    left, top, right, bottom = font.getbbox(char)
    width, height = max(0, right - left), max(0, bottom - top)
    if width == 0 or height == 0:
        return struct.pack(">HHhhh", 0, 0, 0, 0, advance)
    image = Image.new("L", (width, height), 0)
    ImageDraw.Draw(image).text((-left, -top), char, font=font, fill=255)
    bits = []
    pixels = image.load()
    for y in range(height):
        for x in range(width):
            bits.append(1 if pixels[x, y] >= 110 else 0)
    data = bytearray((len(bits) + 7) // 8)
    for i, bit in enumerate(bits):
        if bit:
            data[i // 8] |= 0x80 >> (i % 8)
    # x offset from the pen; y offset of the bottom edge from the baseline.
    return struct.pack(">HHhhh", width, height, left, ascent - bottom, advance) + bytes(data)


def main(ttf, size, name, output):
    font = ImageFont.truetype(ttf, int(size))
    ascent, descent = font.getmetrics()
    family = name.rpartition(" ")[0]  # without the size
    weight = "bold" if family.endswith(" Bold") else "normal"
    for word in (" Bold", " Regular"):
        if family.endswith(word):
            family = family[:-len(word)]
    glyphs = [(code, glyph(font, code, ascent)) for code in CHARS if font.getmask(chr(code)).getbbox() or code == 0x20]
    max_width = max(struct.unpack(">H", g[:2])[0] for _, g in glyphs)
    max_height = max(struct.unpack(">H", g[2:4])[0] for _, g in glyphs)
    header = b"".join([
        section("FILE", b"PFF2"),
        section("NAME", name.encode() + b"\0"),
        section("FAMI", family.encode() + b"\0"),
        section("WEIG", weight.encode() + b"\0"),
        section("SLAN", b"normal\0"),
        section("PTSZ", struct.pack(">H", int(size))),
        section("MAXW", struct.pack(">H", max_width)),
        section("MAXH", struct.pack(">H", max_height)),
        section("ASCE", struct.pack(">H", ascent)),
        section("DESC", struct.pack(">H", descent)),
    ])
    index_size = 9 * len(glyphs)
    # CHIX, then the DATA section header (length 0xFFFFFFFF: up to the end).
    data_start = len(header) + 8 + index_size + 8
    index = bytearray()
    offset = data_start
    for code, data in glyphs:
        index += struct.pack(">IBI", code, 0, offset)
        offset += len(data)
    blob = header + section("CHIX", bytes(index)) + b"DATA" + struct.pack(">I", 0xFFFFFFFF)
    blob += b"".join(data for _, data in glyphs)
    with open(output, "wb") as f:
        f.write(blob)
    print(f"{output}: {len(glyphs)} glyphs, {len(blob)} bytes, ascent {ascent}, descent {descent}")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    main(*sys.argv[1:])
