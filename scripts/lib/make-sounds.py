#!/usr/bin/env python3
"""Generates the VabaxOS system sounds (DOC-01 §33, block 5).

    make-sounds.py OUTPUT_DIR

The default theme, VabaxOS, has the timbre of Ubuntu's Yaru sounds with
melodies of our own (see VABAXOS below; Vabax's choice, 2026-09-25).
Three more styles of the same family stay available: cristallo (bells),
morbido (soft mallets), aria (gentle pads). Every sound
is built on the VabaxOS motif, the interval of the two boot menu beeps: a
rising figure means "something starts or arrives", a falling one "something
ends or leaves". Sounds are short, have no hard clicks, and differ in pitch
contour, so they can be told apart without seeing anything.

Writes OUTPUT_DIR/vabaxos-STYLE/stereo/NAME.oga (Ogg Vorbis, the format
of GNOME sound themes) with the names of the freedesktop Sound Naming
Specification, and an index.theme for each style. The package
vabaxos-sounds holds the result:

    python3 scripts/lib/make-sounds.py packages/vabaxos-sounds/root/usr/share/sounds

Needs python3-numpy, oggenc (vorbis-tools) and ffmpeg. The output is the same at
every run (no random numbers), but oggenc output may change with its
version: the generated files are kept in Git.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import wave

import numpy as np

RATE = 48000


def note_freq(name):
    names = {"C": -9, "D": -7, "E": -5, "F": -4, "G": -2, "A": 0, "B": 2}
    semis = names[name[0]]
    rest = name[1:]
    if rest.startswith("#"):
        semis += 1
        rest = rest[1:]
    elif rest.startswith("b"):
        semis -= 1
        rest = rest[1:]
    octave = int(rest)
    return 440.0 * 2 ** ((semis + 12 * (octave - 4)) / 12)


def envelope(n, attack, decay):
    t = np.arange(n) / RATE
    env = np.minimum(1.0, t / max(attack, 1e-4)) * np.exp(-t / decay)
    fade = min(n, int(RATE * 0.02))
    env[-fade:] *= np.linspace(1, 0, fade)  # no click at the end
    return env


def crystal(freq, length, level=1.0):
    n = int(RATE * length)
    t = np.arange(n) / RATE
    index = 2.2 * np.exp(-t / 0.25)
    mod = np.sin(2 * np.pi * freq * 3.5 * t) * index
    tone = np.sin(2 * np.pi * freq * t + mod) + 0.25 * np.sin(2 * np.pi * freq * 2.01 * t)
    return level * tone * envelope(n, 0.003, length / 3.2)


def soft(freq, length, level=1.0):
    n = int(RATE * length)
    t = np.arange(n) / RATE
    tone = (np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * freq * 2 * t) * np.exp(-t / 0.08)
            + 0.12 * np.sin(2 * np.pi * freq * 4 * t) * np.exp(-t / 0.03))
    return level * tone * envelope(n, 0.006, length / 3.0)


def air(freq, length, level=1.0):
    n = int(RATE * length)
    t = np.arange(n) / RATE
    tone = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(2 * np.pi * freq * 2 * t) + 0.1 * np.sin(2 * np.pi * freq * 3 * t)
    attack = min(0.06, length / 4)
    env = np.minimum(1.0, t / attack) * np.exp(-np.maximum(0, t - attack) / (length / 2.2))
    fade = min(n, int(RATE * 0.05))
    env[-fade:] *= np.linspace(1, 0, fade)
    return level * tone * env


STYLES = {"cristallo": crystal, "morbido": soft, "aria": air}

# (note, start in seconds, length in seconds, level)
SOUNDS = {
    "system-ready": [("A4", 0.0, 0.9, 0.8), ("E5", 0.18, 0.9, 0.8), ("A5", 0.36, 1.3, 0.9)],
    "desktop-login": [("E5", 0.0, 0.6, 0.8), ("A5", 0.14, 0.9, 0.9)],
    "desktop-logout": [("A5", 0.0, 0.6, 0.8), ("E5", 0.14, 0.9, 0.8)],
    "system-shutdown": [("A5", 0.0, 0.7, 0.8), ("E5", 0.18, 0.7, 0.8), ("A4", 0.36, 1.2, 0.8)],
    "message-new-instant": [("C#6", 0.0, 0.35, 0.7), ("E6", 0.09, 0.5, 0.7)],
    "message": [("A5", 0.0, 0.5, 0.7)],
    "dialog-information": [("E5", 0.0, 0.4, 0.7), ("E5", 0.16, 0.5, 0.6)],
    "dialog-warning": [("F5", 0.0, 0.35, 0.8), ("C5", 0.14, 0.6, 0.8)],
    "dialog-error": [("C5", 0.0, 0.45, 0.9), ("C#5", 0.0, 0.45, 0.6), ("G4", 0.2, 0.7, 0.9)],
    "complete": [("A5", 0.0, 0.3, 0.7), ("C#6", 0.08, 0.3, 0.7), ("E6", 0.16, 0.7, 0.8)],
    "device-added": [("E5", 0.0, 0.3, 0.7), ("B5", 0.1, 0.5, 0.7)],
    "device-removed": [("B5", 0.0, 0.3, 0.7), ("E5", 0.1, 0.5, 0.7)],
    "power-plug": [("A4", 0.0, 0.3, 0.7), ("A5", 0.1, 0.6, 0.7)],
    "power-unplug": [("A5", 0.0, 0.3, 0.7), ("A4", 0.1, 0.6, 0.7)],
    "battery-low": [("E5", 0.0, 0.3, 0.8), ("C5", 0.15, 0.3, 0.8), ("E5", 0.45, 0.3, 0.8), ("C5", 0.6, 0.5, 0.8)],
    "audio-volume-change": [("A5", 0.0, 0.15, 0.6)],
    "bell-window-system": [("E6", 0.0, 0.25, 0.6)],
    "trash-empty": [("E5", 0.0, 0.2, 0.6), ("C5", 0.06, 0.2, 0.6), ("A4", 0.12, 0.4, 0.6)],
    "screen-capture": [("A6", 0.0, 0.12, 0.5), ("E6", 0.05, 0.2, 0.5)],
    "network-connectivity-established": [("A4", 0.0, 0.3, 0.7), ("E5", 0.1, 0.3, 0.7), ("B5", 0.2, 0.5, 0.7)],
    "network-connectivity-lost": [("B5", 0.0, 0.3, 0.7), ("E5", 0.1, 0.3, 0.7), ("A4", 0.2, 0.5, 0.7)],
}

# Italian names, for the listening demo and the documentation.
NAMES_IT = {
    "system-ready": "Sistema pronto", "desktop-login": "Accesso", "desktop-logout": "Uscita",
    "system-shutdown": "Spegnimento", "message-new-instant": "Nuovo messaggio",
    "message": "Notifica", "dialog-information": "Informazione", "dialog-warning": "Avviso",
    "dialog-error": "Errore", "complete": "Operazione completata", "device-added": "Dispositivo collegato",
    "device-removed": "Dispositivo scollegato", "power-plug": "Alimentatore collegato",
    "power-unplug": "Alimentatore scollegato", "battery-low": "Batteria scarica",
    "audio-volume-change": "Cambio del volume", "bell-window-system": "Campanello",
    "trash-empty": "Cestino svuotato", "screen-capture": "Schermata catturata",
    "network-connectivity-established": "Rete collegata", "network-connectivity-lost": "Rete persa",
}


def render(style, notes):
    total = max(start + length for _, start, length, _ in notes) + 0.05
    out = np.zeros(int(RATE * total))
    for name, start, length, level in notes:
        tone = STYLES[style](note_freq(name), length, level)
        i = int(RATE * start)
        out[i:i + len(tone)] += tone
    peak = np.max(np.abs(out)) or 1.0
    return out / peak * 10 ** (-6 / 20)  # peak at -6 dBFS: never louder than speech


def write_oga(path, samples):
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        with wave.open(tmp.name, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(RATE)
            w.writeframes((samples * 32767).astype(np.int16).tobytes())
        subprocess.run(["oggenc", "-Q", "-q", "5", "-o", path, tmp.name], check=True)


TITLES = {"cristallo": ("Cristallo", "bells"), "morbido": ("Morbido", "soft mallets"),
          "aria": ("Aria", "gentle pads")}


# The VabaxOS theme (Vabax's choice, 2026-09-25): the timbre of Ubuntu's
# sounds with VabaxOS melodies. Every note is one strike of Yaru's
# bell.oga (a single D5, Mads Rosendahl, CC-BY-SA-4.0), transposed: the
# sound of a real system, and melodies of our own, in D major like Yaru,
# on the motif of the boot beeps (root, fifth, octave: rising when
# something starts or arrives, falling when it ends or leaves). Start-up
# and shut-down are longer phrases over a soft chord. The screen capture
# is freedesktop's (freesound user horsthorstensen, CC-BY-SA).
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SAMPLE = os.path.join(REPO, "artwork", "sounds", "yaru-bell.oga")
SAMPLE_NOTE = 587.3  # D5
CAPTURE = os.path.join(REPO, "artwork", "sounds", "freedesktop-screen-capture.oga")

VABAXOS = {
    "system-ready": [("D5", 0.0), ("A5", 0.16), ("F#5", 0.32), ("A5", 0.48), ("D6", 0.70),
                     ("E6", 1.00), ("F#6", 1.22), ("A6", 1.50), ("F#6", 1.95), ("D6", 2.25)],
    "desktop-login": [("D5", 0.0), ("A5", 0.14), ("D6", 0.28), ("F#6", 0.48)],
    "desktop-logout": [("F#6", 0.0), ("D6", 0.14), ("A5", 0.28), ("D5", 0.48)],
    "system-shutdown": [("A6", 0.0), ("F#6", 0.20), ("E6", 0.40), ("D6", 0.62), ("A5", 0.95),
                        ("F#5", 1.20), ("E5", 1.45), ("D5", 1.80)],
    "message-new-instant": [("A5", 0.0), ("D6", 0.10)],
    "message": [("F#5", 0.0), ("A5", 0.12)],
    "dialog-information": [("A5", 0.0), ("A5", 0.16)],
    "dialog-warning": [("F5", 0.0), ("C5", 0.14)],
    "dialog-error": [("D5", 0.0), ("C#5", 0.0), ("A4", 0.18)],
    "complete": [("D5", 0.0), ("F#5", 0.08), ("A5", 0.16), ("D6", 0.24)],
    "device-added": [("D5", 0.0), ("A5", 0.10), ("D6", 0.20)],
    "device-removed": [("D6", 0.0), ("A5", 0.10), ("D5", 0.20)],
    "power-plug": [("D4", 0.0), ("D5", 0.12)],
    "power-unplug": [("D5", 0.0), ("D4", 0.12)],
    "battery-low": [("D6", 0.0), ("A5", 0.15), ("D6", 0.45), ("A5", 0.60)],
    "audio-volume-change": [("D6", 0.0)],
    "bell-window-system": [("A5", 0.0)],
    "trash-empty": [("F#5", 0.0), ("D5", 0.07), ("A4", 0.14)],
    "network-connectivity-established": [("D5", 0.0), ("F#5", 0.10), ("A5", 0.20)],
    "network-connectivity-lost": [("A5", 0.0), ("F#5", 0.10), ("D5", 0.20)],
}
# A soft chord under the long phrases: (notes, start, length).
VABAXOS_PADS = {
    "system-ready": (["D4", "A4", "F#5"], 0.6, 3.0),
    "system-shutdown": (["D4", "A4", "D5"], 0.3, 2.8),
}


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(RATE),
                          "-f", "s16le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768


def strike(sample, freq):
    """The sample transposed to freq by resampling (a higher note is also
    shorter, as on a real mallet instrument)."""
    ratio = freq / SAMPLE_NOTE
    positions = np.arange(0, len(sample) - 1, ratio)
    tone = np.interp(positions, np.arange(len(sample)), sample)
    fade = min(len(tone), int(RATE * 0.01))
    tone[-fade:] *= np.linspace(1, 0, fade)
    return tone


def render_vabaxos(sample, name):
    notes = VABAXOS[name]
    tones = [(strike(sample, note_freq(n)), start) for n, start in notes]
    total = max(start + len(t) / RATE for t, start in tones)
    pad = VABAXOS_PADS.get(name)
    if pad:
        total = max(total, pad[1] + pad[2])
    out = np.zeros(int(RATE * total) + 1)
    for tone, start in tones:
        i = int(RATE * start)
        out[i:i + len(tone)] += tone
    if pad:
        chord, start, length = pad
        i = int(RATE * start)
        for n in chord:
            tone = air(note_freq(n), length, 0.18)
            out[i:i + len(tone)] += tone[:len(out) - i]
    peak = np.max(np.abs(out)) or 1.0
    return out / peak * 10 ** (-6 / 20)


def vabaxos_theme(out):
    theme = os.path.join(out, "vabaxos")
    os.makedirs(os.path.join(theme, "stereo"), exist_ok=True)
    with open(os.path.join(theme, "index.theme"), "w", encoding="utf-8") as f:
        f.write("[Sound Theme]\nName=VabaxOS\n"
                "Comment=VabaxOS system sounds, with the timbre of Ubuntu's Yaru theme\n"
                "Inherits=freedesktop\nDirectories=stereo\n\n[stereo]\nOutputProfile=stereo\n")
    sample = load(SAMPLE)
    for name in VABAXOS:
        write_oga(os.path.join(theme, "stereo", name + ".oga"), render_vabaxos(sample, name))
    shutil.copyfile(CAPTURE, os.path.join(theme, "stereo", "screen-capture.oga"))


def main(out):
    vabaxos_theme(out)
    for style in STYLES:
        theme = os.path.join(out, "vabaxos-" + style)
        os.makedirs(os.path.join(theme, "stereo"), exist_ok=True)
        title, kind = TITLES[style]
        with open(os.path.join(theme, "index.theme"), "w", encoding="utf-8") as f:
            f.write(f"[Sound Theme]\nName=VabaxOS {title}\n"
                    f"Comment=VabaxOS system sounds, {kind}\n"
                    "Inherits=freedesktop\nDirectories=stereo\n\n[stereo]\nOutputProfile=stereo\n")
        for name, notes in SOUNDS.items():
            write_oga(os.path.join(theme, "stereo", name + ".oga"), render(style, notes))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
