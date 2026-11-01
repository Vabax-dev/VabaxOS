"""The agenda: the appointments of every calendar of the user, said as
sentences (Vabax, 2026-11-02: appointments read well by Orca, linked to
the reminders and to Google or Outlook).

The calendars are those of GNOME (Evolution Data Server): the computer's
own, and Google or Microsoft 365 / Outlook added in GNOME's Online
Accounts. GNOME Calendar shows the same appointments. Pure functions
here; calendars.py speaks to Evolution Data Server.

    describe(event, now)       'Tomorrow at 10:30, Dentist, one hour, Via Roma 3'
    group_by_day(events, now)  [(day label, [events])]
    from_sentence(text, now)   a new appointment from 'domani alle 10:30 dentista'
    due_announcements(...)     what to say 15 minutes before
"""

import datetime
import gettext
from dataclasses import dataclass

_translation = gettext.translation("vabaxos-agenda", fallback=True)
_ = _translation.gettext
ngettext = _translation.ngettext

NOTICE_MINUTES = 15


@dataclass
class Event:
    title: str
    start: datetime.datetime          # aware; for a whole day, midnight
    end: datetime.datetime
    location: str = ""
    calendar: str = ""
    all_day: bool = False
    uid: str = ""
    source: str = ""

    @property
    def key(self):
        return f"{self.source}/{self.uid}/{self.start.isoformat()}"


def weekday(date):
    return (_("Monday"), _("Tuesday"), _("Wednesday"), _("Thursday"), _("Friday"), _("Saturday"),
            _("Sunday"))[date.weekday()]


def month(date):
    return (_("January"), _("February"), _("March"), _("April"), _("May"), _("June"), _("July"), _("August"),
            _("September"), _("October"), _("November"), _("December"))[date.month - 1]


def day_label(date, today):
    """'Today', 'Tomorrow', 'Thursday', 'Friday 20 November': it starts a
    sentence, so with a capital letter also where weekdays have none."""
    label = _day_label(date, today)
    return label[:1].upper() + label[1:]


def _day_label(date, today):
    days = (date - today).days
    if days == 0:
        return _("Today")
    if days == 1:
        return _("Tomorrow")
    if days == 2:
        return _("The day after tomorrow")
    if 0 < days < 7:
        return weekday(date)
    return _("{weekday} {day} {month}").format(weekday=weekday(date), day=date.day, month=month(date))


def duration(event):
    minutes = round((event.end - event.start).total_seconds() / 60)
    if event.all_day or minutes <= 0:
        return ""
    hours, rest = divmod(minutes, 60)
    if hours and not rest:
        return ngettext("one hour", "{hours} hours", hours).format(hours=hours)
    if hours:
        return _("{hours} h {minutes} min").format(hours=hours, minutes=rest)
    return ngettext("one minute", "{minutes} minutes", rest).format(minutes=rest)


def describe(event, now, with_day=True):
    """'Tomorrow at 10:30, Dentist, one hour, Via Roma 3, Personal'."""
    local = event.start.astimezone(now.tzinfo) if event.start.tzinfo and now.tzinfo else event.start
    parts = []
    day = day_label(local.date(), now.date())
    if event.all_day:
        parts.append(f"{day}, " + _("all day") if with_day else _("All day"))
    else:
        time_text = local.strftime("%H:%M")
        parts.append(_("{day} at {time}").format(day=day, time=time_text) if with_day else time_text)
    parts.append(event.title or _("Untitled"))
    for extra in (duration(event), event.location, event.calendar):
        if extra:
            parts.append(extra)
    return ", ".join(parts)


def group_by_day(events, now):
    groups = []
    for event in sorted(events, key=lambda e: (e.start.astimezone(now.tzinfo).date() if e.start.tzinfo else
                                               e.start.date(), not e.all_day, e.start)):
        local = event.start.astimezone(now.tzinfo) if event.start.tzinfo and now.tzinfo else event.start
        label = day_label(local.date(), now.date())
        if not groups or groups[-1][0] != label:
            groups.append((label, []))
        groups[-1][1].append(event)
    return groups


def summary(events, now, days=2):
    """What Super+Alt+A says: today and tomorrow."""
    soon = [e for e in events if (e.start.astimezone(now.tzinfo).date() - now.date()).days < days
            and (e.end > now or e.all_day)]
    if not soon:
        return _("No appointments today and tomorrow.")
    count = ngettext("One appointment.", "{count} appointments.", len(soon)).format(count=len(soon))
    return count + " " + " ".join(describe(e, now) + "." for e in sorted(soon, key=lambda e: e.start))


def from_sentence(text, now, location=""):
    """A new Event from a sentence, as the reminders understand them
    ('domani alle 10:30 dentista'); None if no time is in it."""
    import vabaxos_reminders
    reminder = vabaxos_reminders.parse(text, now)
    if reminder is None or not reminder.text:
        return None
    start = reminder.when
    if start.tzinfo is None:
        start = start.astimezone()
    return Event(reminder.text, start, start + datetime.timedelta(hours=1), location)


def due_announcements(events, now, announced, minutes=NOTICE_MINUTES):
    """[(event, sentence)] for the appointments starting within minutes,
    not yet said; announced is the set of keys already said."""
    out = []
    for event in events:
        if event.all_day or event.key in announced:
            continue
        left = (event.start - now).total_seconds() / 60
        if 0 <= left <= minutes:
            announced.add(event.key)
            place = f", {event.location}" if event.location else ""
            if left < 1:
                out.append((event, _("Now: {title}{place}.").format(title=event.title, place=place)))
            else:
                out.append((event, ngettext("In one minute: {title}{place}.", "In {minutes} minutes: {title}{place}.",
                                            round(left)).format(minutes=round(left), title=event.title, place=place)))
    return out
