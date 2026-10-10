"""The day's state: one structured record that every output renders from."""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from typing import Optional


def _norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


@dataclass
class Event:
    date: str                      # YYYY-MM-DD (America/Detroit)
    title: str
    kids: list[str] = field(default_factory=list)
    start: Optional[str] = None    # HH:MM 24h, None = all day
    end: Optional[str] = None
    end_date: Optional[str] = None # multi-day spans
    location: Optional[str] = None
    kind: str = "event"            # event | school_status | religious_school | deadline | game | practice
    details: Optional[str] = None
    sources: list[str] = field(default_factory=list)
    status: Optional[str] = None   # for school_status: half_day | no_school | recess | ...

    @property
    def all_day(self) -> bool:
        return self.start is None

    def key(self) -> str:
        """Dedupe key: same day, same start time, same normalized title."""
        return f"{self.date}|{self.start or 'allday'}|{_norm_title(self.title)[:40]}"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["id"] = self.key()
        return d


def weekday_label(d: str | date) -> str:
    """'Tue, Oct 13' for a YYYY-MM-DD string or date."""
    if isinstance(d, str):
        d = date.fromisoformat(d)
    return f"{d:%a}, {d:%b} {d.day}"


def fmt_time(hhmm: Optional[str]) -> str:
    """'18:00' -> '6:00 pm'."""
    if not hhmm:
        return "All day"
    t = datetime.strptime(hhmm, "%H:%M")
    return f"{t.hour % 12 or 12}:{t:%M} {'am' if t.hour < 12 else 'pm'}"


def _same(a: Event, b: Event) -> bool:
    """Same event from two sources: same dedupe key (and no conflicting children), or same day + same start time + a shared child."""
    kids_ok = not a.kids or not b.kids or bool(set(a.kids) & set(b.kids))
    if a.key() == b.key():
        return kids_ok
    return (a.date == b.date and a.start is not None and a.start == b.start and bool(a.kids) and bool(b.kids)
            and kids_ok and a.kind != "school_status" and b.kind != "school_status")


def merge(events: list[Event]) -> list[Event]:
    """Merge duplicates (see _same); the first source's fields win, sources and kids are unioned.
    Pass sources in priority order (e.g. PlayMetrics before Outlook for soccer)."""
    out: list[Event] = []
    for e in events:
        m = next((x for x in out if _same(x, e)), None)
        if m is None:
            out.append(e)
            continue
        for s in e.sources:
            if s not in m.sources:
                m.sources.append(s)
        for kid in e.kids:
            if kid not in m.kids:
                m.kids.append(kid)
        for attr in ("location", "details", "end"):
            if not getattr(m, attr) and getattr(e, attr):
                setattr(m, attr, getattr(e, attr))
    return sorted(out, key=lambda e: (e.date, e.start or "00:00", e.title))


def _minutes(hhmm: str) -> int:
    h, m = map(int, hhmm.split(":"))
    return h * 60 + m


def _arrive(e: dict) -> Optional[int]:
    """'arrive 11:30 am' in details -> minutes; the child must be there by then."""
    m = re.search(r"arrive (\d{1,2}):(\d{2})\s*(am|pm)", e.get("details") or "", re.I)
    if not m:
        return None
    h = int(m.group(1)) % 12 + (12 if m.group(3).lower() == "pm" else 0)
    return h * 60 + int(m.group(2))


def conflicts(events: list[dict]) -> list[dict]:
    """Same child, same day, overlapping times (arrival time counts as the start). Untimed events are ignored;
    an event with no end is treated as 60 minutes."""
    out = []
    timed = [e for e in events if e.get("start") and e.get("kids") and e.get("kind") != "school_status"]
    for i, a in enumerate(timed):
        for b in timed[i + 1:]:
            if a["date"] != b["date"]:
                continue
            shared = sorted(set(a["kids"]) & set(b["kids"]))
            if not shared:
                continue
            spans = []
            for e in (a, b):
                s = min(_minutes(e["start"]), _arrive(e) or 10 ** 6)
                end = _minutes(e["end"]) if e.get("end") else _minutes(e["start"]) + 60
                spans.append((s, end))
            if spans[0][0] < spans[1][1] and spans[1][0] < spans[0][1]:
                out.append({"date": a["date"], "kids": shared, "a": a["title"], "b": b["title"],
                            "a_time": a["start"], "b_time": b["start"]})
    return out
