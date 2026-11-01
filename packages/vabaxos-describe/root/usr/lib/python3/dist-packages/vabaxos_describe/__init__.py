"""Descriptions of pictures, on the computer (ADR-0029, proposed): a
llama.cpp server with a vision model is started, asked, and stopped.

The server speaks the OpenAI chat format: the picture goes in a message as
a data URL. Pure functions here, so the request and the answer are tested
without a model (tests/describe).
"""

import base64
import json
import mimetypes
import os
import shutil
import socket
import subprocess
import time
import urllib.request

MODEL_DIR = os.environ.get("VABAXOS_DESCRIBE_DIR", "/usr/share/vabaxos/describe")
MODEL = "model.gguf"
PROJECTOR = "mmproj.gguf"

PROMPTS = {
    "it": "Descrivi questa immagine a una persona cieca, in italiano, in tre o quattro frasi brevi: "
          "prima cosa mostra nel complesso, poi i dettagli importanti, i colori principali e l'eventuale "
          "testo scritto. Non cominciare con «L'immagine mostra».",
    "en": "Describe this picture to a blind person, in English, in three or four short sentences: first "
          "what it shows as a whole, then the important details, the main colours and any written text. "
          "Do not start with \"The image shows\".",
}


def available(model_dir=MODEL_DIR):
    return (shutil.which("llama-server") is not None and os.path.exists(os.path.join(model_dir, MODEL))
            and os.path.exists(os.path.join(model_dir, PROJECTOR)))


def prompt(language):
    return PROMPTS.get(language[:2], PROMPTS["en"])


def data_url(path):
    kind = mimetypes.guess_type(path)[0] or "image/png"
    with open(path, "rb") as f:
        return f"data:{kind};base64," + base64.b64encode(f.read()).decode("ascii")


def request_body(path, language):
    return {
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": prompt(language)},
            {"type": "image_url", "image_url": {"url": data_url(path)}},
        ]}],
        "temperature": 0.2,
        "max_tokens": 300,
    }


def answer_text(reply):
    """The words of the model, from the server's JSON answer."""
    try:
        text = reply["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return ""
    if isinstance(text, list):
        text = " ".join(part.get("text", "") for part in text if isinstance(part, dict))
    return " ".join(text.split())


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def server_command(port, model_dir=MODEL_DIR, threads=None):
    threads = threads or max(1, (os.cpu_count() or 2) - 1)
    return ["llama-server", "-m", os.path.join(model_dir, MODEL), "--mmproj", os.path.join(model_dir, PROJECTOR),
            "--host", "127.0.0.1", "--port", str(port), "-t", str(threads), "-c", "4096"]


def describe(path, language, model_dir=MODEL_DIR, timeout=300):
    """The description of a picture; starts and stops the server."""
    port = free_port()
    server = subprocess.Popen(server_command(port, model_dir), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{port}"
    try:
        deadline = time.monotonic() + 120
        while True:
            if server.poll() is not None:
                raise RuntimeError("the description engine stopped")
            try:
                with urllib.request.urlopen(base + "/health", timeout=2) as health:
                    if health.status == 200:
                        break
            except OSError:
                pass
            if time.monotonic() > deadline:
                raise RuntimeError("the description engine did not start")
            time.sleep(0.5)
        body = json.dumps(request_body(path, language)).encode("utf-8")
        query = urllib.request.Request(base + "/v1/chat/completions", data=body,
                                       headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(query, timeout=timeout) as reply:
            return answer_text(json.load(reply))
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
