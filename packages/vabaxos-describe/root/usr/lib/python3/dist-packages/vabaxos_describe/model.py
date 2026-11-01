"""The vision model, downloaded once when the user asks (ADR-0029).

Qwen3.5 0.8B (Apache-2.0, multilingual, 2026), as published for llama.cpp
by its own project (ggml-org/Qwen3.5-0.8B-GGUF): the language model in
Q8_0 and its picture projector (mmproj), about 1 GB together. The files
are chosen from the list of the repository, each checked with the SHA-256
the repository gives (its "lfs.oid"), or with the SHA-256 written in
PINNED when VabaxOS has pinned them; then saved as model.gguf and
mmproj.gguf in the user's folder.
"""

import hashlib
import json
import os
import re
import urllib.request

from . import MODEL, PROJECTOR, user_dir

REPOSITORY = os.environ.get("VABAXOS_DESCRIBE_REPOSITORY", "ggml-org/Qwen3.5-0.8B-GGUF")
API = "https://huggingface.co/api/models/{repo}/tree/main"
FILE = "https://huggingface.co/{repo}/resolve/main/{path}"
# Quantizations in order of preference: Q8_0 keeps a small model sharp.
MODEL_PREFERENCE = ("q8_0", "q6_k", "q5_k_m", "q4_k_m")
PROJECTOR_PREFERENCE = ("q8_0", "f16", "bf16", "f32")
# file name -> SHA-256, when VabaxOS pins the files (checked on a real
# download); empty: the repository's own SHA-256 is used.
PINNED = {}


class DownloadError(RuntimeError):
    pass


def _parts(path):
    """'mmproj-Qwen3.5-0.8B-F16.gguf' -> {'mmproj', 'qwen3', '5', '0', '8b', 'f16', 'gguf'}:
    whole parts, so f16 never matches bf16."""
    return set(re.split(r"[-.]", path.lower()))


def _pick(files, preference):
    for wanted in preference:
        found = [f for f in files if wanted in _parts(f["path"])]
        if found:
            return min(found, key=lambda f: f.get("size", 0))
    return min(files, key=lambda f: f.get("size", 0)) if files else None


def choose(listing):
    """(model file, projector file) from the repository listing."""
    files = [f for f in listing if f.get("type") == "file" and f.get("path", "").endswith(".gguf")]
    projectors = [f for f in files if "mmproj" in f["path"].lower()]
    models = [f for f in files if "mmproj" not in f["path"].lower()]
    model, projector = _pick(models, MODEL_PREFERENCE), _pick(projectors, PROJECTOR_PREFERENCE)
    if model is None or projector is None:
        raise DownloadError("the repository has no model or no picture projector")
    return model, projector


def expected_sha(entry):
    name = os.path.basename(entry["path"])
    if name in PINNED:
        return PINNED[name]
    sha = (entry.get("lfs") or {}).get("oid") or ""
    if len(sha) != 64:
        raise DownloadError(f"no checksum for {name}")
    return sha


def total_size(files):
    return sum(f.get("size") or (f.get("lfs") or {}).get("size", 0) for f in files)


def listing(opener=urllib.request.urlopen):
    with opener(API.format(repo=REPOSITORY), timeout=30) as reply:
        return json.load(reply)


def download(entry, target, progress=None, cancelled=lambda: False, opener=urllib.request.urlopen,
             done_before=0, total=0):
    """One file into target, checked; progress(bytes so far, total)."""
    url = FILE.format(repo=REPOSITORY, path=entry["path"])
    sha = expected_sha(entry)
    digest = hashlib.sha256()
    part = target + ".part"
    received = 0
    with opener(url, timeout=60) as reply, open(part, "wb") as out:
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
                progress(done_before + received, total)
    if digest.hexdigest() != sha:
        os.remove(part)
        raise DownloadError("the file is damaged (wrong checksum)")
    os.replace(part, target)
    return received


def install(progress=None, cancelled=lambda: False, folder=None, opener=urllib.request.urlopen):
    """Downloads the model and the projector into folder (the user's)."""
    folder = folder or user_dir()
    os.makedirs(folder, exist_ok=True)
    model, projector = choose(listing(opener))
    total = total_size([model, projector])
    done = download(model, os.path.join(folder, MODEL), progress, cancelled, opener, 0, total)
    download(projector, os.path.join(folder, PROJECTOR), progress, cancelled, opener, done, total)
    with open(os.path.join(folder, "source.json"), "w", encoding="utf-8") as f:
        json.dump({"repository": REPOSITORY, "model": model["path"], "projector": projector["path"]}, f)
    return folder


def remove(folder=None):
    folder = folder or user_dir()
    for name in (MODEL, PROJECTOR, "source.json"):
        try:
            os.remove(os.path.join(folder, name))
        except OSError:
            pass


def size_text(size):
    return f"{size / 1e9:.1f} GB".replace(".", ",") if size >= 1e9 else f"{round(size / 1e6)} MB"
