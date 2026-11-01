#!/usr/bin/env python3
"""Tests for vabaxos-news: RSS, Atom and podcasts, the feed found from a
site's page, the sources on disk, and the window with a made-up network
and player on Broadway.

    python3 tests/news/test_news.py
"""

import io
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ROOT = os.path.join(REPO, "packages", "vabaxos-news", "root")
LIB = os.path.join(ROOT, "usr", "lib", "python3", "dist-packages")
PROGRAM = os.path.join(ROOT, "usr", "bin", "vabaxos-news")
sys.path.insert(0, LIB)

import vabaxos_news as vn  # noqa: E402

RSS = b"""<?xml version="1.0"?><rss version="2.0"><channel><title>Il Post</title>
<item><title>Notizia uno</title><link>https://example.org/1</link>
<description>&lt;p&gt;Testo &amp;amp; altro&lt;/p&gt;&lt;p&gt;Secondo&lt;/p&gt;</description>
<pubDate>Mon, 02 Nov 2026 10:00:00 +0100</pubDate></item>
<item><title>Morning</title><pubDate>Mon, 02 Nov 2026 07:00:00 +0100</pubDate>
<enclosure url="https://example.org/e.mp3" type="audio/mpeg" length="1"/></item>
</channel></rss>"""
ATOM = b"""<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"><title>Blog</title>
<entry><title>Post</title><link href="https://example.org/p"/><updated>2026-11-01T09:00:00Z</updated>
<summary>Riassunto</summary></entry>
<entry><title>Episodio</title><link rel="enclosure" type="audio/ogg" href="https://example.org/e.ogg"/></entry>
</feed>"""
PAGE = b'<html><head><link rel="alternate" type="application/rss+xml" title="x" href="/feed/"></head></html>'


class Reply(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def opener(request, timeout=None):
    url = request.full_url
    return Reply({"https://www.ilpost.it": PAGE, "https://www.ilpost.it/feed/": RSS}.get(url, b"<html></html>"))


class FeedTest(unittest.TestCase):

    def test_rss(self):
        title, items = vn.parse_feed(RSS)
        self.assertEqual(title, "Il Post")
        self.assertEqual(items[0].summary, "Testo & altro\nSecondo")
        self.assertEqual(items[0].describe(), "02/11/2026 10:00")
        self.assertEqual(items[1].audio, "https://example.org/e.mp3")
        self.assertEqual(items[1].describe(), "02/11/2026 07:00, podcast")

    def test_atom(self):
        title, items = vn.parse_feed(ATOM)
        self.assertEqual((title, items[0].link, items[0].summary), ("Blog", "https://example.org/p", "Riassunto"))
        self.assertEqual(items[1].audio, "https://example.org/e.ogg")

    def test_not_a_feed(self):
        with self.assertRaises(ValueError):
            vn.parse_feed(b"<html><body>no</body></html>")
        with self.assertRaises(ValueError):
            vn.parse_feed(b"not xml at all <")

    def test_feed_found_from_the_site(self):
        url, title, items = vn.fetch("www.ilpost.it", opener=opener)
        self.assertEqual((url, title, len(items)), ("https://www.ilpost.it/feed/", "Il Post", 2))
        with self.assertRaises(ValueError):
            vn.fetch("example.org", opener=opener)

    def test_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "n.json")
            self.assertEqual(vn.load(path), [])
            vn.save([("Il Post", "https://www.ilpost.it/feed/")], path)
            self.assertEqual(vn.load(path), [("Il Post", "https://www.ilpost.it/feed/")])


CHILD = r'''
import importlib.machinery, importlib.util, sys
loader = importlib.machinery.SourceFileLoader("newsprog", sys.argv[1])
spec = importlib.util.spec_from_loader("newsprog", loader)
program = importlib.util.module_from_spec(spec)
loader.exec_module(program)
import vabaxos_news as vn
from gi.repository import Adw, GLib, Gtk
said, played = [], []
_t, ITEMS = vn.parse_feed(open(sys.argv[3], "rb").read())
def fetcher(address):
    return "https://www.ilpost.it/feed/", "Il Post", ITEMS
class FakePlayer:
    def __init__(self): self.rate, self.on = 1.0, True
    def play(self, url): played.append(url)
    def toggle(self):
        self.on = not self.on
        return self.on
    def jump(self, s): played.append("jump %d" % s)
    def set_rate(self, r): self.rate = r
App, Window = program.window_classes(fetcher=fetcher, player_class=FakePlayer, speak=said.append)

def walk(widget):
    yield widget
    child = widget.get_first_child()
    while child is not None:
        yield from walk(child)
        child = child.get_next_sibling()

def inner(w):
    while w is not None:
        if type(w).__name__ in ("AdwToastWidget", "WindowControls", "AdwBackButton"):
            return True
        w = w.get_parent()
    return False

app = Adw.Application(application_id="org.vabaxos.NewsTest")
def check(app):
    window = Window(app, store=sys.argv[2])
    window.present()
    window.add_source("ilpost.it")
    def added():
        print("SOURCES:" + "|".join(r.get_title() for r in window.source_rows), flush=True)
        window.open_source("Il Post", "https://www.ilpost.it/feed/")
        GLib.timeout_add(400, opened)
        return False
    def opened():
        print("ITEMS:" + "|".join(i.title for i in window.items), flush=True)
        window.open_item(window.items[1])
        window.speed(1)
        window.speed(1)
        window.toggle()
        window.jump(30)
        print("PLAYED:" + "|".join(played), flush=True)
        print("RATE:%s" % window.player.rate, flush=True)
        print("SAID:" + "|".join(said[-4:]), flush=True)
        unnamed = [type(w).__name__ for w in walk(window) if isinstance(w, Gtk.Button) and w.get_mapped()
                   and not w.get_label() and not w.get_tooltip_text() and not inner(w)]
        print("UNNAMED:" + ",".join(unnamed), flush=True)
        app.quit()
        return False
    GLib.timeout_add(400, added)
app.connect("activate", check)
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

    def test_add_open_play(self):
        display = free_display()
        broadway = subprocess.Popen(["gtk4-broadwayd", f":{display}"], stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
        time.sleep(1)
        with tempfile.TemporaryDirectory() as tmp:
            feed = os.path.join(tmp, "feed.xml")
            with open(feed, "wb") as f:
                f.write(RSS)
            env = dict(os.environ, GDK_BACKEND="broadway", BROADWAY_DISPLAY=f":{display}",
                       GSETTINGS_BACKEND="memory", NO_AT_BRIDGE="1", PYTHONPATH=LIB, LANGUAGE="C",
                       LANG="C.UTF-8", PYTHONDONTWRITEBYTECODE="1")
            try:
                result = subprocess.run([sys.executable, "-c", CHILD, PROGRAM, os.path.join(tmp, "n.json"), feed],
                                        env=env, capture_output=True, text=True, timeout=60)
            finally:
                broadway.terminate()
                broadway.wait()
        out = dict(line.split(":", 1) for line in result.stdout.splitlines() if ":" in line)
        err = result.stderr[-2000:]
        self.assertEqual(out.get("SOURCES"), "Il Post", err)
        self.assertEqual(out.get("ITEMS"), "Notizia uno|Morning", err)
        self.assertEqual(out.get("PLAYED"), "https://example.org/e.mp3|jump 30", err)
        self.assertEqual(out.get("RATE"), "1.5", err)
        self.assertEqual(out.get("SAID"), "Speed 1,25.|Speed 1,5.|Paused.|Forward 30 seconds.", err)
        self.assertEqual(out.get("UNNAMED"), "", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
