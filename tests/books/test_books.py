#!/usr/bin/env python3
"""Tests for vabaxos-books: the answers of Gutendex and LibriVox, the
search by title then by author, the download, the audiobook added to News
and podcasts, and the window on Broadway with a made-up catalog.

    python3 tests/books/test_books.py
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
import urllib.error

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ROOT = os.path.join(REPO, "packages", "vabaxos-books", "root")
LIB = os.path.join(ROOT, "usr", "lib", "python3", "dist-packages")
NEWS = os.path.join(REPO, "packages", "vabaxos-news", "root", "usr", "lib", "python3", "dist-packages")
PROGRAM = os.path.join(ROOT, "usr", "bin", "vabaxos-books")
sys.path[:0] = [LIB, NEWS]

import vabaxos_books as vb  # noqa: E402
import vabaxos_news  # noqa: E402

GUTENDEX = {"count": 2, "results": [
    {"id": 52484, "title": "Le avventure di Pinocchio:\r\nStoria di un burattino",
     "authors": [{"name": "Collodi, Carlo", "birth_year": 1826}], "languages": ["it"],
     "formats": {"application/epub+zip": "https://www.gutenberg.org/ebooks/52484.epub3.images",
                 "text/plain; charset=us-ascii": "https://x/52484.txt"}},
    {"id": 1, "title": "Only pictures", "authors": [], "languages": ["it"], "formats": {"image/jpeg": "x"}},
    {"id": 2, "title": "Testo", "authors": [{"name": "Verga"}], "languages": ["it"],
     "formats": {"text/plain; charset=utf-8": "https://x/2.txt"}}]}
LIBRIVOX = {"books": [
    {"id": "100", "title": "Pinocchio", "language": "Italian", "url_rss": "https://librivox.org/rss/100",
     "totaltime": "04:12:30", "authors": [{"first_name": "Carlo", "last_name": "Collodi"}]},
    {"id": "101", "title": "Pinocchio (English)", "language": "English", "url_rss": "https://librivox.org/rss/101",
     "totaltime": "00:42:00", "authors": [{"first_name": "Carlo", "last_name": "Collodi"}]}]}


class Reply(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class CatalogTest(unittest.TestCase):

    def test_gutendex(self):
        asked = []

        def opener(request, timeout=30):
            asked.append(request.full_url)
            return Reply(json.dumps(GUTENDEX).encode())
        books = vb.search_books("Pinocchio", True, opener)
        self.assertIn("languages=it", asked[0])
        self.assertEqual([(b.title, b.kind) for b in books],
                         [("Le avventure di Pinocchio: Storia di un burattino", "epub"), ("Testo", "text")])
        self.assertEqual(books[0].describe(), "Le avventure di Pinocchio: Storia di un burattino, Carlo Collodi, book")

    def test_librivox_title_then_author(self):
        asked = []

        def opener(request, timeout=30):
            asked.append(request.full_url)
            if "title=" in request.full_url:
                raise urllib.error.HTTPError(request.full_url, 404, "not found", {}, None)
            return Reply(json.dumps(LIBRIVOX).encode())
        books = vb.search_audiobooks("Collodi", True, opener)
        self.assertIn("title=%5ECollodi", asked[0])
        self.assertIn("author=%5ECollodi", asked[1])
        self.assertEqual([b.describe() for b in books], ["Pinocchio, Carlo Collodi, audiobook, 4 hours"])
        self.assertEqual(len(vb.parse_librivox(LIBRIVOX, italian=False)), 2)
        self.assertEqual(vb.parse_librivox(LIBRIVOX, italian=False)[1].duration, "42 minutes")

    def test_download_and_podcasts(self):
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder)
        book = vb.parse_gutendex(GUTENDEX)[0]
        path = vb.download(book, folder, lambda request, timeout=60: Reply(b"PK epub"))
        self.assertEqual(os.path.basename(path), "Le avventure di Pinocchio Storia di un burattino - Carlo Collodi.epub")
        store = os.path.join(folder, "news.json")
        vabaxos_news.save([("Il Post", "https://ilpost.it/feed")], store)
        audio = vb.parse_librivox(LIBRIVOX)[0]
        vb.add_to_podcasts(audio, store)
        vb.add_to_podcasts(audio, store)
        self.assertEqual(vabaxos_news.load(store), [("Il Post", "https://ilpost.it/feed"),
                                                    ("Pinocchio", "https://librivox.org/rss/100")])
        self.assertIn("s=promessi+sposi", vb.liberliber_url("promessi  sposi"))


CHILD = r'''
import importlib.machinery, importlib.util, sys, types
loader = importlib.machinery.SourceFileLoader("booksprog", sys.argv[1])
spec = importlib.util.spec_from_loader("booksprog", loader)
program = importlib.util.module_from_spec(spec)
loader.exec_module(program)
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk
import vabaxos_books as vb

said, launched, browsed, added = [], [], [], []
BOOK = vb.Book("gutenberg", "1", "Pinocchio", ["Carlo Collodi"], "it", "https://x/1.epub", "epub")
AUDIO = vb.Book("librivox", "2", "Pinocchio", ["Carlo Collodi"], "Italian", "https://x/rss", "audio", "4 hours")

def no_audio(words, italian):
    raise OSError("down")

catalog = types.SimpleNamespace(search_books=lambda w, i: [BOOK], search_audiobooks=lambda w, i: [AUDIO],
                                download=lambda book: "/home/x/Documenti/Libri/Pinocchio.epub",
                                add_to_podcasts=added.append, liberliber_url=vb.liberliber_url)
App, Window = program.window_classes(speak=said.append, catalog=catalog,
                                     launcher=lambda *c: launched.append(c) or True, browser=browsed.append)
app = Adw.Application(application_id="org.vabaxos.BooksTest")

def check(app):
    window = Window(app)
    window.present()
    def step1():
        window.entry.set_text("Pinocchio")
        GLib.timeout_add(1300, step2)
        return False
    def step2():
        print("FOUND:" + said[-1] + " / " + window.books.get_description() + " / " + window.audio.get_description(),
              flush=True)
        window.choose(BOOK)
        GLib.timeout_add(400, step3)
        return False
    def step3():
        print("READ:" + said[-1] + " " + repr(launched[-1]), flush=True)
        window.choose(AUDIO)
        print("LISTEN:" + said[-1] + " " + repr(launched[-1]) + " " + str(len(added)), flush=True)
        window.liber_liber()
        print("LIBER:" + browsed[-1], flush=True)
        catalog.search_audiobooks = no_audio
        window.search()
        GLib.timeout_add(600, step4)
        return False
    def step4():
        print("DOWN:" + window.audio.get_description(), flush=True)
        app.quit()
        return False
    GLib.timeout_add(300, step1)

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
        env = dict(os.environ, GDK_BACKEND="broadway", BROADWAY_DISPLAY=f":{display}", GSETTINGS_BACKEND="memory",
                   NO_AT_BRIDGE="1", PYTHONPATH=LIB, LANGUAGE="C", LANG="C.UTF-8", PYTHONDONTWRITEBYTECODE="1")
        try:
            result = subprocess.run([sys.executable, "-c", CHILD, PROGRAM], env=env, capture_output=True, text=True,
                                    timeout=60, check=False)
        finally:
            broadway.terminate()
            broadway.wait()
        out = dict(line.split(":", 1) for line in result.stdout.splitlines() if ":" in line)
        err = result.stderr[-3000:]
        self.assertEqual(out.get("FOUND"), "Books: 1. Audiobooks: 1. / From Project Gutenberg. 1 found. / From "
                                           "LibriVox, read by volunteers. 1 found.", err)
        self.assertEqual(out.get("READ"), "Pinocchio is in Documents, folder Libri: it opens in the document reader. "
                                          "('vabaxos-reader', '/home/x/Documenti/Libri/Pinocchio.epub')", err)
        self.assertEqual(out.get("LISTEN"), "Pinocchio added to News and podcasts: open it there; its chapters are "
                                            "the episodes. ('vabaxos-news',) 1", err)
        self.assertEqual(out.get("LIBER"), "https://www.liberliber.it/online/?s=Pinocchio", err)
        self.assertEqual(out.get("DOWN"), "From LibriVox, read by volunteers. It does not answer: is Internet "
                                          "connected?", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
