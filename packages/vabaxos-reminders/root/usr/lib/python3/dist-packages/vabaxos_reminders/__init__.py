"""Reminders and alarms said aloud (vabaxos-reminders): a sentence as one
would say it becomes a time and a text, in Italian or English.

    "alle 15 chiama Marco"              today at 15:00 (tomorrow if past)
    "tra 10 minuti scola la pasta"      in ten minutes
    "domani alle 7.30 sveglia"          tomorrow at 7:30, an alarm
    "lunedì alle 9 dentista"            next Monday at 9:00
    "ogni giorno alle 8 medicine"       every day at 8:00
    "remind me at 6 pm to call Anna"    English too

Pure functions, tested without a clock (tests/reminders).
"""

import datetime
import gettext
import json
import os
import re
import uuid


def _(text):
    return gettext.dgettext("vabaxos-reminders", text)


WEEKDAYS = {
    "lunedì": 0, "lunedi": 0, "martedì": 1, "martedi": 1, "mercoledì": 2, "mercoledi": 2,
    "giovedì": 3, "giovedi": 3, "venerdì": 4, "venerdi": 4, "sabato": 5, "domenica": 6,
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6,
}
NUMBERS = {"un": 1, "uno": 1, "una": 1, "due": 2, "tre": 3, "quattro": 4, "cinque": 5, "sei": 6, "sette": 7,
           "otto": 8, "nove": 9, "dieci": 10, "quindici": 15, "venti": 20, "trenta": 30, "mezz'ora": 30,
           "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "five": 5, "ten": 10, "fifteen": 15,
           "twenty": 20, "thirty": 30}
ALARM_WORDS = ("sveglia", "svegliami", "alarm", "wake me")

_IN = re.compile(r"\b(?:tra|fra|in)\s+(\d+|[a-zà']+)\s+(minuti|minuto|min|ore|ora|minutes|minute|hours|hour)\b", re.I)
_HALF_HOUR = re.compile(r"\b(?:tra|fra|in)\s+(?:mezz'ora|mezzora|half an hour)\b", re.I)
_AT = re.compile(r"\b(?:alle|all'|alla|ore|at)\s*(\d{1,2})(?:[:.](\d{2}))?\s*(am|pm|di sera|del pomeriggio|"
                 r"di mattina|del mattino)?", re.I)
_DAY = re.compile(r"\b(oggi|domani|dopodomani|today|tomorrow|ogni giorno|tutti i giorni|every day|"
                  r"(?:next\s+)?(?:" + "|".join(WEEKDAYS) + r"))\b", re.I)
_FILLER = re.compile(r"^\s*(?:ricordami|ricorda|promemoria|remind me|reminder)\s*(?:di|che|to|that)?\s*|"
                     r"^\s*(?:di|to)\s+|\s*(?:di|to)\s*$", re.I)


class Reminder:
    def __init__(self, when, text, alarm=False, daily=False, ident=None):
        self.when = when
        self.text = text
        self.alarm = alarm
        self.daily = daily
        self.ident = ident or uuid.uuid4().hex[:12]

    def to_json(self):
        return {"when": self.when.isoformat(timespec="minutes"), "text": self.text, "alarm": self.alarm,
                "daily": self.daily, "id": self.ident}

    @classmethod
    def from_json(cls, data):
        return cls(datetime.datetime.fromisoformat(data["when"]), data.get("text", ""),
                   bool(data.get("alarm")), bool(data.get("daily")), data.get("id"))

    def describe(self, now):
        """'Today at 15:00: call Marco' (and 'every day', 'alarm')."""
        time_text = self.when.strftime("%H:%M")
        if self.daily:
            when = _("Every day at {time}").format(time=time_text)
        elif self.when.date() == now.date():
            when = _("Today at {time}").format(time=time_text)
        elif self.when.date() == now.date() + datetime.timedelta(days=1):
            when = _("Tomorrow at {time}").format(time=time_text)
        else:
            when = _("{date} at {time}").format(date=self.when.strftime("%d/%m/%Y"), time=time_text)
        kind = _("alarm") if self.alarm else ""
        text = self.text or kind or _("reminder")
        return f"{when}: {text}" + (f" ({kind})" if kind and self.text else "")


def _number(word):
    word = word.lower()
    if word.isdigit():
        return int(word)
    return NUMBERS.get(word)


def parse(sentence, now):
    """A Reminder from a sentence, or None if no time is in it."""
    text = " " + sentence.strip() + " "
    lower = text.lower()
    alarm = any(word in lower for word in ALARM_WORDS)
    when = None
    daily = False

    match = _HALF_HOUR.search(text)
    if match:
        when = now + datetime.timedelta(minutes=30)
        text = text[:match.start()] + " " + text[match.end():]
    else:
        match = _IN.search(text)
        if match and _number(match.group(1)) is not None:
            amount = _number(match.group(1))
            unit = match.group(2).lower()
            minutes = amount * 60 if unit.startswith(("or", "hour")) else amount
            when = now + datetime.timedelta(minutes=minutes)
            text = text[:match.start()] + " " + text[match.end():]

    if when is None:
        day_offset = None
        weekday = None
        match = _DAY.search(text)
        if match:
            word = match.group(1).lower().replace("next ", "")
            if word in ("domani", "tomorrow"):
                day_offset = 1
            elif word == "dopodomani":
                day_offset = 2
            elif word in ("oggi", "today"):
                day_offset = 0
            elif word in ("ogni giorno", "tutti i giorni", "every day"):
                daily = True
            else:
                weekday = WEEKDAYS[word]
            text = text[:match.start()] + " " + text[match.end():]
        match = _AT.search(text)
        if not match:
            return None
        hour, minute = int(match.group(1)), int(match.group(2) or 0)
        part = (match.group(3) or "").lower()
        if part in ("pm", "di sera", "del pomeriggio") and hour < 12:
            hour += 12
        if part == "am" and hour == 12:
            hour = 0
        if hour > 23 or minute > 59:
            return None
        text = text[:match.start()] + " " + text[match.end():]
        when = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if day_offset is not None:
            when += datetime.timedelta(days=day_offset)
        elif weekday is not None:
            days = (weekday - now.weekday()) % 7 or 7
            when += datetime.timedelta(days=days)
        elif when <= now:
            when += datetime.timedelta(days=1)

    text = re.sub(r"\s+", " ", text).strip(" ,.")
    for _round in range(3):
        text = _FILLER.sub("", text).strip(" ,.")
    if alarm and text.lower() in ALARM_WORDS:
        text = ""
    return Reminder(when.replace(second=0, microsecond=0), text[:1].upper() + text[1:], alarm, daily)


def due(reminders, now):
    """The reminders whose time has come."""
    return [r for r in reminders if r.when <= now]


def after_firing(reminder):
    """None when it is done, or the same reminder tomorrow (every day)."""
    if not reminder.daily:
        return None
    reminder.when += datetime.timedelta(days=1)
    return reminder


def store_path():
    base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return os.path.join(base, "vabaxos", "reminders.json")


def load(path=None):
    path = path or store_path()
    try:
        with open(path, encoding="utf-8") as f:
            return [Reminder.from_json(item) for item in json.load(f)]
    except (OSError, ValueError, KeyError, TypeError):
        return []


def save(reminders, path=None):
    path = path or store_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump([r.to_json() for r in sorted(reminders, key=lambda r: r.when)], f, indent=1,
                  ensure_ascii=False)
    os.replace(tmp, path)
