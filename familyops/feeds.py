"""Public ICS feeds Jacob supplies (data/feeds.yaml) -> Events, e.g. Ari's swim team calendars (Jacob, 2026-10-30)."""
from __future__ import annotations

import re
from datetime import date

import requests
import yaml

from . import ROOT, ics
from .model import Event

# "Red @BHHS", "Clinic @NHMS - Pre-Registration Required", "Quacktackular Meet @Birmingham Seaholm"
_AT = re.compile(r"^(?P<what>.*?)\s*@\s*(?P<where>.+?)(?:\s+[-–]\s+(?P<note>.+))?$")


def config() -> list[dict]:
    p = ROOT / "data/feeds.yaml"
    return (yaml.safe_load(p.read_text()) or {}).get("feeds") or [] if p.exists() else []


def fetch(url: str) -> str:
    r = requests.get(re.sub(r"^webcal://", "https://", url), timeout=30)
    r.raise_for_status()
    if "BEGIN:VCALENDAR" not in r.text:
        raise RuntimeError("feed response is not an ICS calendar")
    return r.text


def _names(text: str, word: str) -> bool:
    return re.search(rf"\b{re.escape(word)}\b", text, re.I) is not None


def to_events(feed: dict, occs: list[ics.IcsEvent]) -> list[Event]:
    out = []
    prefix, group = feed.get("prefix", ""), feed.get("group")
    for o in occs:
        summary = o.summary.strip()
        if group and not _names(summary, group) and any(_names(summary, g) for g in feed.get("other_groups") or []):
            continue                                   # another group's item on a club-wide calendar
        m = _AT.match(summary)
        what, where, note = (m["what"], m["where"].strip(), m["note"]) if m else (summary, None, None)
        what = what.strip(" -–:") or summary
        if feed.get("practice") and re.match(feed["practice"], what, re.I):
            kind = "practice"                          # "Red" -> "Swim practice"; "Red 1" -> "Swim practice (Red 1)"
            title = f"{prefix} practice".strip() + (f" ({what})" if " " in what else "")
        elif prefix and (no := re.match(r"^No Practices?\b\W*(?P<rest>.*)$", what, re.I)):
            kind = "event"                             # "No Practice - All Groups" -> "No swim practice (all groups)"
            rest = no["rest"].strip()
            title = f"No {prefix.lower()} practice" + (f" ({rest.lower()})" if rest else "")
        else:
            kind = "event"
            title = f"{prefix}: {what}" if prefix else what
        out.append(Event(
            date=o.day.isoformat(),
            start=None if o.all_day else o.start.strftime("%H:%M"),
            end=None if o.all_day or o.end is None else o.end.strftime("%H:%M"),
            title=title, kids=list(feed["kids"]), location=where or (o.location or None), kind=kind,
            details=note.strip() if note else None, sources=[feed["name"]],
        ))
    return out


def events(start: date, end: date, texts: dict[str, str] | None = None) -> list[Event]:
    """Every configured feed's events in [start, end]. `texts` (name -> ICS text) skips the download (tests)."""
    out = []
    for feed in config():
        text = texts[feed["name"]] if texts is not None else fetch(feed["url"])
        out += to_events(feed, ics.expand(ics.parse(text), start, end))
    return out
