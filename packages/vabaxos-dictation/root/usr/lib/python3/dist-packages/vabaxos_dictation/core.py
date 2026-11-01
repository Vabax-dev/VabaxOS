"""Speech to text with whisper.cpp (Debian's package), on the computer.

Known problems of Whisper, handled here (checked online, 2026-11-01):

- on silence or noise it writes sentences nobody said, the same in every
  language, such as "Sottotitoli creati dalla comunità Amara.org": the
  audio is checked first, and silence is never sent to it (the advice of
  its users: no silence to the model), then the known sentences are
  removed;
- it writes [Music] or (applausi) for sounds: removed.

Spoken commands, in Italian and English, become characters: "a capo"
(new line), "nuovo paragrafo" (new paragraph).
"""

import array
import os
import re
import shutil
import subprocess
import tempfile
import wave

MODEL_DIR = os.environ.get("VABAXOS_WHISPER_DIR", "/usr/share/vabaxos/whisper")
MODEL = "ggml-small.bin"
PROGRAMS = ("whisper-cli", "whisper-cpp", "whisper.cpp", "whisper")
RATE = 16000

# Mean loudness (RMS of 16-bit samples) below which a piece of audio is
# silence or room noise; speech near a laptop microphone is far above.
SILENCE_RMS = 300
# At least this much audio above the threshold, in seconds, to be speech.
MIN_SPEECH = 0.3

# Sentences Whisper writes on silence and noise (lower case, without the
# final punctuation). From its users' reports; added to when found.
HALLUCINATIONS = (
    "sottotitoli creati dalla comunità amara.org",
    "sottotitoli e revisione a cura di qtss",
    "sottotitoli a cura di qtss",
    "grazie per la visione",
    "grazie a tutti per la visione",
    "subtitles by the amara.org community",
    "thanks for watching",
    "thank you for watching",
)

_SOUNDS = re.compile(r"\s*[\[(][^\])]{1,40}[\])]\s*")
_COMMANDS = [
    (re.compile(r",?\s*\bnuovo paragrafo\b[,.]?\s*", re.I), "\n\n"),
    (re.compile(r",?\s*\bnew paragraph\b[,.]?\s*", re.I), "\n\n"),
    (re.compile(r",?\s*\ba capo\b[,.]?\s*", re.I), "\n"),
    (re.compile(r",?\s*\bnew line\b[,.]?\s*", re.I), "\n"),
]


def find_program():
    for name in PROGRAMS:
        path = shutil.which(name)
        if path:
            return path
    return None


def model_path():
    return os.path.join(MODEL_DIR, MODEL)


def available():
    return find_program() is not None and os.path.exists(model_path())


def speech_seconds(path, threshold=SILENCE_RMS):
    """Seconds of a 16-bit WAV file louder than threshold (in 20 ms pieces)."""
    with wave.open(path) as f:
        if f.getsampwidth() != 2:
            raise ValueError("16-bit audio expected")
        channels, rate = f.getnchannels(), f.getframerate()
        data = f.readframes(f.getnframes())
    samples = array.array("h")
    samples.frombytes(data[:len(data) - len(data) % 2])
    step = max(1, int(rate * 0.02)) * channels
    loud = 0
    for start in range(0, len(samples), step):
        piece = samples[start:start + step]
        if piece and (sum(s * s for s in piece) / len(piece)) ** 0.5 >= threshold:
            loud += 1
    return loud * 0.02


def has_speech(path):
    try:
        return speech_seconds(path) >= MIN_SPEECH
    except (OSError, ValueError, EOFError, wave.Error):
        return False


def clean(text):
    """The text as it should be typed: no sounds in brackets, no invented
    sentences, spoken commands turned into characters, tidy spaces."""
    text = _SOUNDS.sub(" ", text)
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if line.lower().rstrip(".!?… ") in HALLUCINATIONS:
            continue
        lines.append(line)
    text = " ".join(lines)
    for sentence in HALLUCINATIONS:
        text = re.sub(re.escape(sentence) + r"[.!?…]*", "", text, flags=re.I)
    for pattern, replacement in _COMMANDS:
        text = pattern.sub(replacement, text)
    text = re.sub(r"[ \t]+", " ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    # A new line written as a command starts with a capital letter.
    text = re.sub(r"\n([a-zàèéìòù])", lambda m: "\n" + m.group(1).upper(), text)
    return text.strip(" ")


def as_16k_mono(path, out_path):
    """A copy of a 16-bit WAV file at 16 kHz mono (Whisper's format), by
    linear interpolation; False if it already is in that format."""
    with wave.open(path) as f:
        channels, rate, width = f.getnchannels(), f.getframerate(), f.getsampwidth()
        data = f.readframes(f.getnframes())
    if width != 2:
        raise ValueError("16-bit audio expected")
    if channels == 1 and rate == RATE:
        return False
    samples = array.array("h")
    samples.frombytes(data[:len(data) - len(data) % (2 * channels)])
    mono = [sum(samples[i:i + channels]) // channels for i in range(0, len(samples), channels)]
    count = int(len(mono) * RATE / rate)
    out = array.array("h")
    for i in range(count):
        position = i * rate / RATE
        left = int(position)
        right = min(left + 1, len(mono) - 1)
        fraction = position - left
        out.append(int(mono[left] * (1 - fraction) + mono[right] * fraction))
    with wave.open(out_path, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(RATE)
        f.writeframes(out.tobytes())
    return True


def threads():
    return max(1, min(8, (os.cpu_count() or 2) - 1))


def transcribe(path, language="it", program=None, model=None):
    """The text of a WAV file (16 kHz mono), or "" if nothing was said."""
    if not has_speech(path):
        return ""
    program = program or find_program()
    if not program:
        raise RuntimeError("whisper.cpp is not installed")
    with tempfile.TemporaryDirectory(prefix="vabaxos-dictation-") as tmp:
        ready = os.path.join(tmp, "16k.wav")
        if not as_16k_mono(path, ready):
            ready = path
        command = [program, "-m", model or model_path(), "-f", ready, "-l", language,
                   "-t", str(threads()), "-nt", "-np"]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        lines = result.stderr.strip().splitlines()
        raise RuntimeError(lines[-1] if lines else "whisper.cpp failed")
    return clean(result.stdout)


def record_command(path):
    """Recording from the default microphone, 16 kHz mono, as Whisper wants."""
    if shutil.which("pw-record"):
        return ["pw-record", "--rate", str(RATE), "--channels", "1", "--format", "s16", path]
    return ["parecord", f"--rate={RATE}", "--channels=1", "--format=s16le", "--file-format=wav", path]


def user_language():
    for name in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(name, "")
        if value and value not in ("C", "POSIX") and not value.startswith("C."):
            return value.split(":")[0][:2]
    return "en"
