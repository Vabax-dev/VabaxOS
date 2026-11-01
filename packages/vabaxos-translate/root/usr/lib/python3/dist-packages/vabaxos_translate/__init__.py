"""Translation without Internet, with the multilingual model VabaxOS
already downloads on request for the descriptions of pictures (Qwen3.5
0.8B, Apache-2.0, ADR-0029) and llama.cpp of Debian: nothing more in the
ISO. A model so small gives the meaning well, not a text to sign.

Argos Translate and Bergamot are not in Debian; Firefox translates web
pages by itself without Internet.

    Engine()               the llama.cpp server, started once, stopped at the end
    engine.translate(text, target)
"""

import gettext
import json
import re
import subprocess
import time
import urllib.request

import vabaxos_describe as vd

_ = gettext.translation("vabaxos-translate", fallback=True).gettext

# code: the name of the language in English, for the model.
LANGUAGES = {"it": "Italian", "en": "English", "fr": "French", "de": "German", "es": "Spanish",
             "pt": "Portuguese"}
CHUNK = 900          # characters per request: a small model keeps its quality


class TranslateError(RuntimeError):
    pass


def chunks(text, size=CHUNK):
    """Paragraphs, joined up to size; a long paragraph cut at sentence ends."""
    parts = []
    for paragraph in re.split(r"\n\s*\n", text.strip()):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        sentences = re.split(r"(?<=[.!?…])\s+", paragraph) if len(paragraph) > size else [paragraph]
        current = ""
        for sentence in sentences:
            if current and len(current) + len(sentence) + 1 > size:
                parts.append(current)
                current = sentence
            else:
                current = f"{current} {sentence}".strip()
        if current:
            parts.append(current)
    return parts


def request_body(text, target, fallback="en"):
    name, other = LANGUAGES.get(target, "Italian"), LANGUAGES.get(fallback, "English")
    if other == name:
        other = "English" if name != "English" else "Italian"
    return {
        "messages": [
            {"role": "system", "content": (
                f"You are a translator. Translate the user's text into {name}. If the text is already in "
                f"{name}, translate it into {other} instead. Keep the meaning, the names and the line breaks. "
                "Answer with the translation only, without notes or quotation marks.")},
            {"role": "user", "content": text},
        ],
        "temperature": 0.1,
        "max_tokens": max(64, len(text)),
    }


def clean(answer):
    """The translation without what small models add around it."""
    text = (answer or "").strip()
    text = re.sub(r"^(translation|traduzione)\s*:\s*", "", text, flags=re.IGNORECASE)
    pairs = {'"': '"', "'": "'", "«": "»", "“": "”"}
    if len(text) > 1 and pairs.get(text[0]) == text[-1]:
        text = text[1:-1].strip()
    return text


def answer_text(reply):
    """Like vabaxos_describe.answer_text, but keeping the line breaks."""
    try:
        text = reply["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return ""
    if isinstance(text, list):
        text = " ".join(part.get("text", "") for part in text if isinstance(part, dict))
    return text


class Engine:
    """llama-server with the model, kept running while the window is open."""

    def __init__(self, folder=None):
        self.folder = folder or vd.model_dir()
        self.server = None
        self.base = None

    @staticmethod
    def available(folder=None):
        return vd.available(folder)

    def start(self, timeout=120):
        if self.server is not None and self.server.poll() is None:
            return
        port = vd.free_port()
        self.server = subprocess.Popen(vd.server_command(port, self.folder), stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL)
        self.base = f"http://127.0.0.1:{port}"
        deadline = time.monotonic() + timeout
        while True:
            if self.server.poll() is not None:
                raise TranslateError("the translation engine stopped")
            try:
                with urllib.request.urlopen(self.base + "/health", timeout=2) as health:
                    if health.status == 200:
                        return
            except OSError:
                pass
            if time.monotonic() > deadline:
                self.stop()
                raise TranslateError("the translation engine did not start")
            time.sleep(0.5)

    def ask(self, body, timeout=300):
        query = urllib.request.Request(self.base + "/v1/chat/completions", data=json.dumps(body).encode("utf-8"),
                                       headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(query, timeout=timeout) as reply:
            return clean(answer_text(json.load(reply)))

    def translate(self, text, target="it", fallback="en", progress=None):
        if not text.strip():
            return ""
        self.start()
        parts = chunks(text)
        out = []
        for index, part in enumerate(parts):
            out.append(self.ask(request_body(part, target, fallback)))
            if progress and len(parts) > 1:
                progress(index + 1, len(parts))
        return "\n\n".join(out)

    def stop(self):
        if self.server is None:
            return
        self.server.terminate()
        try:
            self.server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.server.kill()
        self.server = None
