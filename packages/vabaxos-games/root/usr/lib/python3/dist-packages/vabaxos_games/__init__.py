"""Audio games of VabaxOS: the rules, without sound or windows, so they are
tested alone (tests/games). Sounds are made here too, as WAV bytes."""

import io
import math
import random
import struct
import wave


class Guess:
    """Guess the number from 1 to 100: higher, lower, right."""

    def __init__(self, rng=random, top=100):
        self.top = top
        self.number = rng.randint(1, top)
        self.tries = 0

    def guess(self, value):
        self.tries += 1
        if value < self.number:
            return "higher"
        if value > self.number:
            return "lower"
        return "right"


class Simon:
    """A sequence of notes 1-4, one longer each round; the player repeats it."""

    def __init__(self, rng=random):
        self.rng = rng
        self.sequence = []
        self.position = 0

    def next_round(self):
        self.sequence.append(self.rng.randint(1, 4))
        self.position = 0
        return list(self.sequence)

    def press(self, note):
        """'ok' (go on), 'round' (the whole sequence right), 'wrong', or
        'wait' (the round is over: the next one is being played)."""
        if self.position >= len(self.sequence):
            return "wait"
        if note != self.sequence[self.position]:
            return "wrong"
        self.position += 1
        return "round" if self.position == len(self.sequence) else "ok"

    def score(self):
        return max(0, len(self.sequence) - 1)


LINES = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]
# Keys 1-9 as on the number pad: 7 8 9 the top row, 1 2 3 the bottom one.
KEY_TO_CELL = {7: 0, 8: 1, 9: 2, 4: 3, 5: 4, 6: 5, 1: 6, 2: 7, 3: 8}
CELL_TO_KEY = {cell: key for key, cell in KEY_TO_CELL.items()}


class TicTacToe:
    """You are X, the computer O."""

    def __init__(self, rng=random):
        self.rng = rng
        self.cells = [""] * 9

    def free(self):
        return [i for i, c in enumerate(self.cells) if not c]

    def winner(self):
        for a, b, c in LINES:
            if self.cells[a] and self.cells[a] == self.cells[b] == self.cells[c]:
                return self.cells[a]
        return "draw" if not self.free() else None

    def place(self, cell, mark="X"):
        if self.cells[cell] or self.winner():
            return False
        self.cells[cell] = mark
        return True

    def computer(self):
        """Win if it can, else block, else the centre, a corner, any cell."""
        for mark in ("O", "X"):
            for a, b, c in LINES:
                line = [self.cells[a], self.cells[b], self.cells[c]]
                if line.count(mark) == 2 and line.count("") == 1:
                    cell = (a, b, c)[line.index("")]
                    self.cells[cell] = "O"
                    return cell
        for choice in ([4], [0, 2, 6, 8], self.free()):
            options = [c for c in choice if not self.cells[c]]
            if options:
                cell = self.rng.choice(options)
                self.cells[cell] = "O"
                return cell
        return None


NOTES = {1: 523.25, 2: 659.25, 3: 783.99, 4: 1046.5}  # C E G C
RATE = 22050


def tone(frequency, seconds=0.3, volume=0.4):
    count = int(RATE * seconds)
    fade = int(RATE * 0.01)
    samples = [int(32767 * volume * min(1.0, i / fade, (count - i) / fade) *
                   math.sin(2 * math.pi * frequency * i / RATE)) for i in range(count)]
    data = io.BytesIO()
    with wave.open(data, "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(struct.pack(f"<{count}h", *samples))
    return data.getvalue()


def chord(frequencies, seconds=0.5):
    """Notes one after another, as one sound (a win, a mistake)."""
    parts = [tone(f, seconds / len(frequencies)) for f in frequencies]
    frames = b"".join(p[44:] for p in parts)
    data = io.BytesIO()
    with wave.open(data, "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(frames)
    return data.getvalue()
