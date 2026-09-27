#!/usr/bin/env python3
"""Reproduces the speech-dispatcher 0.12.1 hang that silenced Orca in
VabaxOS (2026-09-27; still in speech-dispatcher's master branch).

With server-side audio, a command with a reply (here LIST VOICES, which
Orca sends when it looks for a voice) while a module sends audio: the
reply reader stops reading and signals reply_cond, but the event thread
waits on event_cond for it, and sleeps for ever. Nobody reads the module
any more; the module blocks writing audio, and speech stops until
speech-dispatcher is restarted. The fix (output-wake-event-reader in
docs/sviluppo/segnalazioni.md) signals event_cond.

    python3 tests/upstream/speechd-reply-race.py [ROUNDS]

Needs speech-dispatcher with the espeak-ng module and a sound server.
Prints "no stall", or "STUCK at round N" (exit status 3).
"""

import sys
import threading
import time

import speechd

LONG = "This is a long sentence that keeps the module busy sending audio to the server. " * 4


def main():
    rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    client = speechd.SSIPClient("race")
    client.set_output_module("espeak-ng")
    query = speechd.SSIPClient("query")
    query.set_output_module("espeak-ng")
    for i in range(1, rounds + 1):
        client.cancel()
        client.speak(LONG)
        time.sleep(0.05 * (i % 5))
        query.list_synthesis_voices()
        done = threading.Event()
        client.cancel()
        client.speak("probe", callback=lambda *args, **kwargs: done.set(),
                     event_types=(speechd.CallbackType.END, speechd.CallbackType.CANCEL))
        if not done.wait(60):
            print(f"STUCK at round {i}", flush=True)
            return 3
    print("no stall", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
