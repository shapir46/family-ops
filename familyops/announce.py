"""Special announcements for the newspaper (Jacob, 2026-10-21).

A kid's field trip today gets a "Field Trip Day!" band across the top of the paper. Trips are the day's events for a
family kid whose title says "field trip" (e.g. data/schedules/leo-kindergarten-montemurri-2026-27.yaml). The daily run
copies state.announcements into edition.json `announce` verbatim; build2.py draws the band.
"""
from __future__ import annotations

import re

from . import family
from .model import Event, fmt_time


def _span(start: str | None, end: str | None) -> str:
    """'12:15–2:15 pm', '9:30 am–1:00 pm', '10:00 am', or 'All day'."""
    if not start:
        return "All day"
    a, b = fmt_time(start), fmt_time(end) if end else ""
    if b and a[-2:] == b[-2:]:
        a = a[:-3]
    return f"{a}–{b}" if b else a


def _first_sentence(text: str | None) -> str:
    return re.split(r"(?<=[.!?])\s+", text.strip())[0] if text else ""


def for_day(today: str, events: list[Event]) -> list[dict] | None:
    """[{kind, kids, colors, title, when, where, tip}] for today's field trips, or None."""
    kids = family.kids()
    out = []
    for e in sorted(events, key=lambda e: e.start or ""):
        if e.date != today or "field trip" not in e.title.lower():
            continue
        who = [k for k in e.kids if k in kids]
        if not who:
            continue
        out.append({"kind": "field_trip", "kids": who, "colors": [kids[k]["color"] for k in who],
                    "title": e.title, "when": _span(e.start, e.end), "where": e.location or "",
                    "tip": _first_sentence(e.details)})
    return out or None
