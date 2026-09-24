#!/usr/bin/env python3
"""Prints when a WAV recording has sound, to check beeps and speech without ears.

    wav-timeline.py FILE.wav [--offset SECONDS]

For each stretch of sound: start and end in seconds, loudness, and a guess:
"tone ~NNN Hz" for a steady beep (like the boot menu's 440 Hz), "voice" for
speech. Used with scripts/run-qemu.sh --record-audio.
"""

import array
import math
import sys
import wave

WINDOW = 0.05  # seconds
SILENCE = 300  # RMS below this is silence (16-bit samples)
GAP = 0.4  # seconds of silence that end a stretch


def windows(path):
    with wave.open(path, "rb") as w:
        if w.getsampwidth() != 2:
            sys.exit("only 16-bit WAV files are supported")
        rate, channels = w.getframerate(), w.getnchannels()
        step = int(rate * WINDOW)
        index = 0
        while True:
            frames = w.readframes(step)
            if not frames:
                break
            samples = array.array("h", frames)[::channels]
            if not samples:
                break
            rms = math.sqrt(sum(s * s for s in samples) / len(samples))
            crossings = sum(1 for a, b in zip(samples, samples[1:]) if (a < 0) != (b < 0))
            freq = crossings / 2 / (len(samples) / rate)
            yield index * WINDOW, rms, freq
            index += 1


def main():
    path = sys.argv[1]
    offset = float(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[2] == "--offset" else 0.0
    stretches = []
    current = None
    for t, rms, freq in windows(path):
        if rms >= SILENCE:
            if current and t - current["end"] <= GAP:
                current["end"] = t + WINDOW
                current["rms"].append(rms)
                current["freq"].append(freq)
            else:
                current = {"start": t, "end": t + WINDOW, "rms": [rms], "freq": [freq]}
                stretches.append(current)
    if not stretches:
        print("silenzio: nessun suono nella registrazione")
        return
    for s in stretches:
        freqs = sorted(s["freq"])
        median = freqs[len(freqs) // 2]
        spread = freqs[int(len(freqs) * 0.9)] - freqs[int(len(freqs) * 0.1)]
        kind = f"tono ~{median:.0f} Hz" if spread < 60 else "voce o suono complesso"
        print(f"{s['start'] + offset:7.1f}s - {s['end'] + offset:7.1f}s  "
              f"volume {max(s['rms']):6.0f}  {kind}")


if __name__ == "__main__":
    main()
