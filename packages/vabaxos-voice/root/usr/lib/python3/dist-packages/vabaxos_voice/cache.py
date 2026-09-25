"""Cache of synthesized phrases (ADR-0019).

A screen reader says the same short phrases again and again: "button",
"check box", "not checked", menu names. Kokoro needs 0.2-0.8 s for each new
phrase; from the cache it starts at once. Phrases live in memory; the ones
said at least twice, and the common phrases prepared in advance, are also
kept on disk, so they are ready after a restart.

The audio is kept at natural speed: the rate is applied when playing.
"""

import collections
import hashlib
import os
import threading

import numpy as np


def cache_dir():
    base = os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")
    return os.path.join(base, "vabaxos-voice")


class PhraseCache:
    def __init__(self, directory=None, max_bytes=96 * 1024 * 1024):
        self.directory = directory or cache_dir()
        self.max_bytes = max_bytes
        self.memory = collections.OrderedDict()
        self.size = 0
        self.seen = collections.Counter()
        self.lock = threading.Lock()

    @staticmethod
    def key(voice, language, text):
        return hashlib.sha1(f"{voice}\0{language}\0{text}".encode("utf-8")).hexdigest()

    def _path(self, voice, key):
        return os.path.join(self.directory, voice, key[:2], key + ".pcm")

    def get(self, voice, language, text):
        key = self.key(voice, language, text)
        with self.lock:
            pcm = self.memory.get(key)
            if pcm is not None:
                self.memory.move_to_end(key)
                return pcm
        path = self._path(voice, key)
        try:
            pcm = np.fromfile(path, dtype=np.int16)
        except OSError:
            return None
        self._remember(key, pcm)
        return pcm

    def put(self, voice, language, text, pcm, persist=False):
        key = self.key(voice, language, text)
        self._remember(key, pcm)
        with self.lock:
            self.seen[key] += 1
            persist = persist or self.seen[key] >= 2
        if persist:
            self._write(self._path(voice, key), pcm)

    def has_on_disk(self, voice, language, text):
        return os.path.exists(self._path(voice, self.key(voice, language, text)))

    def _remember(self, key, pcm):
        with self.lock:
            if key in self.memory:
                return
            self.memory[key] = pcm
            self.size += pcm.nbytes
            while self.size > self.max_bytes and self.memory:
                _, old = self.memory.popitem(last=False)
                self.size -= old.nbytes

    def _write(self, path, pcm):
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            tmp = path + ".tmp"
            pcm.astype(np.int16).tofile(tmp)
            os.replace(tmp, path)
        except OSError:
            pass
