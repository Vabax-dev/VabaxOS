"""Speech Dispatcher output module for Kokoro (ADR-0019).

Speaks the output module protocol of Speech Dispatcher on stdin and stdout
(doc/speech-dispatcher.texi, "Communication Protocol for Output Modules").
Orca talks to Speech Dispatcher, which starts this module as sd_kokoro.

How it keeps the delay short:
- the model is loaded once, at INIT, and warmed up;
- phrases already said come from the cache (vabaxos_voice.cache);
- a message is cut at sentence and clause ends: the first part plays while
  the next one is synthesized;
- silence before and after each part is removed (engine.trim);
- audio goes out with a 30 ms buffer and stops within 20 ms on STOP.

Rate, pitch and volume are applied at playback (Sonic), so the cache holds
one copy of each phrase for every speed. Languages Kokoro does not have, and
single characters it cannot say, are spoken by eSpeak NG.
"""

import html
import io
import os
import queue
import re
import subprocess
import sys
import threading
import time
import wave

import numpy as np

from . import engine
from .cache import PhraseCache
from .player import make_player

CONFIG = "/etc/speech-dispatcher/modules/kokoro.conf"
STATE = "/var/lib/vabaxos/voice.conf"
PHRASES = os.path.join(engine.DATA_DIR, "phrases-{lang}.txt")

_MARK = re.compile(r"<mark\s+name=\"([^\"]*)\"\s*/>")
_TAG = re.compile(r"<[^>]+>")


def log(*args):
    print("sd_kokoro:", *args, file=sys.stderr, flush=True)


def read_config(paths):
    """Voice per language: 'DefaultVoice it im_nicola' in kokoro.conf, or
    'it=im_nicola' in the state file written by vabaxos-voice-select."""
    voices = {}
    for path in paths:
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.split("#", 1)[0].strip()
                    parts = line.split()
                    if len(parts) == 3 and parts[0] == "DefaultVoice":
                        voices[parts[1]] = parts[2].strip('"')
                    elif "=" in line and " " not in line:
                        lang, voice = line.split("=", 1)
                        voices[lang] = voice
        except OSError:
            pass
    return voices


def parse_ssml(text):
    """SSML from Speech Dispatcher to a list of ('mark', name) and
    ('text', words), in order."""
    items = []
    pos = 0
    for match in _MARK.finditer(text):
        items.append(("text", text[pos:match.start()]))
        items.append(("mark", match.group(1)))
        pos = match.end()
    items.append(("text", text[pos:]))
    out = []
    for kind, value in items:
        if kind == "text":
            value = html.unescape(_TAG.sub(" ", value))
            value = " ".join(value.split())
            if not value:
                continue
            for part in engine.split(value):
                out.append(("text", part))
        else:
            out.append((kind, value))
    return out


def speed_for(rate):
    """Speech Dispatcher rate -100..100 to a Sonic speed 0.5..2.5."""
    rate = max(-100, min(100, rate))
    return 1.0 + rate / 200.0 if rate < 0 else 1.0 + rate / 100.0 * 1.5


def pitch_for(pitch):
    pitch = max(-100, min(100, pitch))
    return 1.0 + pitch / 400.0


def gain_for(volume):
    volume = max(-100, min(100, volume))
    return (volume + 100) / 100.0


class Module:
    def __init__(self, out=sys.stdout, config=CONFIG, state=STATE):
        self.out = out
        self.out_lock = threading.Lock()
        self.settings = {"rate": 0, "pitch": 0, "volume": 0, "language": "it",
                         "voice": "NULL", "synthesis_voice": "NULL"}
        self.voices = read_config([config, state])
        self.kokoro = None
        self.cache = None
        self.player = None
        self.job = None
        self.cancel = threading.Event()
        self.busy = threading.Event()
        self.running = None
        self.preparing = None

    # -- output --------------------------------------------------------

    def send(self, *lines):
        with self.out_lock:
            for line in lines:
                self.out.write(line + "\n")
            self.out.flush()

    # -- startup -------------------------------------------------------

    def init(self):
        self.kokoro = engine.Kokoro()
        self.cache = PhraseCache()
        self.player = make_player(engine.SAMPLE_RATE)
        # The first run of the model is slow: do it now, not on the first word.
        self.kokoro.synthesize("pronto", self.voice_for("it"), "it")
        threading.Thread(target=self.prepare_phrases, daemon=True).start()
        return "Kokoro loaded"

    def prepare_phrases(self):
        """Fills the disk cache with the phrases a screen reader says most,
        while nothing is being spoken."""
        for lang in engine.VOICES:
            voice = self.voice_for(lang)
            try:
                with open(PHRASES.format(lang=lang), encoding="utf-8") as f:
                    phrases = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            except OSError:
                continue
            for phrase in phrases:
                if self.cache.has_on_disk(voice, lang, phrase):
                    continue
                while self.busy.is_set():
                    time.sleep(0.5)
                options = self.kokoro.run_options()
                self.preparing = options
                try:
                    pcm = self.kokoro.synthesize(phrase, voice, lang, options)
                except Exception:  # noqa: BLE001 - interrupted by speech: try again later
                    continue
                finally:
                    self.preparing = None
                self.cache.put(voice, lang, phrase, pcm, persist=True)

    # -- voices --------------------------------------------------------

    def language(self):
        lang = (self.settings.get("language") or "it").lower()
        return lang.split("-")[0].split("_")[0]

    def voice_for(self, lang):
        """The voice for a language: one chosen explicitly by the client,
        else the one chosen for this computer (vabaxos-voice-select or
        kokoro.conf), else one of the requested gender, else the first.
        Speech Dispatcher always sends a voice type (MALE1 by default), so
        the choice for this computer comes before it."""
        chosen = self.settings.get("synthesis_voice")
        if chosen and chosen != "NULL" and chosen in self.kokoro.voices and chosen[0] == lang[0]:
            return chosen
        names = engine.VOICES.get(lang, [])
        if self.voices.get(lang) in names:
            return self.voices[lang]
        kind = (self.settings.get("voice") or "").lower()
        gender = "m" if kind.startswith(("male", "child_male")) else "f" if kind.startswith(("female", "child_female")) else None
        matching = [n for n in names if n[1] == gender]
        return (matching or names or [None])[0]

    def list_voices(self):
        lines = []
        for lang, names in engine.VOICES.items():
            for name in names:
                lines.append(f"200-{name}\t{lang}\tnone")
        lines.append("200 OK VOICE LIST SENT")
        self.send(*lines)

    # -- speaking ------------------------------------------------------

    def speak(self, text, kind="text"):
        self.stop_and_wait()
        self.cancel.clear()
        self.busy.set()
        preparing = self.preparing
        if preparing is not None:
            preparing.terminate = True  # speech first; the phrase is redone later
        self.job = threading.Thread(target=self.run_job, args=(text, kind), daemon=True)
        self.job.start()

    def stop_and_wait(self):
        if self.job and self.job.is_alive():
            self.cancel.set()
            self.job.join()

    def stop(self):
        self.cancel.set()
        running = self.running
        if running is not None:
            running.terminate = True

    def synth(self, text, lang, voice):
        pcm = self.cache.get(voice, lang, text)
        if pcm is None:
            options = self.kokoro.run_options()
            self.running = options
            try:
                pcm = self.kokoro.synthesize(text, voice, lang, options)
            finally:
                self.running = None
            self.cache.put(voice, lang, text, pcm)
        return pcm

    def run_job(self, text, kind):
        began = False
        try:
            lang = self.language()
            voice = self.voice_for(lang) if lang in engine.VOICES else None
            if kind == "text":
                items = parse_ssml(text)
            else:
                word = text.strip()
                if kind == "key":
                    word = word.replace("_", " ")
                items = [("text", word)] if word else []
            if voice is None or (kind == "char" and not self.kokoro.tokens(text, lang)):
                self.send("701 BEGIN")
                began = True
                done = self.speak_espeak(" ".join(v for k, v in items if k == "text") or text, lang, kind)
                self.send("702 END" if done else "703 STOP")
                return
            speed = speed_for(int(self.settings.get("rate") or 0))
            pitch = pitch_for(int(self.settings.get("pitch") or 0))
            gain = gain_for(int(self.settings.get("volume") or 0))
            ready = queue.Queue(maxsize=2)

            def produce():
                for item_kind, value in items:
                    if self.cancel.is_set():
                        break
                    if item_kind == "text":
                        try:
                            pcm = self.synth(value, lang, voice)
                        except Exception:  # noqa: BLE001 - terminated by STOP, or failed
                            if not self.cancel.is_set():
                                raise
                            break
                        pcm = self.kokoro.sonic(pcm, speed, pitch)
                        if gain != 1.0:
                            pcm = np.clip(pcm.astype(np.float32) * gain, -32768, 32767).astype(np.int16)
                        ready.put(("audio", pcm))
                    else:
                        ready.put((item_kind, value))
                ready.put(("end", None))

            producer = threading.Thread(target=produce, daemon=True)
            producer.start()
            while True:
                try:
                    item_kind, value = ready.get(timeout=0.02)
                except queue.Empty:
                    if self.cancel.is_set():
                        break
                    continue
                if self.cancel.is_set():
                    break
                if item_kind == "end":
                    break
                if not began:
                    self.send("701 BEGIN")
                    began = True
                if item_kind == "mark":
                    self.send(f"700-{value}", "700 INDEX MARK")
                elif not self.player.play(value, self.cancel.is_set):
                    break
            if not self.cancel.is_set():
                self.player.drain(self.cancel.is_set)
            # Let the producer finish its current part and exit.
            while producer.is_alive():
                try:
                    ready.get(timeout=0.05)
                except queue.Empty:
                    pass
            if not began:
                self.send("701 BEGIN")
            self.send("703 STOP" if self.cancel.is_set() else "702 END")
        except Exception as error:  # noqa: BLE001 - report and stay alive
            log("speak failed:", repr(error))
            if not began:
                self.send("701 BEGIN")
            self.send("703 STOP")
        finally:
            self.busy.clear()

    def speak_espeak(self, text, lang, kind):
        """eSpeak NG for what Kokoro cannot say (other languages, symbols)."""
        wpm = int(175 * speed_for(int(self.settings.get("rate") or 0)))
        args = ["espeak-ng", "--stdout", "-v", lang or "en", "-s", str(wpm)]
        if kind == "char":
            args.append("--punct")
        result = subprocess.run(args + [text], capture_output=True, check=False)
        if result.returncode != 0 or not result.stdout:
            return True
        with wave.open(io.BytesIO(result.stdout)) as w:
            rate = w.getframerate()
            pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
        player = make_player(rate)
        try:
            ok = player.play(pcm, self.cancel.is_set)
            return player.drain(self.cancel.is_set) and ok
        finally:
            player.close()

    # -- protocol ------------------------------------------------------

    def read_block(self, stdin):
        lines = []
        for line in stdin:
            line = line.rstrip("\n")
            if line == ".":
                break
            if line.startswith(".."):
                line = line[1:]
            lines.append(line)
        return lines

    def read_params(self, stdin):
        params = {}
        for line in self.read_block(stdin):
            if "=" in line:
                name, value = line.split("=", 1)
                params[name] = value
        return params

    def loop(self, stdin):
        first = stdin.readline()
        if first.strip() != "INIT":
            log("server did not start with INIT")
            return 3
        try:
            message = self.init()
        except Exception as error:  # noqa: BLE001 - tell the server why
            self.send(f"399-{error}", "399 ERR CANT INIT MODULE")
            return 1
        self.send(f"299-{message}", "299 OK LOADED SUCCESSFULLY")
        while True:
            line = stdin.readline()
            if not line:
                return 0
            command = line.strip()
            if command in ("SPEAK", "CHAR", "KEY", "SOUND_ICON"):
                self.send("202 OK RECEIVING MESSAGE")
                text = "\n".join(self.read_block(stdin))
                self.send("200 OK SPEAKING")
                if command == "SOUND_ICON":
                    self.send("701 BEGIN", "702 END")
                else:
                    self.speak(text, {"SPEAK": "text", "CHAR": "char", "KEY": "key"}[command])
            elif command == "STOP":
                self.stop()
            elif command == "PAUSE":
                self.stop()
            elif command.startswith("LIST VOICES"):
                self.list_voices()
            elif command == "SET":
                self.send("203 OK RECEIVING SETTINGS")
                self.settings.update(self.read_params(stdin))
                self.send("203 OK SETTINGS RECEIVED")
            elif command == "AUDIO":
                self.send("207 OK RECEIVING AUDIO SETTINGS")
                self.read_params(stdin)
                self.send("203 OK AUDIO INITIALIZED")
            elif command == "LOGLEVEL":
                self.send("207 OK RECEIVING LOGLEVEL SETTINGS")
                self.read_params(stdin)
                self.send("203 OK LOGLEVEL SET")
            elif command.startswith("DEBUG"):
                self.send("200 OK DEBUGGING " + ("ON" if " ON" in command else "OFF"))
            elif command == "QUIT":
                self.stop_and_wait()
                if self.player:
                    self.player.close()
                self.send("210 OK QUIT")
                return 0
            else:
                self.send("300 ERR UNKNOWN COMMAND")


def main():
    config = sys.argv[1] if len(sys.argv) > 1 else CONFIG
    if not os.path.isabs(config):
        config = os.path.join("/etc/speech-dispatcher/modules", config)
    stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", newline="\n")
    return Module(config=config).loop(stdin)
