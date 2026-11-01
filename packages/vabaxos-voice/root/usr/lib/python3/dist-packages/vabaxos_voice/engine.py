"""Kokoro speech synthesis for VabaxOS (ADR-0019).

Only Debian packages are used: onnxruntime runs the model, espeak-ng turns
text into IPA phonemes (the same phonemes Kokoro was trained with, as in
kokoro-onnx), and libsonic changes the speed. The model always speaks at its
natural speed; faster or slower speech comes from Sonic, which keeps every
word clear even at high speed (listening test with Vabax, 2026-09-24).
"""

import ctypes
import json
import os
import re
import threading

import numpy as np

SAMPLE_RATE = 24000
SYSTEM_DIR = "/usr/share/vabaxos/kokoro"
# The text files (vocab.json, phrases-*.txt) are in the package; the model
# can be in the package or downloaded by the user (model.py).
DATA_DIR = os.environ.get("VABAXOS_KOKORO_DIR", SYSTEM_DIR)
MODEL = "kokoro-v1.0.onnx"
VOICES_FILE = "voices-v1.0.bin"


def user_dir():
    base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return os.path.join(base, "vabaxos", "kokoro")


def has_model(folder):
    return all(os.path.exists(os.path.join(folder, name)) for name in (MODEL, VOICES_FILE))


def model_dir():
    """Where the model is: VABAXOS_KOKORO_DIR, the user's download, or the
    package; None when there is none."""
    for folder in (os.environ.get("VABAXOS_KOKORO_DIR"), user_dir(), SYSTEM_DIR):
        if folder and has_model(folder):
            return folder
    return None
MAX_PHONEMES = 510

# The voices for each language; the first one is the default until the
# speed test (vabaxos-voice-select) picks the faster one.
VOICES = {
    # The first voice is the default one (ADR-0024: no measurement at boot);
    # Nicola is the one Vabax liked most.
    "it": ["im_nicola", "if_sara"],
    "en": ["af_heart", "am_michael", "bf_emma", "bm_george"],
}
ESPEAK_LANGUAGE = {"it": "it", "en": "en-us"}

# Punctuation Kokoro knows, kept between the phonemes of the words.
_PUNCT = re.compile(r'([;:,.!?—…"“”()]+)')
_LANG_FLAG = re.compile(r"\([a-z-]+\)")


class Phonemizer:
    """Text to IPA with espeak-ng, keeping punctuation, like phonemizer."""

    _lock = threading.Lock()

    def __init__(self):
        self.lib = ctypes.CDLL("libespeak-ng.so.1")
        self.lib.espeak_Initialize.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
        self.lib.espeak_SetVoiceByName.argtypes = [ctypes.c_char_p]
        self.lib.espeak_TextToPhonemes.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_int, ctypes.c_int]
        self.lib.espeak_TextToPhonemes.restype = ctypes.c_char_p
        # AUDIO_OUTPUT_SYNCHRONOUS: no audio device is opened.
        if self.lib.espeak_Initialize(2, 0, None, 0) < 0:
            raise RuntimeError("espeak-ng cannot start")
        self.language = None

    def _words(self, text):
        buf = ctypes.create_string_buffer(text.encode("utf-8"))
        ptr = ctypes.c_void_p(ctypes.addressof(buf))
        parts = []
        while ptr.value:
            # espeakCHARS_UTF8 = 1; phoneme mode 0x02 = IPA, with stress marks.
            out = self.lib.espeak_TextToPhonemes(ctypes.byref(ptr), 1, 0x02)
            if out:
                parts.append(out.decode("utf-8"))
        return _LANG_FLAG.sub("", " ".join(parts)).strip()

    def __call__(self, text, language):
        with self._lock:
            if language != self.language:
                self.lib.espeak_SetVoiceByName(ESPEAK_LANGUAGE.get(language, language).encode())
                self.language = language
            out = []
            for piece in _PUNCT.split(text):
                if not piece.strip():
                    continue
                if _PUNCT.fullmatch(piece):
                    out.append(piece.strip())
                else:
                    if out:
                        out.append(" ")
                    out.append(self._words(piece))
            return "".join(out).strip()


class Sonic:
    """libsonic: speeds speech up or down without losing words."""

    def __init__(self):
        lib = ctypes.CDLL("libsonic.so.0")
        lib.sonicCreateStream.restype = ctypes.c_void_p
        lib.sonicCreateStream.argtypes = [ctypes.c_int, ctypes.c_int]
        lib.sonicSetSpeed.argtypes = [ctypes.c_void_p, ctypes.c_float]
        lib.sonicSetPitch.argtypes = [ctypes.c_void_p, ctypes.c_float]
        lib.sonicWriteShortToStream.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_short), ctypes.c_int]
        lib.sonicFlushStream.argtypes = [ctypes.c_void_p]
        lib.sonicSamplesAvailable.argtypes = [ctypes.c_void_p]
        lib.sonicReadShortFromStream.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_short), ctypes.c_int]
        lib.sonicDestroyStream.argtypes = [ctypes.c_void_p]
        self.lib = lib

    def __call__(self, pcm, speed=1.0, pitch=1.0):
        if abs(speed - 1.0) < 0.01 and abs(pitch - 1.0) < 0.01:
            return pcm
        lib = self.lib
        stream = lib.sonicCreateStream(SAMPLE_RATE, 1)
        try:
            lib.sonicSetSpeed(stream, speed)
            lib.sonicSetPitch(stream, pitch)
            data = np.ascontiguousarray(pcm, dtype=np.int16)
            lib.sonicWriteShortToStream(stream, data.ctypes.data_as(ctypes.POINTER(ctypes.c_short)), len(data))
            lib.sonicFlushStream(stream)
            count = lib.sonicSamplesAvailable(stream)
            out = np.zeros(count, dtype=np.int16)
            lib.sonicReadShortFromStream(stream, out.ctypes.data_as(ctypes.POINTER(ctypes.c_short)), count)
            return out
        finally:
            lib.sonicDestroyStream(stream)


def trim(pcm, threshold=330, keep=0.03):
    """Removes the silence Kokoro puts before and after speech (0.2-0.4 s),
    as NVDA does for its voices: the words start sooner."""
    loud = np.nonzero(np.abs(pcm) > threshold)[0]
    if not len(loud):
        return pcm[:0]
    pad = int(SAMPLE_RATE * keep)
    return pcm[max(0, loud[0] - pad):loud[-1] + pad]


class Kokoro:
    """The model, loaded once and kept in memory."""

    def __init__(self, data_dir=None, threads=None):
        import onnxruntime as ort
        data_dir = data_dir or model_dir() or DATA_DIR
        options = ort.SessionOptions()
        options.intra_op_num_threads = threads or default_threads()
        options.inter_op_num_threads = 1
        options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self.session = ort.InferenceSession(os.path.join(data_dir, MODEL), options,
                                            providers=["CPUExecutionProvider"])
        inputs = {i.name: i for i in self.session.get_inputs()}
        self.tokens_input = "tokens" if "tokens" in inputs else "input_ids"
        self.speed_int = "int" in inputs["speed"].type
        self.voices = dict(np.load(os.path.join(data_dir, VOICES_FILE)))
        vocab = os.path.join(data_dir, "vocab.json")
        if not os.path.exists(vocab):
            vocab = os.path.join(DATA_DIR, "vocab.json")
        with open(vocab, encoding="utf-8") as f:
            self.vocab = json.load(f)
        self.phonemize = Phonemizer()
        self.sonic = Sonic()
        self._run_lock = threading.Lock()

    def tokens(self, text, language):
        phonemes = self.phonemize(text, language)
        ids = [self.vocab[p] for p in phonemes if p in self.vocab]
        return ids[:MAX_PHONEMES]

    def run_options(self):
        """Options for one synthesis; setting .terminate = True from another
        thread stops it (used on STOP)."""
        import onnxruntime as ort
        return ort.RunOptions()

    def synthesize(self, text, voice, language, run_options=None):
        """PCM 16-bit at 24 kHz, natural speed, silence trimmed."""
        ids = self.tokens(text, language)
        if not ids:
            return np.zeros(0, dtype=np.int16)
        style = self.voices[voice][min(len(ids), len(self.voices[voice])) - 1]
        speed = np.array([1], dtype=np.int32) if self.speed_int else np.array([1.0], dtype=np.float32)
        feed = {self.tokens_input: np.array([[0, *ids, 0]], dtype=np.int64),
                "style": np.asarray(style, dtype=np.float32).reshape(1, -1), "speed": speed}
        with self._run_lock:
            audio = self.session.run(None, feed, run_options)[0].ravel()
        pcm = (np.clip(audio, -1, 1) * 32767).astype(np.int16)
        return trim(pcm)


def default_threads():
    """Up to 8 threads: more gave no gain in the measurements (2026-09-24)."""
    return max(1, min(8, len(os.sched_getaffinity(0))))


# Kokoro needs about a third of the length of the audio it makes (measured
# 2026-11-02: 1.4 s before a 4.8 s sentence starts on a 4-core 2.1 GHz CPU),
# so the first words go alone: they play while the rest is made.
FIRST_WORDS = 3
MAX_WORDS = 12
# A part never ends on these words: the voice would stop on "the" or "di".
FUNCTION_WORDS = {
    "il", "lo", "la", "i", "gli", "le", "l", "un", "uno", "una", "di", "a", "da", "in", "con", "su", "per",
    "tra", "fra", "del", "della", "dei", "degli", "delle", "al", "alla", "ai", "agli", "alle", "dal", "dalla",
    "nel", "nella", "nei", "sul", "sulla", "e", "o", "ma", "che", "non", "se", "come", "è",
    "the", "a", "an", "of", "to", "in", "on", "at", "for", "with", "from", "by", "and", "or", "but", "that",
    "is", "are", "not", "if", "as", "my", "your", "this",
}


def first_words_setting(path="/etc/vabaxos/voice.conf"):
    """first_words= in voice.conf (0: the first part is a whole clause)."""
    value = os.environ.get("VABAXOS_KOKORO_FIRST_WORDS")
    if value is None:
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.split("#", 1)[0].strip()
                    if line.startswith("first_words="):
                        value = line.split("=", 1)[1].strip()
        except OSError:
            pass
    try:
        return max(0, int(value)) if value is not None else FIRST_WORDS
    except ValueError:
        return FIRST_WORDS


def _cut(words, size):
    """Where to cut a list of words near size, never after a function word."""
    cut = min(size, len(words))
    while cut < len(words) - 1 and words[cut - 1].lower().strip("'’") in FUNCTION_WORDS:
        cut += 1
    return cut


def split(text, first_words=None, max_words=MAX_WORDS):
    """Splits text at sentence and clause ends, long clauses every
    max_words words, and the first few words alone, so the first part
    starts playing at once while the rest is synthesized. A short text
    (up to first_words + 2 words) stays whole."""
    first_words = first_words_setting() if first_words is None else first_words
    clauses = [p.strip() for p in re.split(r"(?<=[.!?;:])\s+|(?<=,)\s+", text) if p.strip()]
    parts = []
    for clause in clauses:
        words = clause.split()
        while len(words) > max_words + 3:
            cut = _cut(words, max_words)
            parts.append(" ".join(words[:cut]))
            words = words[cut:]
        parts.append(" ".join(words))
    if first_words and parts:
        words = parts[0].split()
        if len(words) > first_words + 2:
            cut = _cut(words, first_words)
            if cut < len(words) - 1:
                parts[0:1] = [" ".join(words[:cut]), " ".join(words[cut:])]
    return parts or [text]
