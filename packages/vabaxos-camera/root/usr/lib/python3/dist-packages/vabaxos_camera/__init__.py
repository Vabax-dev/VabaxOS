"""Reading with the camera: the voice guides the paper into the picture,
then the text is read (Vabax, 2026-11-02: the webcam, with guidance by
voice to frame the text, and a description too).

Known from research on blind users taking pictures for OCR (guidance
makes the right picture much quicker) and from KOZAI (Tesseract, every
hint by sound): each frame of the webcam goes through tesseract, and the
words found tell what to do.

    analyze(words, width, height, brightness, facing_user)  -> Guidance
    words_from_tsv(tsv)                                       -> [Word]
"""

import gettext
import subprocess
from dataclasses import dataclass

_ = gettext.translation("vabaxos-camera", fallback=True).gettext

DARK = 45                 # median brightness (0-255) below which nothing can be read
MIN_CONFIDENCE = 60
MIN_WORDS = 6             # words enough to take the picture
EDGE = 0.02               # a word this close to an edge (share of the side) is cut
SMALL = 0.022             # median word height below this share of the picture: too far
BIG = 0.085             # median word height above this share: too near
LANGUAGES = "ita+eng"


@dataclass
class Word:
    text: str
    left: int
    top: int
    width: int
    height: int
    confidence: float


@dataclass
class Guidance:
    kind: str       # dark, empty, cut, far, near, few, ready
    sentence: str
    sides: tuple = ()

    @property
    def ready(self):
        return self.kind == "ready"


def words_from_tsv(tsv, min_confidence=MIN_CONFIDENCE):
    rows = tsv.splitlines()
    if not rows:
        return []
    header = rows[0].split("\t")
    index = {name: i for i, name in enumerate(header)}
    words = []
    for row in rows[1:]:
        cells = row.split("\t")
        if len(cells) < len(header):
            continue
        text = cells[index["text"]].strip()
        try:
            confidence = float(cells[index["conf"]])
        except ValueError:
            continue
        # One letter alone is mostly noise in a camera picture.
        if len(text) < 2 or confidence < min_confidence or not any(c.isalnum() for c in text):
            continue
        words.append(Word(text, int(cells[index["left"]]), int(cells[index["top"]]), int(cells[index["width"]]),
                          int(cells[index["height"]]), confidence))
    return words


def users_side(side, facing_user):
    """The side of the picture as the user sees it. A webcam that looks at
    the user sees them as a person in front does: the left of the picture
    is the user's right."""
    if facing_user and side in ("left", "right"):
        return "right" if side == "left" else "left"
    return side


def side_name(side, facing_user):
    return {"left": _("on the left"), "right": _("on the right"), "top": _("at the top"),
            "bottom": _("at the bottom")}[users_side(side, facing_user)]


def move_towards(side, facing_user):
    """Where to move the paper so that the part cut comes into the picture:
    the opposite way, in the user's words."""
    opposite = {"left": "right", "right": "left", "top": "bottom", "bottom": "top"}[side]
    return {"left": _("to the left"), "right": _("to the right"), "top": _("up"),
            "bottom": _("down")}[users_side(opposite, facing_user)]


def analyze(words, width, height, brightness=128, facing_user=True):
    if brightness < DARK:
        return Guidance("dark", _("Too dark: turn on a light."))
    if not words:
        return Guidance("empty", _("No text: hold the paper in front of the camera, about 30 centimetres away."))
    heights = sorted(w.height for w in words)
    median = heights[len(heights) // 2] / height
    cut = []
    margin_x, margin_y = width * EDGE, height * EDGE
    for side, touching in (("left", [w for w in words if w.left <= margin_x]),
                           ("right", [w for w in words if w.left + w.width >= width - margin_x]),
                           ("top", [w for w in words if w.top <= margin_y]),
                           ("bottom", [w for w in words if w.top + w.height >= height - margin_y])):
        if len(touching) >= 2 or (touching and len(words) < 4):
            cut.append(side)
    if median > BIG or len(cut) >= 3:
        return Guidance("near", _("Too near: move the paper away a little."), tuple(cut))
    if cut:
        side = cut[0]
        return Guidance("cut", _("The text goes out {side}: move the paper a little {towards}.").format(
            side=side_name(side, facing_user), towards=move_towards(side, facing_user)), tuple(cut))
    if median < SMALL:
        return Guidance("far", _("The text is small: bring the paper nearer."))
    if len(words) < MIN_WORDS:
        return Guidance("few", _("I see only a few words: hold the paper still and straight."))
    return Guidance("ready", _("Still like this."))


def brightness(image):
    """The median brightness of a PIL picture, 0-255."""
    grey = image.convert("L").resize((64, 48))
    values = sorted(grey.getdata())
    return values[len(values) // 2]


def read_frame(image, lang=LANGUAGES, run=subprocess.run):
    """Tesseract on one frame (grey, as it is: quick, about a second)."""
    import io
    buffer = io.BytesIO()
    image.convert("L").save(buffer, format="PNG")
    result = run(["tesseract", "stdin", "-", "-l", lang, "--psm", "11", "tsv"], input=buffer.getvalue(),
                 capture_output=True, check=False)
    return words_from_tsv(result.stdout.decode("utf-8", "replace")) if result.returncode == 0 else []


def guide(image, facing_user=True, lang=LANGUAGES, run=subprocess.run):
    light = brightness(image)
    words = read_frame(image, lang, run) if light >= DARK else []
    return analyze(words, image.width, image.height, light, facing_user)
