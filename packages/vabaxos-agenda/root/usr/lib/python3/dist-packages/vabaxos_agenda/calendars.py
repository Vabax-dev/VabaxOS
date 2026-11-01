"""The calendars of GNOME, through Evolution Data Server: the computer's
own and those of the Online Accounts (Google, Microsoft 365 / Outlook).

    cals = Calendars()
    cals.names()                       [(uid, name)] of the enabled calendars
    cals.events(days)                  [Event], recurring ones expanded
    cals.add(event, uid=None)          in the chosen calendar, or the default one
    cals.remove(event)
"""

import datetime
import time

from . import Event


class Calendars:

    def __init__(self, registry=None):
        import gi
        gi.require_version("ECal", "2.0")
        gi.require_version("EDataServer", "1.2")
        gi.require_version("ICalGLib", "3.0")
        from gi.repository import ECal, EDataServer, ICalGLib
        self.ECal, self.EDS, self.ICal = ECal, EDataServer, ICalGLib
        self.registry = registry or EDataServer.SourceRegistry.new_sync(None)
        self.clients = {}

    def sources(self):
        return [s for s in self.registry.list_sources(self.EDS.SOURCE_EXTENSION_CALENDAR) if s.get_enabled()]

    def names(self):
        return [(s.get_uid(), s.get_display_name()) for s in self.sources()]

    def default_uid(self):
        source = self.registry.ref_default_calendar()
        return source.get_uid() if source else None

    def client(self, source):
        """A calendar's client. It waits at most one second for the
        backend to be online: an account offline gives its saved copy, and
        never keeps the list waiting (0 would wait for ever)."""
        uid = source.get_uid()
        if uid not in self.clients:
            self.clients[uid] = self.ECal.Client.connect_sync(source, self.ECal.ClientSourceType.EVENTS, 1, None)
        return self.clients[uid]

    def _datetime(self, itime, zone):
        if itime.is_date():
            return datetime.datetime(itime.get_year(), itime.get_month(), itime.get_day()).astimezone(), True
        utc = self.ICal.Timezone.get_utc_timezone()
        return datetime.datetime.fromtimestamp(itime.as_timet_with_zone(utc), datetime.timezone.utc).astimezone(), \
            False

    def events(self, days=14, now=None):
        start = int(now.timestamp() if now else time.time()) - 12 * 3600
        end = start + days * 86400 + 12 * 3600
        found = []
        for source in self.sources():
            try:
                client = self.client(source)
            except Exception:  # noqa: BLE001 - an account offline: the others count
                continue
            name = source.get_display_name()

            def collect(icomp, istart, iend, *_args, name=name, source=source):
                begin, all_day = self._datetime(istart, None)
                finish, _ = self._datetime(iend, None)
                found.append(Event(icomp.get_summary() or "", begin, finish, icomp.get_location() or "", name,
                                   all_day, icomp.get_uid() or "", source.get_uid()))
                return True
            try:
                client.generate_instances_sync(start, end, None, collect)
            except Exception:  # noqa: BLE001
                continue
        return sorted(found, key=lambda e: e.start)

    def _itime(self, moment):
        utc = self.ICal.Timezone.get_utc_timezone()
        return self.ICal.Time.new_from_timet_with_zone(int(moment.timestamp()), False, utc)

    def add(self, event, uid=None):
        uid = uid or self.default_uid()
        source = self.registry.ref_source(uid)
        comp = self.ICal.Component.new(self.ICal.ComponentKind.VEVENT_COMPONENT)
        comp.set_summary(event.title)
        if event.location:
            comp.set_location(event.location)
        comp.set_dtstart(self._itime(event.start))
        comp.set_dtend(self._itime(event.end))
        _ok, new_uid = self.client(source).create_object_sync(comp, self.ECal.OperationFlags.NONE, None)
        event.uid, event.source, event.calendar = new_uid, uid, source.get_display_name()
        return event

    def remove(self, event):
        source = self.registry.ref_source(event.source)
        self.client(source).remove_object_sync(event.uid, None, self.ECal.ObjModType.ALL,
                                               self.ECal.OperationFlags.NONE, None)
