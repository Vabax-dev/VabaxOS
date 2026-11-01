"""The Kokoro model, downloaded when the user asks for the natural voice.

The same files the package build downloads (packages/vabaxos-voice/fetch):
the ONNX export of Kokoro-82M v1.0 (Apache-2.0) and its voices, published
by the kokoro-onnx project (MIT) on GitHub, each checked with its SHA-256,
saved in ~/.local/share/vabaxos/kokoro. About 350 MB.

    install(progress, cancelled)    progress(bytes so far, total)
    remove(), installed(), measure() and verdict()
"""

import hashlib
import json
import os
import statistics
import time
import urllib.request

from . import engine

BASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
FILES = [
    (engine.MODEL, "7d5df8ecf7d4b1878015a32686053fd0eebe2bc377234608764cc0ef3636a6c5", 325532387),
    (engine.VOICES_FILE, "bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d", 28214398),
]
TOTAL = sum(size for _name, _sha, size in FILES)
SPEED_FILE = "speed.json"
# Phrases a screen reader says often, never cached: what the user waits for.
TEST_PHRASES = {"it": ["Impostazioni", "Nuova cartella", "Casella di controllo selezionata",
                       "Il documento è stato salvato"],
                "en": ["Settings", "New folder", "Check box checked", "The document has been saved"]}
# A short new phrase, in milliseconds (ADR-0026: a screen reader should
# answer within about 0.2 seconds).
FAST_MS = 300
SLOW_MS = 600


class DownloadError(RuntimeError):
    pass


def downloaded(folder=None):
    """The user's own download."""
    return engine.has_model(folder or engine.user_dir())


def installed(folder=None):
    return downloaded(folder) or engine.model_dir() is not None


def download(name, sha, size, folder, progress=None, cancelled=lambda: False, opener=urllib.request.urlopen,
             done_before=0):
    target = os.path.join(folder, name)
    part = target + ".part"
    digest = hashlib.sha256()
    received = 0
    with opener(BASE + name, timeout=60) as reply, open(part, "wb") as out:
        while True:
            if cancelled():
                out.close()
                os.remove(part)
                raise DownloadError("cancelled")
            chunk = reply.read(1 << 20)
            if not chunk:
                break
            out.write(chunk)
            digest.update(chunk)
            received += len(chunk)
            if progress:
                progress(done_before + received, TOTAL)
    if digest.hexdigest() != sha:
        os.remove(part)
        raise DownloadError("damaged")
    os.replace(part, target)
    return received


def install(progress=None, cancelled=lambda: False, folder=None, opener=urllib.request.urlopen):
    folder = folder or engine.user_dir()
    os.makedirs(folder, exist_ok=True)
    done = 0
    for name, sha, size in FILES:
        if os.path.exists(os.path.join(folder, name)) and _sha(os.path.join(folder, name)) == sha:
            done += size
            continue
        done += download(name, sha, size, folder, progress, cancelled, opener, done)
    return folder


def _sha(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def remove(folder=None):
    folder = folder or engine.user_dir()
    for name in [name for name, _sha, _size in FILES] + [SPEED_FILE]:
        try:
            os.remove(os.path.join(folder, name))
        except OSError:
            pass


# -- is this computer fast enough? -------------------------------------------

def measure(kokoro=None, language="it", voice=None):
    """Milliseconds before the first part of a new short phrase is ready
    (the median of the test phrases, without the cache)."""
    kokoro = kokoro or engine.Kokoro()
    voice = voice or engine.VOICES[language][0]
    kokoro.synthesize("prova", voice, language)      # the first run is slower
    times = []
    for phrase in TEST_PHRASES[language]:
        first = engine.split(phrase)[0]
        start = time.perf_counter()
        kokoro.synthesize(first, voice, language)
        times.append((time.perf_counter() - start) * 1000)
    return round(statistics.median(times))


def verdict(ms):
    """'fast', 'slow' or 'too-slow'."""
    if ms <= FAST_MS:
        return "fast"
    if ms <= SLOW_MS:
        return "slow"
    return "too-slow"


def save_speed(ms, folder=None):
    folder = folder or engine.user_dir()
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, SPEED_FILE), "w", encoding="utf-8") as f:
        json.dump({"ms": ms, "verdict": verdict(ms), "when": int(time.time())}, f)


def load_speed(folder=None):
    try:
        with open(os.path.join(folder or engine.user_dir(), SPEED_FILE), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None
