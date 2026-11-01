"""Live captions: the audio is cut into phrases, each phrase becomes text.

The audio arrives as raw 16-bit mono at 16 kHz (parec). A phrase ends at a
pause (0.6 s under the loudness of speech) after some speech, or after
8 seconds at most, so the captions follow with a few seconds of delay.
Silence is dropped, never sent to Whisper (see core).
"""

import array

from . import core

PIECE = 0.02           # seconds in a loudness measure
PAUSE = 0.6            # silence that ends a phrase
MAX_PHRASE = 8.0       # longest phrase
MIN_SPEECH = 0.3       # less speech than this is noise


def loud(piece, threshold=core.SILENCE_RMS):
    if not piece:
        return False
    return (sum(s * s for s in piece) / len(piece)) ** 0.5 >= threshold


class Segmenter:
    """Feed raw audio with feed(); get finished phrases (raw bytes) back."""

    def __init__(self, rate=core.RATE, threshold=core.SILENCE_RMS):
        self.rate = rate
        self.threshold = threshold
        self.step = int(rate * PIECE)
        self.buffer = array.array("h")
        self.phrase = array.array("h")
        self.speech = 0.0
        self.quiet = 0.0
        self.pending = b""

    def feed(self, data):
        data = self.pending + data
        usable = len(data) - len(data) % 2
        self.pending = data[usable:]
        self.buffer.frombytes(data[:usable])
        done = []
        while len(self.buffer) >= self.step:
            piece = self.buffer[:self.step]
            del self.buffer[:self.step]
            if loud(piece, self.threshold):
                self.speech += PIECE
                self.quiet = 0.0
                self.phrase.extend(piece)
            elif self.speech > 0:
                self.quiet += PIECE
                self.phrase.extend(piece)
            length = len(self.phrase) / self.rate
            if self.speech > 0 and (self.quiet >= PAUSE or length >= MAX_PHRASE):
                phrase = self.take()
                if phrase:
                    done.append(phrase)
        return done

    def take(self):
        """The phrase so far, if it has enough speech; starts a new one."""
        phrase, speech = self.phrase, self.speech
        self.phrase, self.speech, self.quiet = array.array("h"), 0.0, 0.0
        return phrase.tobytes() if speech >= MIN_SPEECH else None

    def flush(self):
        phrase = self.take()
        return [phrase] if phrase else []


def capture_command(source):
    """parec of the sound the computer plays ("computer") or of the
    microphone ("microphone"), raw 16 kHz mono on standard output."""
    device = "@DEFAULT_MONITOR@" if source == "computer" else "@DEFAULT_SOURCE@"
    return ["parec", f"--device={device}", f"--rate={core.RATE}", "--channels=1", "--format=s16le",
            "--latency-msec=100"]
