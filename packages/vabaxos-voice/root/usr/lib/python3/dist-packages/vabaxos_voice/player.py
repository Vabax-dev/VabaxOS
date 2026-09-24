"""Low-latency playback for speech, through the PulseAudio interface of
PipeWire (ADR-0019).

A small buffer (about 30 ms) is requested, as NVDA does with WASAPI, so the
first words are heard at once, and audio is written in short pieces, so a
STOP can cut it off within a few tens of milliseconds.
"""

import ctypes
import threading

import numpy as np

PA_STREAM_PLAYBACK = 1
PA_SAMPLE_S16LE = 3


class _SampleSpec(ctypes.Structure):
    _fields_ = [("format", ctypes.c_int), ("rate", ctypes.c_uint32), ("channels", ctypes.c_uint8)]


class _BufferAttr(ctypes.Structure):
    _fields_ = [("maxlength", ctypes.c_uint32), ("tlength", ctypes.c_uint32), ("prebuf", ctypes.c_uint32),
                ("minreq", ctypes.c_uint32), ("fragsize", ctypes.c_uint32)]


class Player:
    def __init__(self, rate=24000, name=b"VabaxOS voice", latency=0.03, chunk=0.02):
        self.lib = ctypes.CDLL("libpulse-simple.so.0")
        self.lib.pa_simple_new.restype = ctypes.c_void_p
        self.lib.pa_simple_new.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p,
                                           ctypes.c_char_p, ctypes.POINTER(_SampleSpec), ctypes.c_void_p,
                                           ctypes.POINTER(_BufferAttr), ctypes.POINTER(ctypes.c_int)]
        self.lib.pa_simple_write.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_int)]
        self.lib.pa_simple_drain.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]
        self.lib.pa_simple_flush.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]
        self.lib.pa_simple_free.argtypes = [ctypes.c_void_p]
        self.rate = rate
        self.name = name
        self.latency = latency
        self.chunk = int(rate * chunk)
        self.stream = None
        self.lock = threading.Lock()

    def _open(self):
        if self.stream:
            return
        spec = _SampleSpec(PA_SAMPLE_S16LE, self.rate, 1)
        tlength = int(self.rate * self.latency) * 2
        attr = _BufferAttr(0xFFFFFFFF, tlength, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF)
        error = ctypes.c_int(0)
        stream = self.lib.pa_simple_new(None, self.name, PA_STREAM_PLAYBACK, None, b"speech",
                                        ctypes.byref(spec), None, ctypes.byref(attr), ctypes.byref(error))
        if not stream:
            raise OSError(f"cannot open the sound server (error {error.value})")
        self.stream = stream

    def play(self, pcm, cancelled):
        """Plays int16 mono audio; returns False if cancelled() became true."""
        data = np.ascontiguousarray(pcm, dtype=np.int16)
        error = ctypes.c_int(0)
        with self.lock:
            self._open()
            for start in range(0, len(data), self.chunk):
                if cancelled():
                    self.lib.pa_simple_flush(self.stream, ctypes.byref(error))
                    return False
                piece = data[start:start + self.chunk]
                if self.lib.pa_simple_write(self.stream, piece.ctypes.data, piece.nbytes, ctypes.byref(error)) < 0:
                    self.close()
                    raise OSError(f"sound server write failed (error {error.value})")
        return True

    def drain(self, cancelled):
        """Waits until the sound is out, unless cancelled."""
        error = ctypes.c_int(0)
        with self.lock:
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
    """Writes the audio to a file instead of the speakers, in real time, for
    tests (VABAXOS_VOICE_RECORD=file): raw 16-bit mono, appended."""

    def __init__(self, rate, path):
        self.rate = rate
        self.path = path

    def play(self, pcm, cancelled):
        import time
        data = np.ascontiguousarray(pcm, dtype=np.int16)
        step = int(self.rate * 0.02)
        with open(self.path, "ab") as f:
            for start in range(0, len(data), step):
                if cancelled():
                    return False
                f.write(data[start:start + step].tobytes())
                time.sleep(step / self.rate)
        return True

    def drain(self, cancelled):
        return not cancelled()

    def close(self):
        pass


def make_player(rate):
    import os
    path = os.environ.get("VABAXOS_VOICE_RECORD")
    return Recorder(rate, path) if path else Player(rate)
