"""Free books and audiobooks: Project Gutenberg (through Gutendex, its
catalog for programs) for books to read, LibriVox for audiobooks read by
volunteers; both public domain. Liber Liber has no catalog for programs:
the window opens its search in the browser.

    search_books(words, italian)        [Book] from Project Gutenberg
    search_audiobooks(words, italian)   [Book] from LibriVox
    download(book, folder)              the EPUB, for the document reader
    add_to_podcasts(book)               the audiobook's chapters in News and podcasts
"""

import gettext
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

_ = gettext.translation("vabaxos-books", fallback=True).gettext

GUTENDEX = "https://gutendex.com/books/"
LIBRIVOX = "https://librivox.org/api/feed/audiobooks/"
LIBERLIBER = "https://www.liberliber.it/online/?s={words}"
USER_AGENT = "VabaxOS-Books/1.0 (+https://github.com/Vabax-dev/VabaxOS)"
LIMIT = 30


@dataclass
class Book:
    source: str                  # "gutenberg" or "librivox"
    id: str
    title: str
    authors: list = field(default_factory=list)
    language: str = ""
    url: str = ""                # the EPUB (or text), or the audiobook's RSS
    kind: str = "epub"           # "epub", "text" or "audio"
    duration: str = ""

    def describe(self):
        """'Le avventure di Pinocchio, Carlo Collodi, audiobook, 4 hours'."""
        parts = [self.title]
        if self.authors:
            parts.append(_(" and ").join(self.authors[:2]))
        parts.append(_("audiobook") if self.kind == "audio" else _("book"))
        if self.duration:
            parts.append(self.duration)
        return ", ".join(parts)


def get_json(url, opener=urllib.request.urlopen):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with opener(request, timeout=30) as reply:
        return json.load(reply)


def _author_name(name):
    """'Collodi, Carlo' -> 'Carlo Collodi'."""
    if "," in name:
        last, first = (p.strip() for p in name.split(",", 1))
        return f"{first} {last}".strip()
    return name.strip()


def parse_gutendex(data):
    books = []
    for item in (data or {}).get("results", []):
        formats = item.get("formats") or {}
        epub = next((u for m, u in formats.items() if m.startswith("application/epub+zip")), None)
        text = next((u for m, u in formats.items() if m.startswith("text/plain") and "utf-8" in m.lower()), None)
        if not (epub or text):
            continue
        books.append(Book("gutenberg", str(item.get("id", "")), " ".join((item.get("title") or "").split()),
                          [_author_name(a.get("name", "")) for a in item.get("authors", []) if a.get("name")],
                          ",".join(item.get("languages", [])), epub or text, "epub" if epub else "text"))
    return books


def search_books(words, italian=True, opener=urllib.request.urlopen):
    params = {"search": " ".join(words.split())}
    if italian:
        params["languages"] = "it"
    return parse_gutendex(get_json(GUTENDEX + "?" + urllib.parse.urlencode(params), opener))[:LIMIT]


def _hours(text):
    """'04:12:30' -> '4 hours 12 minutes'."""
    match = re.match(r"(\d+):(\d+):(\d+)", text or "")
    if not match:
        return ""
    hours, minutes = int(match.group(1)), int(match.group(2))
    if hours:
        return gettext.translation("vabaxos-books", fallback=True).ngettext(
            "{hours} hour", "{hours} hours", hours).format(hours=hours)
    return _("{minutes} minutes").format(minutes=max(1, minutes))


def parse_librivox(data, italian=True):
    books = []
    for item in (data or {}).get("books", []) if isinstance(data, dict) else []:
        language = item.get("language", "")
        if italian and language.lower() not in ("italian", "italiano"):
            continue
        rss = item.get("url_rss") or ""
        if not rss:
            continue
        authors = [" ".join(p for p in (a.get("first_name", ""), a.get("last_name", "")) if p).strip()
                   for a in item.get("authors", [])]
        books.append(Book("librivox", str(item.get("id", "")), " ".join((item.get("title") or "").split()),
                          [a for a in authors if a], language, rss, "audio", _hours(item.get("totaltime"))))
    return books


def search_audiobooks(words, italian=True, opener=urllib.request.urlopen):
    """By title, then by author when no title matches."""
    words = " ".join(words.split())
    found = []
    for key in ("title", "author"):
        params = {key: "^" + words, "format": "json", "limit": 100}
        try:
            found = parse_librivox(get_json(LIBRIVOX + "?" + urllib.parse.urlencode(params), opener), italian)
        except urllib.error.HTTPError as error:
            if error.code != 404:      # LibriVox answers 404 when nothing is found
                raise
            found = []
        if found:
            break
    return found[:LIMIT]


def liberliber_url(words):
    return LIBERLIBER.format(words=urllib.parse.quote_plus(" ".join(words.split())))


# -- getting them ------------------------------------------------------------

def books_folder():
    try:
        from gi.repository import GLib
        documents = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS)
    except Exception:  # noqa: BLE001
        documents = None
    return os.path.join(documents or os.path.expanduser("~"), "Libri")


def safe_name(text):
    name = re.sub(r"[^\w\s.,'-]", "", text, flags=re.UNICODE).strip()
    return re.sub(r"\s+", " ", name)[:80] or "libro"


def download(book, folder=None, opener=urllib.request.urlopen):
    """The book in Documents/Libri; returns its path."""
    folder = folder or books_folder()
    os.makedirs(folder, exist_ok=True)
    author = f" - {book.authors[0]}" if book.authors else ""
    path = os.path.join(folder, safe_name(book.title + author) + (".epub" if book.kind == "epub" else ".txt"))
    request = urllib.request.Request(book.url, headers={"User-Agent": USER_AGENT})
    with opener(request, timeout=60) as reply:
        data = reply.read()
    if not data:
        raise OSError("empty")
    with open(path + ".part", "wb") as f:
        f.write(data)
    os.replace(path + ".part", path)
    return path


def add_to_podcasts(book, store=None):
    """The audiobook in News and podcasts: its chapters are the episodes."""
    import vabaxos_news as news
    sources = [s for s in news.load(store) if s[1] != book.url]
    sources.append((book.title, book.url))
    news.save(sources, store)
