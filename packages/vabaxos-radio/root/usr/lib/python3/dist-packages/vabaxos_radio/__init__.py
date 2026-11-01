"""Radio over the Internet: the stations of Radio Browser (radio-browser.info,
a free catalog without accounts, used by many programs), searched by name
or kind, Italian first, and the favourites of the user.

    top(country)              the most listened stations of a country
    search(words, country)    by name, then by kind (jazz, news...)
    clicked(station)          tells the catalog a station was played
    load(), save()            the favourites
"""

import gettext
import json
import os
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field

_ = gettext.translation("vabaxos-radio", fallback=True).gettext

# all.api.radio-browser.info answers from one of the servers of the
# catalog; the others are tried when it does not answer.
SERVERS = ("all.api.radio-browser.info", "de1.api.radio-browser.info", "de2.api.radio-browser.info",
           "fi1.api.radio-browser.info")
USER_AGENT = "VabaxOS-Radio/1.0 (+https://github.com/Vabax-dev/VabaxOS)"
LIMIT = 60


@dataclass
class Station:
    uuid: str
    name: str
    url: str
    country: str = ""
    countrycode: str = ""
    tags: list = field(default_factory=list)
    codec: str = ""
    bitrate: int = 0
    homepage: str = ""

    def describe(self):
        """'Radio Deejay, Italia, pop e dance, 128 kilobit'."""
        parts = [self.name]
        if self.country:
            parts.append(self.country)
        if self.tags:
            parts.append(_(" and ").join(self.tags[:2]))
        if self.bitrate:
            parts.append(_("{rate} kilobit").format(rate=self.bitrate))
        return ", ".join(parts)


def parse(data):
    """Stations from the catalog's JSON list; broken and nameless ones left
    out, each stream once."""
    stations, seen = [], set()
    for item in data or []:
        url = (item.get("url_resolved") or item.get("url") or "").strip()
        name = " ".join((item.get("name") or "").split())
        if not url or not name or item.get("lastcheckok") == 0 or url in seen:
            continue
        seen.add(url)
        tags = [t.strip() for t in (item.get("tags") or "").split(",") if t.strip()][:4]
        try:
            bitrate = int(item.get("bitrate") or 0)
        except (TypeError, ValueError):
            bitrate = 0
        stations.append(Station(item.get("stationuuid", ""), name, url, item.get("country", ""),
                                item.get("countrycode", ""), tags, item.get("codec", ""), bitrate,
                                item.get("homepage", "")))
    return stations


def api(path, params=None, opener=urllib.request.urlopen, servers=SERVERS):
    query = "?" + urllib.parse.urlencode(params) if params else ""
    last = None
    for server in servers:
        request = urllib.request.Request(f"https://{server}{path}{query}", headers={"User-Agent": USER_AGENT})
        try:
            with opener(request, timeout=15) as reply:
                return json.load(reply)
        except Exception as error:  # noqa: BLE001 - the next server
            last = error
    raise ConnectionError(str(last))


def top(country="IT", opener=urllib.request.urlopen, limit=LIMIT):
    params = {"limit": limit, "hidebroken": "true", "order": "clickcount", "reverse": "true"}
    if country:
        params["countrycode"] = country
    return parse(api("/json/stations/search", params, opener))


def search(words, country="IT", opener=urllib.request.urlopen, limit=LIMIT):
    """By name; when nothing is found, by kind (the tags of the stations)."""
    words = " ".join(words.split())
    if not words:
        return top(country, opener, limit)
    base = {"limit": limit, "hidebroken": "true", "order": "clickcount", "reverse": "true"}
    if country:
        base["countrycode"] = country
    found = parse(api("/json/stations/search", dict(base, name=words), opener))
    if not found:
        found = parse(api("/json/stations/search", dict(base, tag=words.lower()), opener))
    return found


def clicked(station, opener=urllib.request.urlopen):
    """The catalog counts the listens (as its rules ask); never in the way."""
    try:
        api(f"/json/url/{urllib.parse.quote(station.uuid)}", None, opener)
    except Exception:  # noqa: BLE001
        pass


def favourites_path():
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "vabaxos", "radio.json")


def load(path=None):
    try:
        with open(path or favourites_path(), encoding="utf-8") as f:
            return [Station(**item) for item in json.load(f)]
    except (OSError, ValueError, TypeError):
        return []


def save(stations, path=None):
    path = path or favourites_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump([asdict(s) for s in stations], f, ensure_ascii=False, indent=1)
