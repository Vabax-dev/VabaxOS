"""News and podcasts (vabaxos-news): RSS and Atom feeds, read and played.

A source is a feed address; a web site's address works too, since its
page names its feeds (<link rel="alternate">). Items have a title, a date,
a summary, a link and, for podcasts, the audio of the episode.

Pure functions here, tested without the network (tests/news).
"""

import datetime
import email.utils
import gettext
import html
import html.parser
import json
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


def _(text):
    return gettext.dgettext("vabaxos-news", text)


SUGGESTIONS = [
    ("ANSA", "https://www.ansa.it/sito/ansait_rss.xml"),
    ("Il Post", "https://www.ilpost.it/feed/"),
]
ATOM = "{http://www.w3.org/2005/Atom}"
USER_AGENT = "VabaxOS-news/1.0 (+https://github.com/Vabax-dev/VabaxOS)"


class Item:
    def __init__(self, title, link="", summary="", date=None, audio=""):
        self.title = title
        self.link = link
        self.summary = summary
        self.date = date
        self.audio = audio

    def describe(self):
        when = self.date.strftime("%d/%m/%Y %H:%M") if self.date else ""
        kind = _("podcast") if self.audio else ""
        return ", ".join(p for p in (when, kind) if p)


def plain(text):
    """HTML of a summary as plain text."""
    text = re.sub(r"<(br|/p|/div|/li)[^>]*>", "\n", text or "", flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    return "\n".join(" ".join(line.split()) for line in text.splitlines() if line.strip())


def _date(text):
    text = (text or "").strip()
    if not text:
        return None
    try:
        return email.utils.parsedate_to_datetime(text)
    except (TypeError, ValueError):
        pass
    try:
        return datetime.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def parse_feed(data):
    """(title, [Item]) of an RSS 2.0 or Atom feed; ValueError if it is not one."""
    try:
        root = ET.fromstring(data)
    except ET.ParseError as error:
        raise ValueError("not a feed") from error
    if root.tag == "rss" or root.find("channel") is not None:
        channel = root.find("channel")
        items = []
        for node in channel.findall("item"):
            enclosure = node.find("enclosure")
            audio = enclosure.get("url", "") if enclosure is not None and \
                (enclosure.get("type", "").startswith("audio") or enclosure.get("url", "").endswith(
                    (".mp3", ".m4a", ".ogg", ".opus"))) else ""
            items.append(Item(" ".join((node.findtext("title") or "").split()), (node.findtext("link") or "").strip(),
                              plain(node.findtext("description") or ""), _date(node.findtext("pubDate")), audio))
        return " ".join((channel.findtext("title") or "").split()), items
    if root.tag == ATOM + "feed":
        items = []
        for node in root.findall(ATOM + "entry"):
            link, audio = "", ""
            for anchor in node.findall(ATOM + "link"):
                rel = anchor.get("rel", "alternate")
                if rel == "alternate" and not link:
                    link = anchor.get("href", "")
                elif rel == "enclosure" and anchor.get("type", "").startswith("audio"):
                    audio = anchor.get("href", "")
            summary = node.findtext(ATOM + "summary") or node.findtext(ATOM + "content") or ""
            items.append(Item(" ".join((node.findtext(ATOM + "title") or "").split()), link, plain(summary),
                              _date(node.findtext(ATOM + "updated") or node.findtext(ATOM + "published")), audio))
        return " ".join((root.findtext(ATOM + "title") or "").split()), items
    raise ValueError("not a feed")


class _Links(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.feeds = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "link" and "alternate" in (attrs.get("rel") or "").lower() and \
                (attrs.get("type") or "").lower() in ("application/rss+xml", "application/atom+xml"):
            self.feeds.append(attrs.get("href", ""))


def discover(page, base):
    """The feed addresses a web page names."""
    parser = _Links()
    parser.feed(page)
    return [urllib.parse.urljoin(base, href) for href in parser.feeds if href]


def normalize_address(text):
    text = text.strip()
    if text and "://" not in text:
        text = "https://" + text
    return text


def _get(url, opener):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with opener(request, timeout=30) as reply:
        return reply.read()


def fetch(address, opener=urllib.request.urlopen):
    """(feed address, title, items) of a feed, or of the first feed a web
    page names."""
    url = normalize_address(address)
    data = _get(url, opener)
    try:
        title, items = parse_feed(data)
        return url, title, items
    except ValueError:
        pass
    feeds = discover(data.decode("utf-8", "replace"), url)
    if not feeds:
        raise ValueError(_("no news feed at this address"))
    title, items = parse_feed(_get(feeds[0], opener))
    return feeds[0], title, items


def store_path():
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "vabaxos", "news.json")


def load(path=None):
    try:
        with open(path or store_path(), encoding="utf-8") as f:
            data = json.load(f)
        return [(s["title"], s["url"]) for s in data if s.get("url")]
    except (OSError, ValueError, KeyError, TypeError):
        return []


def save(sources, path=None):
    path = path or store_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump([{"title": t, "url": u} for t, u in sources], f, indent=1, ensure_ascii=False)
