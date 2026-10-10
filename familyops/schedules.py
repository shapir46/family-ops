"""Activity schedules Jacob supplies (data/schedules/*.yaml)."""
from __future__ import annotations

from datetime import date

import yaml

from . import ROOT
from .model import Event


def events(start: date, end: date) -> list[Event]:
    out = []
    for path in sorted((ROOT / "data/schedules").glob("*.yaml")):
        s = yaml.safe_load(path.read_text())
        for e in s["events"]:
            first = e["date"]
            last = e.get("end_date", first)
            if last < start or first > end:
                continue
            title = e["title"] + (" (tentative)" if e.get("tentative") and "(if" not in e["title"] else "")
            out.append(Event(
                date=max(first, start).isoformat(), end_date=last.isoformat() if last != first else None,
                start=e.get("start"), end=e.get("end"), title=title, kids=list(s["kids"]),
                location=e.get("location", s.get("location")), kind=e.get("kind", "event"),
                details=e.get("details"), sources=[s["source_label"]],
            ))
    return out
