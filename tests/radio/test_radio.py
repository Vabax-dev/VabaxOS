#!/usr/bin/env python3
"""Tests for vabaxos-radio: the catalog's answers, the servers tried in
turn, the search by name then by kind, the favourites, and the window on
Broadway with a made-up catalog and player.

    python3 tests/radio/test_radio.py
"""

import io
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ROOT = os.path.join(REPO, "packages", "vabaxos-radio", "root")
LIB = os.path.join(ROOT, "usr", "lib", "python3", "dist-packages")
PROGRAM = os.path.join(ROOT, "usr", "bin", "vabaxos-radio")
sys.path.insert(0, LIB)

import vabaxos_radio as vr  # noqa: E402

ANSWER = [
    {"stationuuid": "a1", "name": "Radio  Deejay", "url": "http://x/deejay", "url_resolved": "http://r/deejay",
     "country": "Italy", "countrycode": "IT", "tags": "pop,dance,hits", "codec": "MP3", "bitrate": 128,
     "lastcheckok": 1},
    {"stationuuid": "a2", "name": "Rai Radio 3", "url": "http://x/radio3", "url_resolved": "",
     "country": "Italy", "countrycode": "IT", "tags": "classical", "bitrate": "96", "lastcheckok": 1},
    {"stationuuid": "a3", "name": "Broken", "url": "http://x/broken", "lastcheckok": 0},
    {"stationuuid": "a4", "name": "", "url": "http://x/noname", "lastcheckok": 1},
    {"stationuuid": "a5", "name": "Deejay again", "url": "http://r/deejay", "lastcheckok": 1},
]


class Reply(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class CatalogTest(unittest.TestCase):

    def test_parse_and_describe(self):
        stations = vr.parse(ANSWER)
        self.assertEqual([(s.name, s.url) for s in stations],
                         [("Radio Deejay", "http://r/deejay"), ("Rai Radio 3", "http://x/radio3")])
        self.assertEqual(stations[0].describe(), "Radio Deejay, Italy, pop and dance, 128 kilobit")
        self.assertEqual(stations[1].bitrate, 96)

    def test_servers_in_turn_and_user_agent(self):
        asked = []

        def opener(request, timeout=15):
            asked.append((request.full_url, request.get_header("User-agent")))
            if "all.api" in request.full_url:
                raise OSError("down")
            return Reply(json.dumps(ANSWER).encode())
        found = vr.top("IT", opener)
        self.assertEqual(len(found), 2)
        self.assertIn("countrycode=IT", asked[1][0])
        self.assertTrue(asked[1][0].startswith("https://de1.api.radio-browser.info/json/stations/search?"))
        self.assertTrue(asked[1][1].startswith("VabaxOS-Radio/"))
        with self.assertRaises(ConnectionError):
            vr.api("/json/stations/search", opener=lambda *a, **k: (_ for _ in ()).throw(OSError("no")))

    def test_search_by_name_then_by_kind(self):
        asked = []

        def opener(request, timeout=15):
            asked.append(request.full_url)
            return Reply(json.dumps([] if "name=" in request.full_url else ANSWER[:1]).encode())
        found = vr.search("Jazz", "", opener)
        self.assertEqual(len(found), 1)
        self.assertIn("name=Jazz", asked[0])
        self.assertIn("tag=jazz", asked[1])
        self.assertNotIn("countrycode", asked[1])

    def test_favourites(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "vabaxos", "radio.json")
            self.assertEqual(vr.load(path), [])
            vr.save(vr.parse(ANSWER)[:1], path)
            self.assertEqual(vr.load(path)[0].name, "Radio Deejay")


CHILD = r'''
import importlib.machinery, importlib.util, sys, types
loader = importlib.machinery.SourceFileLoader("radioprog", sys.argv[1])
spec = importlib.util.spec_from_loader("radioprog", loader)
program = importlib.util.module_from_spec(spec)
loader.exec_module(program)
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk
import vabaxos_radio as vr

said, searched, clicks = [], [], []
STATIONS = [vr.Station("a1", "Radio Deejay", "http://r/deejay", "Italy", "IT", ["pop"], "MP3", 128),
            vr.Station("a2", "Rai Radio 3", "http://r/radio3", "Italy", "IT", ["classical"], "MP3", 96)]

def search(words, country):
    searched.append((words, country))
    return STATIONS if not words else STATIONS[1:]

catalog = types.SimpleNamespace(search=search, clicked=clicks.append, load=vr.load, save=vr.save)

class FakePlayer:
    def __init__(self, on_error=None):
        self.playing, self.title, self.volume, self.url = False, "", 1.0, None
    def play(self, url):
        self.url, self.playing, self.title = url, True, "Bach, Concerto brandeburghese"
    def stop(self):
        self.playing = False

App, Window = program.window_classes(speak=said.append, catalog=catalog, player_class=FakePlayer,
                                     favourites_path=sys.argv[2])
app = Adw.Application(application_id="org.vabaxos.RadioTest")

def check(app):
    window = Window(app)
    window.present()
    def step1():
        print("START:" + window.list_group.get_description() + " " + "|".join(r.get_title() for r in window.rows),
              flush=True)
        window.entry.set_text("classica")
        window.search()
        GLib.timeout_add(400, step2)
        return False
    def step2():
        print("FOUND:" + said[-1] + " " + repr(searched[-1]), flush=True)
        window.rows[0].emit("activated")
        print("PLAY:" + said[-1] + " " + window.player.url + " " + window.now.get_title(), flush=True)
        window.say_title()
        print("TITLE:" + said[-1], flush=True)
        window.toggle_favourite()
        print("FAV:" + said[-1] + " " + "|".join(r.get_title() for r in window.fav_rows), flush=True)
        window.change_volume(-1)
        print("VOLUME:" + said[-1], flush=True)
        window.toggle()
        print("STOP:" + said[-1] + " " + window.now.get_title(), flush=True)
        window.failed("boom")
        print("FAILED:" + said[-1], flush=True)
        window.world.set_active(True)
        GLib.timeout_add(300, step3)
        return False
    def step3():
        print("WORLD:" + repr(searched[-1]), flush=True)
        GLib.timeout_add(200, lambda: print("CLICKS:" + str(len(clicks)), flush=True) or app.quit())
        return False
    GLib.timeout_add(400, step1)

app.connect("activate", check)
app.hold()
app.run([])
'''


def free_display():
    for number in range(60, 100):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", 8080 + number)) != 0:
                return number
    raise RuntimeError("no free Broadway display")


@unittest.skipUnless(shutil.which("gtk4-broadwayd"), "gtk4-broadwayd (libgtk-4-bin) is not installed")
class WindowTest(unittest.TestCase):

    def test_window(self):
        display = free_display()
        broadway = subprocess.Popen(["gtk4-broadwayd", f":{display}"], stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
        time.sleep(1)
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder)
        env = dict(os.environ, GDK_BACKEND="broadway", BROADWAY_DISPLAY=f":{display}", GSETTINGS_BACKEND="memory",
                   NO_AT_BRIDGE="1", PYTHONPATH=LIB, LANGUAGE="C", LANG="C.UTF-8", PYTHONDONTWRITEBYTECODE="1")
        try:
            result = subprocess.run([sys.executable, "-c", CHILD, PROGRAM, os.path.join(folder, "radio.json")],
                                    env=env, capture_output=True, text=True, timeout=60, check=False)
        finally:
            broadway.terminate()
            broadway.wait()
        out = dict(line.split(":", 1) for line in result.stdout.splitlines() if ":" in line)
        err = result.stderr[-3000:]
        self.assertEqual(out.get("START"), "The most listened Italian stations. Radio Deejay|Rai Radio 3", err)
        self.assertEqual(out.get("FOUND"), "1 station found. ('classica', 'IT')", err)
        self.assertEqual(out.get("PLAY"), "Rai Radio 3. http://r/radio3 Playing: Rai Radio 3", err)
        self.assertEqual(out.get("TITLE"), "On air: Bach, Concerto brandeburghese", err)
        self.assertEqual(out.get("FAV"), "Rai Radio 3 added to the favourites. Rai Radio 3", err)
        self.assertEqual(out.get("VOLUME"), "Volume 90 percent.", err)
        self.assertEqual(out.get("STOP"), "Stopped. Stopped: Rai Radio 3", err)
        self.assertEqual(out.get("FAILED"), "Rai Radio 3 does not answer: try another station.", err)
        self.assertEqual(out.get("WORLD"), "('classica', '')", err)
        self.assertEqual(out.get("CLICKS"), "1", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
