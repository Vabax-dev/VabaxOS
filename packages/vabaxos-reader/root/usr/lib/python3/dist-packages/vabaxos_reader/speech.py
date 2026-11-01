"""Voices of the VabaxOS reader (ADR-0026).

eSpeak NG is always there: it is the voice of the whole system. Kokoro, the
natural voice (ADR-0019), is used only when the vabaxos-voice package is
installed; for now it is not in the ISO (ADR-0026, Vabax's choice).

Each engine turns a sentence into 16-bit mono PCM bytes at its own rate.
A synthesis in progress can be stopped at once (stop()).
"""

import ctypes
import io
import os
import shutil
import subprocess
import threading
import wave

# eSpeak NG speaks 175 words a minute at speed 1.0; it goes up to 450.
ESPEAK_WPM = 175
ESPEAK_MAX_WPM = 450
ESPEAK_MIN_WPM = 80


class Voice:
    """One voice in the reader's list."""

    def __init__(self, engine, ident, language, name):
        self.engine = engine
        self.ident = ident
        self.language = language
        self.name = name

    def __repr__(self):
        return f"Voice({self.engine.kind}, {self.ident})"


class Espeak:
    """eSpeak NG through its command, which writes a WAV file on stdout."""

    kind = "espeak"
    rate = 22050

    def __init__(self, program=None):
        self.program = program or shutil.which("espeak-ng")
        if not self.program:
            raise RuntimeError("espeak-ng is not installed")
        self.process = None
        self.lock = threading.Lock()

    def voices(self):
        return [Voice(self, "it", "it", "Italiano, eSpeak NG"),
                Voice(self, "en-us", "en", "English, eSpeak NG")]

    def wpm(self, speed):
        return int(max(ESPEAK_MIN_WPM, min(ESPEAK_MAX_WPM, round(ESPEAK_WPM * speed))))

    def synthesize(self, text, voice, speed=1.0):
        command = [self.program, "--stdout", "-v", voice.ident, "-s", str(self.wpm(speed)), "--", text]
        with self.lock:
            self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        process = self.process
        data, _err = process.communicate()
        with self.lock:
            self.process = None
        if process.returncode != 0:
            raise RuntimeError("espeak-ng stopped")
        return wav_pcm(data, self.rate)

    def stop(self):
        with self.lock:
            if self.process is not None and self.process.poll() is None:
                self.process.terminate()

    def clone(self):
        """Another engine for work in parallel (saving the audio)."""
        return Espeak(self.program)


class Kokoro:
    """The natural voice, when vabaxos-voice is installed (ADR-0019)."""

    kind = "kokoro"

    def __init__(self, shared=None):
        from vabaxos_voice import engine
        # The model takes about 570 MB: clones share it.
        self.engine = shared or engine.Kokoro()
        self.rate = engine.SAMPLE_RATE
        self.running = None

    @staticmethod
    def available():
        try:
            from vabaxos_voice import engine
        except ImportError:
            return False
        return os.path.exists(os.path.join(engine.DATA_DIR, "kokoro-v1.0.onnx"))

    def voices(self):
        names = {"im_nicola": "Nicola", "if_sara": "Sara", "af_heart": "Heart", "am_michael": "Michael"}
        return [Voice(self, v, lang, f"{names[v]}, Kokoro")
                for v, lang in (("im_nicola", "it"), ("if_sara", "it"), ("af_heart", "en"), ("am_michael", "en"))]

    def synthesize(self, text, voice, speed=1.0):
        self.running = self.engine.run_options()
        try:
            pcm = self.engine.synthesize(text, voice.ident, voice.language, self.running)
        finally:
            self.running = None
        return self.engine.sonic(pcm, speed).tobytes()

    def stop(self):
        running = self.running
        if running is not None:
            running.terminate = True

    def clone(self):
        return Kokoro(self.engine)


def wav_pcm(data, rate):
    """The samples of a WAV file in memory, checked to be 16-bit mono."""
    if not data:
        return b""
    with wave.open(io.BytesIO(data)) as f:
        if f.getsampwidth() != 2 or f.getnchannels() != 1 or f.getframerate() != rate:
            raise RuntimeError("unexpected audio format from espeak-ng")
        # espeak-ng writes 0x7fffffff as the length when it writes to a pipe.
        return f.readframes(f.getnframes() if f.getnframes() < 0x7FFFFFF else 1 << 30)


def engines():
    """eSpeak NG first (the voice of the system), then Kokoro if installed."""
    found = []
    try:
        found.append(Espeak())
    except RuntimeError:
        pass
    if Kokoro.available():
        try:
            found.append(Kokoro())
        except Exception:  # noqa: BLE001 - the reader still works with eSpeak NG
            pass
    return found


def default_index(voices, language):
    """The first voice of the user's language, else the first voice."""
    for i, voice in enumerate(voices):
        if voice.language == language:
            return i
    return 0


def user_language():
    for name in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(name, "")
        if value and value not in ("C", "POSIX") and not value.startswith("C."):
            return value.split(":")[0][:2]
    return "en"


# -- playback ----------------------------------------------------------------

PA_STREAM_PLAYBACK = 1
PA_SAMPLE_S16LE = 3


class _SampleSpec(ctypes.Structure):
    _fields_ = [("format", ctypes.c_int), ("rate", ctypes.c_uint32), ("channels", ctypes.c_uint8)]


class _BufferAttr(ctypes.Structure):
    _fields_ = [("maxlength", ctypes.c_uint32), ("tlength", ctypes.c_uint32), ("prebuf", ctypes.c_uint32),
                ("minreq", ctypes.c_uint32), ("fragsize", ctypes.c_uint32)]


class Player:
    """Plays PCM bytes through PipeWire (its PulseAudio interface), in short
    pieces, so a pause stops the voice within a few tens of milliseconds."""

    def __init__(self, rate, latency=0.03, chunk=0.02):
        self.lib = ctypes.CDLL("libpulse-simple.so.0")
        self.lib.pa_simple_new.restype = ctypes.c_void_p
        self.lib.pa_simple_new.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p,
                                           ctypes.c_char_p, ctypes.POINTER(_SampleSpec), ctypes.c_void_p,
                                           ctypes.POINTER(_BufferAttr), ctypes.POINTER(ctypes.c_int)]
        self.lib.pa_simple_write.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t,
                                             ctypes.POINTER(ctypes.c_int)]
        self.lib.pa_simple_drain.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]
        self.lib.pa_simple_flush.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]
        self.lib.pa_simple_free.argtypes = [ctypes.c_void_p]
        self.rate = rate
        self.latency = latency
        self.chunk = int(rate * chunk) * 2
        self.stream = None

    def _open(self):
        if self.stream:
            return
        spec = _SampleSpec(PA_SAMPLE_S16LE, self.rate, 1)
        attr = _BufferAttr(0xFFFFFFFF, int(self.rate * self.latency) * 2, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF)
        error = ctypes.c_int(0)
        stream = self.lib.pa_simple_new(None, b"VabaxOS reader", PA_STREAM_PLAYBACK, None, b"reading",
                                        ctypes.byref(spec), None, ctypes.byref(attr), ctypes.byref(error))
        if not stream:
            raise OSError(f"cannot open the sound server (error {error.value})")
        self.stream = stream

    def play(self, pcm, cancelled):
        error = ctypes.c_int(0)
        self._open()
        for start in range(0, len(pcm), self.chunk):
            if cancelled():
                self.lib.pa_simple_flush(self.stream, ctypes.byref(error))
                return False
            piece = pcm[start:start + self.chunk]
            if self.lib.pa_simple_write(self.stream, piece, len(piece), ctypes.byref(error)) < 0:
                self.close()
                raise OSError(f"sound server write failed (error {error.value})")
        return True

    def drain(self, cancelled):
        error = ctypes.c_int(0)
        if not self.stream:
            return True
        if cancelled():
            self.lib.pa_simple_flush(self.stream, ctypes.byref(error))
            return False
        self.lib.pa_simple_drain(self.stream, ctypes.byref(error))
        return True

    def close(self):
        if self.stream:
            self.lib.pa_simple_free(self.stream)
            self.stream = None


class Recorder:
    """For tests (VABAXOS_VOICE_RECORD=file): the audio goes to a file,
    raw 16-bit mono, in real time, instead of the speakers."""

    def __init__(self, rate, path):
        self.rate = rate
        self.path = path

    def play(self, pcm, cancelled):
        import time
        step = int(self.rate * 0.02) * 2
        with open(self.path, "ab") as f:
            for start in range(0, len(pcm), step):
                if cancelled():
                    return False
                f.write(pcm[start:start + step])
                time.sleep(step / 2 / self.rate)
        return True

    def drain(self, cancelled):
        return not cancelled()

    def close(self):
        pass


def make_player(rate):
    path = os.environ.get("VABAXOS_VOICE_RECORD")
    return Recorder(rate, path) if path else Player(rate)
