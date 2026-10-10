"""Static yearly calendars (BPS district) queried by date window. Temple Israel Sunday School: calendar pending from Jacob."""
from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache

import yaml

from . import ROOT, family
from .model import Event

CAL_DIR = ROOT / "data/calendars"


@lru_cache
def _load(name: str) -> dict:
    return yaml.safe_load((CAL_DIR / name).read_text())


def _days(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def _as_date(v) -> date:
    return v if isinstance(v, date) else date.fromisoformat(str(v))


def bps_events(start: date, end: date, cal: str = "bps-2026-27.yaml") -> list[Event]:
    """One school_status Event per affected day in [start, end]."""
    c = _load(cal)
    out = []
    for e in c["entries"]:
        first = _as_date(e["date"])
        last = _as_date(e.get("end", e["date"]))
        is_half = e["kind"] == "half_day" or e.get("half_day", False)
        kids = family.kids_for(e["audience"], half_day=is_half)
        if not kids:
            continue
        for d in _days(max(first, start), min(last, end)):
            if d.weekday() >= 5 and e["kind"] == "recess":
                continue  # recess spans include weekends; they need no line
            out.append(Event(
                date=d.isoformat(), title=e["label"], kids=kids, kind="school_status",
                status="half_day" if is_half else e["kind"], sources=[c["source_label"]],
            ))
    return out


def school_status(d: date) -> list[Event]:
    """Lead-the-day facts for one date: district status."""
    return bps_events(d, d)
