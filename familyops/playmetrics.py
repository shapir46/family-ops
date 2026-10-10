"""PlayMetrics team feed (Elle, MDA U9G Black) -> Events. The feed URL is a credential: env PLAYMETRICS_ICS_URL only."""
from __future__ import annotations

import os
import re
from datetime import date

import requests

from . import ics
from .model import Event

SOURCE = "PlayMetrics"
KID = "Elle"
_CRED = re.compile(r"https?://|passcode|pwd=|meeting id", re.I)


def fetch() -> str:
    url = os.environ.get("PLAYMETRICS_ICS_URL")
    if not url:
        raise RuntimeError("PLAYMETRICS_ICS_URL is not set")
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    if "BEGIN:VCALENDAR" not in r.text:
        raise RuntimeError("PlayMetrics response is not an ICS calendar")
    return r.text


def _game_details(desc: str) -> dict:
    lines = [l.strip() for l in desc.split("\n") if l.strip()]
    d = {}
    for l in lines:
        if m := re.match(r"(.+?) at (.+)$", l):
            home, away = m.group(2), m.group(1)
            if "U9G BLACK" in home.upper():
                d["opponent"], d["home"] = away, True
            elif "U9G BLACK" in away.upper():
                d["opponent"], d["home"] = home, False
        elif m := re.match(r"Arrive by (.+)$", l, re.I):
            d["arrive"] = m.group(1).strip().lower().replace(" ", " ")
        elif m := re.match(r"Uniform:\s*(.+)$", l, re.I):
            d["uniform"] = m.group(1).strip()
    if lines and not _CRED.search(lines[-1]) and not lines[-1].lower().startswith(("please", "arrive", "uniform")) \
            and " at " not in lines[-1]:
        d["field"] = lines[-1]
    return d


def to_events(occs: list[ics.IcsEvent]) -> list[Event]:
    out = []
    for o in occs:
        title = re.sub(r"^(CANCELED\s+)?U9G BLACK\s*-\s*", "", o.summary).strip()
        loc = o.location if not _CRED.search(o.location or "") else ("Zoom" if "zoom" in o.location.lower() else None)
        kind, details = "event", None
        if title == "Game":
            g = _game_details(o.description)
            kind = "game"
            title = "Soccer game" + (f" vs {g['opponent']}" if g.get("opponent") else "")
            bits = [f"arrive {g['arrive']}" if g.get("arrive") else None,
                    g.get("uniform", "").lower().replace(" ", "-") or None]
            details = ", ".join(b for b in bits if b) or None
            if g.get("field"):
                loc = g["field"] + (f", {loc}" if loc else "")
        elif title == "Practice":
            kind, title = "practice", "Soccer practice"
            f = [l for l in o.description.split("\n") if l.strip() and not _CRED.search(l)]
            if f:
                loc = f[-1].strip() + (f", {loc}" if loc else "")
        out.append(Event(
            date=o.day.isoformat(),
            start=None if o.all_day else o.start.strftime("%H:%M"),
            end=None if o.all_day or o.end is None else o.end.strftime("%H:%M"),
            title=title, kids=[KID], location=loc, kind=kind, details=details, sources=[SOURCE],
        ))
    return out


def events(start: date, end: date, text: str | None = None) -> list[Event]:
    return to_events(ics.expand(ics.parse(text if text is not None else fetch()), start, end))
