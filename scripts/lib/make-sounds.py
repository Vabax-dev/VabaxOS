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


# The VabaxOS Campane theme (the first VabaxOS theme, 2026-09-25): the
# timbre of Ubuntu's sounds with VabaxOS melodies. Every note is one strike
# of Yaru's bell.oga (a single D5, Mads Rosendahl, CC-BY-SA-4.0),
# transposed, in D major like Yaru, on the motif of the boot beeps (root,
# fifth, octave: rising when something starts or arrives, falling when it
# ends or leaves). Both VabaxOS themes take the screen capture from
# freedesktop (freesound user horsthorstensen, CC-BY-SA) and emptying the
# trash from Yaru (Vabax's choice: those two are better).
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SAMPLE = os.path.join(REPO, "artwork", "sounds", "yaru-bell.oga")
SAMPLE_NOTE = 587.3  # D5
CAPTURE = os.path.join(REPO, "artwork", "sounds", "freedesktop-screen-capture.oga")
TRASH = os.path.join(REPO, "artwork", "sounds", "yaru-trash-empty.oga")

VABAXOS = {
    "desktop-login": [("D5", 0.0), ("A5", 0.14), ("D6", 0.28), ("F#6", 0.48)],
    "desktop-logout": [("F#6", 0.0), ("D6", 0.14), ("A5", 0.28), ("D5", 0.48)],
    "system-shutdown": [("F#6", 0.0), ("D6", 0.20), ("A5", 0.40), ("F#5", 0.62), ("D5", 0.95)],
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
    "network-connectivity-established": [("D5", 0.0), ("F#5", 0.10), ("A5", 0.20)],
    "network-connectivity-lost": [("A5", 0.0), ("F#5", 0.10), ("D5", 0.20)],
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
    out = np.zeros(int(RATE * total) + 1)
    for tone, start in tones:
        i = int(RATE * start)
        out[i:i + len(tone)] += tone
    peak = np.max(np.abs(out)) or 1.0
    return out / peak * 10 ** (-6 / 20)


# The VabaxOS theme is a piano (Vabax's choice, 2026-09-25: the piano
# among six versions of the start-up sound, then every system sound on the
# same piano, an octave lower than the first proposal). D major, rising
# figures when something starts or arrives, falling when it ends or leaves.
# GNOME plays desktop-login when the desktop starts: that is the start-up
# phrase, like the log-on sound of Windows (an arpeggio up the chord, then
# the chord); system-ready, at the login screen of an installed system, is
# a short motif. Nothing in GNOME plays system-shutdown: the start-up
# phrase going down, played by vabaxos-shutdown-sound.service from its WAV
# copy. Emptying the trash is Yaru's, the screen capture freedesktop's.
PIANO_OCTAVE = -1  # every note an octave lower than written

# name: ([(note, start, velocity)], [chord notes], chord start, chord
# velocity, seconds); short sounds have no chord and a released key.
PIANO = {
    "desktop-login": ([("D4", 0.0, .7), ("A4", 0.16, .72), ("F#5", 0.32, .75), ("E5", 0.48, .7),
                       ("A5", 0.64, .8)], ["D3", "A3", "D5", "F#5", "A5", "D6"], 0.95, .75, 4.2),
    "system-shutdown": ([("A5", 0.0, .72), ("F#5", 0.18, .7), ("E5", 0.36, .66), ("D5", 0.54, .64),
                         ("A4", 0.72, .6)], ["D3", "A3", "D4", "F#4", "A4"], 1.05, .6, 4.6),
    "system-ready": ([("D5", 0.0, .7), ("A5", 0.14, .72), ("D6", 0.30, .75)], [], 0, 0, 1.9),
    "desktop-logout": ([("D6", 0.0, .7), ("A5", 0.11, .68), ("F#5", 0.22, .66), ("D5", 0.36, .64)], [], 0, 0, 1.9),
    "message-new-instant": ([("A5", 0.0, .8), ("D6", 0.09, .85)], [], 0, 0, 1.6),
    "message": ([("F#5", 0.0, .6), ("A5", 0.12, .62)], [], 0, 0, 1.7),
    "dialog-information": ([("A5", 0.0, .6), ("E6", 0.14, .6)], [], 0, 0, 1.7),
    "dialog-warning": ([("F5", 0.0, .8), ("C5", 0.16, .8)], [], 0, 0, 1.7),
    "dialog-error": ([("D4", 0.0, .85), ("C#5", 0.0, .8), ("G#4", 0.0, .75), ("A3", 0.22, .85)], [], 0, 0, 1.8),
    "complete": ([("D5", 0.0, .7), ("F#5", 0.07, .72), ("A5", 0.14, .74), ("D6", 0.21, .8)], [], 0, 0, 1.8),
    "device-added": ([("D5", 0.0, .7), ("A5", 0.1, .72), ("D6", 0.2, .75)], [], 0, 0, 1.8),
    "device-removed": ([("D6", 0.0, .7), ("A5", 0.1, .68), ("D5", 0.2, .66)], [], 0, 0, 1.8),
    "power-plug": ([("D4", 0.0, .75), ("D5", 0.12, .75)], [], 0, 0, 1.7),
    "power-unplug": ([("D5", 0.0, .7), ("D4", 0.12, .7)], [], 0, 0, 1.7),
    "battery-low": ([("D6", 0.0, .75), ("A5", 0.15, .7), ("D6", 0.45, .75), ("A5", 0.6, .7)], [], 0, 0, 2.2),
    "audio-volume-change": ([("D6", 0.0, .6)], [], 0, 0, 1.5),
    "bell-window-system": ([("A5", 0.0, .7)], [], 0, 0, 1.5),
    "network-connectivity-established": ([("D5", 0.0, .65), ("F#5", 0.1, .68), ("A5", 0.2, .7)], [], 0, 0, 1.8),
    "network-connectivity-lost": ([("A5", 0.0, .65), ("F#5", 0.1, .62), ("D5", 0.2, .6)], [], 0, 0, 1.8),
}


def piano(freq, held, velocity, length):
    """A piano note: partials a little sharp as on real strings, three
    strings slightly detuned, a fast then a slow decay (shorter for higher
    notes and partials), the damper when the key is released."""
    t = np.arange(int(RATE * length)) / RATE
    out = np.zeros_like(t)
    scale = (440 / freq) ** 0.5
    for k in range(1, 18):
        fk = k * freq * np.sqrt(1 + 0.00025 * k * k)
        if fk > 12000:
            break
        amp = abs(np.sin(np.pi * k / 7.3)) / k ** 1.05 * velocity ** (0.6 + 0.1 * k)
        env = (0.55 * np.exp(-t / (0.35 * scale / (1 + 0.2 * k)))
               + 0.45 * np.exp(-t / (3.2 * scale / (1 + 0.3 * k))))
        for cents in (-1.2, 0.0, 0.9):
            out += amp / 3 * env * np.sin(2 * np.pi * fk * 2 ** (cents / 1200) * t + k)
    out *= np.minimum(1, t / 0.003)
    released = t > held
    out[released] *= np.exp(-(t[released] - held) / 0.25)
    return out


def room(x, seed, size, decay, mix):
    """A room: the sound convolved with a decaying noise burst."""
    rng = np.random.default_rng(seed)
    t = np.arange(int(RATE * size)) / RATE
    ir = np.convolve(rng.standard_normal(len(t)) * np.exp(-t / decay), np.ones(6) / 6, "same")
    ir[:int(RATE * 0.012)] = 0
    ir /= np.sqrt(np.sum(ir ** 2))
    n = len(x) + len(ir)
    wet = np.fft.irfft(np.fft.rfft(x, n) * np.fft.rfft(ir, n), n)
    return np.concatenate([x, np.zeros(len(ir))]) * (1 - mix) + wet * mix * 3


def render_piano(name):
    notes, chord, chord_start, chord_velocity, length = PIANO[name]
    shift = 2 ** PIANO_OCTAVE
    long_phrase = bool(chord)
    held = 1.0 if long_phrase else 0.35
    out = np.zeros(int(RATE * length))
    for note, start, velocity in notes:
        tone = piano(note_freq(note) * shift, held, velocity, 3.0 if long_phrase else 1.5)
        i = int(RATE * start)
        out[i:i + len(tone)] += tone[:len(out) - i]
    for note in chord:
        tone = piano(note_freq(note) * shift, 3.0, chord_velocity, 3.3) * 0.8
        i = int(RATE * chord_start)
        out[i:i + len(tone)] += tone[:len(out) - i]
    if long_phrase:
        out, floor, level = room(out, 7, 1.6, 0.45, 0.28), -50, -6
    else:  # short sounds: a smaller room, a shorter tail, below the voice
        out, floor, level = room(out, 7, 0.9, 0.3, 0.18), -36, -8
    peak = np.max(np.abs(out))
    out = out[:np.max(np.nonzero(np.abs(out) > peak * 10 ** (floor / 20))) + 1]
    fade = int(RATE * (0.05 if long_phrase else 0.12))
    out[-fade:] *= np.linspace(1, 0, fade)
    return out / peak * 10 ** (level / 20)


def write_wav(path, samples):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes((samples * 32767).astype(np.int16).tobytes())


def vabaxos_theme(out):
    """The default theme, vabaxos (piano), and vabaxos-campane (the first
    VabaxOS theme: Yaru's bell with VabaxOS melodies)."""
    theme = os.path.join(out, "vabaxos")
    os.makedirs(os.path.join(theme, "stereo"), exist_ok=True)
    with open(os.path.join(theme, "index.theme"), "w", encoding="utf-8") as f:
        f.write("[Sound Theme]\nName=VabaxOS\n"
                "Comment=VabaxOS system sounds, on the piano\n"
                "Inherits=freedesktop\nDirectories=stereo\n\n[stereo]\nOutputProfile=stereo\n")
    for name in PIANO:
        samples = render_piano(name)
        write_oga(os.path.join(theme, "stereo", name + ".oga"), samples)
        if name == "system-shutdown":
            write_wav(os.path.join(theme, "system-shutdown.wav"), samples)
    shutil.copyfile(CAPTURE, os.path.join(theme, "stereo", "screen-capture.oga"))
    shutil.copyfile(TRASH, os.path.join(theme, "stereo", "trash-empty.oga"))

    bells = os.path.join(out, "vabaxos-campane")
    os.makedirs(os.path.join(bells, "stereo"), exist_ok=True)
    with open(os.path.join(bells, "index.theme"), "w", encoding="utf-8") as f:
        f.write("[Sound Theme]\nName=VabaxOS Campane\n"
                "Comment=VabaxOS system sounds, with the timbre of Ubuntu's Yaru theme\n"
                "Inherits=freedesktop\nDirectories=stereo\n\n[stereo]\nOutputProfile=stereo\n")
    sample = load(SAMPLE)
    for name in VABAXOS:
        write_oga(os.path.join(bells, "stereo", name + ".oga"), render_vabaxos(sample, name))
    shutil.copyfile(CAPTURE, os.path.join(bells, "stereo", "screen-capture.oga"))
    shutil.copyfile(TRASH, os.path.join(bells, "stereo", "trash-empty.oga"))


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
