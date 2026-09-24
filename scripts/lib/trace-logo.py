#!/usr/bin/env python3
"""Traces the VabaxOS logo from its PNG into SVG files, colour by colour.

    trace-logo.py artwork/logo-vabaxos-original.png artwork/

The logo has four flat colours: cream background, navy, purple and mint.
Each pixel is assigned to the nearest of them; every colour but the
background becomes a black-and-white bitmap that potrace turns into
vector paths. Writes:

    logo-vabaxos.svg              symbol and name, on a transparent background
    logo-vabaxos-symbol.svg       the symbol only, square
    logo-vabaxos-symbol-light.svg the symbol for dark backgrounds (navy -> white)

Needs potrace. The PNG is read with the standard library only (8-bit RGB or
RGBA, not interlaced).
"""

import os
import re
import struct
import subprocess
import sys
import tempfile
import zlib

PALETTE = {  # measured on the original PNG
    "background": (247, 243, 234),
    "navy": (11, 27, 63),
    "purple": (85, 24, 239),
    "mint": (125, 216, 173),
}
SYMBOL_BOTTOM = 0.72  # the name starts below 72% of the height
LIGHT = {"navy": "#ffffff"}


def read_png(path):
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        sys.exit("not a PNG file")
    pos, idat = 8, b""
    while pos < len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        chunk = data[pos + 8:pos + 8 + length]
        if kind == b"IHDR":
            width, height, depth, colour, _, _, interlace = struct.unpack(">IIBBBBB", chunk)
            if depth != 8 or colour not in (2, 6) or interlace:
                sys.exit("only 8-bit RGB or RGBA, not interlaced")
            channels = 3 if colour == 2 else 4
        elif kind == b"IDAT":
            idat += chunk
        pos += 12 + length
    raw = zlib.decompress(idat)
    stride = width * channels
    rows, previous = [], bytearray(stride)
    for y in range(height):
        start = y * (stride + 1)
        kind, line = raw[start], bytearray(raw[start + 1:start + 1 + stride])
        for i in range(stride):
            left = line[i - channels] if i >= channels else 0
            up = previous[i]
            upleft = previous[i - channels] if i >= channels else 0
            if kind == 1:
                line[i] = (line[i] + left) & 255
            elif kind == 2:
                line[i] = (line[i] + up) & 255
            elif kind == 3:
                line[i] = (line[i] + (left + up) // 2) & 255
            elif kind == 4:
                p = left + up - upleft
                pa, pb, pc = abs(p - left), abs(p - up), abs(p - upleft)
                pred = left if pa <= pb and pa <= pc else (up if pb <= pc else upleft)
                line[i] = (line[i] + pred) & 255
        rows.append(line)
        previous = line
    return width, height, channels, rows


def nearest(pixel):
    return min(PALETTE, key=lambda name: sum((a - b) ** 2 for a, b in zip(PALETTE[name], pixel)))


def trace(width, height, mask, workdir, name):
    pbm = os.path.join(workdir, name + ".pbm")
    with open(pbm, "wb") as f:
        f.write(f"P4\n{width} {height}\n".encode())
        for y in range(height):
            row = bytearray((width + 7) // 8)
            for x in range(width):
                if mask[y][x]:
                    row[x // 8] |= 0x80 >> (x % 8)
            f.write(bytes(row))
    svg = os.path.join(workdir, name + ".svg")
    subprocess.run(["potrace", "--svg", "--flat", "--turdsize", "8", "--alphamax", "1.0",
                    "--opttolerance", "0.2", "--unit", "1", "-o", svg, pbm], check=True)
    text = open(svg, encoding="utf-8").read()
    group = re.search(r"<g transform=\"([^\"]+)\"[^>]*>(.*?)</g>", text, re.S)
    return group.group(1), re.findall(r"<path d=\"([^\"]+)\"", group.group(2))


def svg_file(path, view_box, layers, title):
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view_box}" role="img">',
             f"<title>{title}</title>"]
    for colour, transform, paths in layers:
        parts.append(f'<g transform="{transform}" fill="{colour}" stroke="none">')
        parts += [f'<path d="{d}"/>' for d in paths]
        parts.append("</g>")
    parts.append("</svg>")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts) + "\n")


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    source, outdir = sys.argv[1], sys.argv[2]
    width, height, channels, rows = read_png(source)
    classes = [[nearest(tuple(row[x * channels:x * channels + 3])) for x in range(width)] for row in rows]
    limit = int(height * SYMBOL_BOTTOM)
    colours = {"navy": "#0b1b3f", "purple": "#5518ef", "mint": "#7dd8ad"}
    with tempfile.TemporaryDirectory() as workdir:
        full, symbol = [], []
        for name, colour in colours.items():
            mask = [[c == name for c in line] for line in classes]
            transform, paths = trace(width, height, mask, workdir, name)
            full.append((colour, transform, paths))
            top = [[c == name and y < limit for c in line] for y, line in enumerate(classes)]
            transform, paths = trace(width, height, top, workdir, name + "-symbol")
            symbol.append((name, colour, transform, paths))
    svg_file(os.path.join(outdir, "logo-vabaxos.svg"), f"0 0 {width} {height}", full, "VabaxOS")
    # The symbol sits roughly between 14% and 72% of the height: a square around it.
    side = limit - int(height * 0.12)
    left = (width - side) // 2
    box = f"{left} {int(height * 0.12)} {side} {side}"
    svg_file(os.path.join(outdir, "logo-vabaxos-symbol.svg"), box,
             [(c, t, p) for _, c, t, p in symbol], "VabaxOS")
    svg_file(os.path.join(outdir, "logo-vabaxos-symbol-light.svg"), box,
             [(LIGHT.get(n, c), t, p) for n, c, t, p in symbol], "VabaxOS")


if __name__ == "__main__":
    main()
