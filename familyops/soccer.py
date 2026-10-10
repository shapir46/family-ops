"""'MDA Kicks & Giggles': Elle's soccer box for the newspaper (Jacob, 2026-10-10).

Upcoming games/tournaments come from the PlayMetrics feed; scores and Elle's goals come from
data/results/elle-mda-*.yaml, which Jacob supplies. Shown only when there was a game since the last paper
or a game/tournament within the next 3 days. A goal count of 0 is never printed.
"""
from __future__ import annotations

from datetime import date, timedelta

import yaml

from . import ROOT
from .model import Event, fmt_time

LOOKAHEAD_DAYS = 3


def results() -> dict[str, dict]:
    out = {}
    for p in sorted((ROOT / "data/results").glob("elle-mda-*.yaml")):
        for r in (yaml.safe_load(p.read_text()) or {}).get("results") or []:
            out[str(r["date"])] = r
    return out


def recent_days(today: date) -> list[date]:
    """Days whose games the paper hasn't reported yet: yesterday; on Monday also Saturday
    (Saturday's paper prints before Saturday's games, and there is no Sunday paper)."""
    days = [today - timedelta(days=1)]
    if today.weekday() == 0:
        days.insert(0, today - timedelta(days=2))
    return days


def _is_game(e: Event) -> bool:
    return e.kind == "game"


def _is_tournament(e: Event) -> bool:
    return e.kind == "event" and e.start is None   # all-day PlayMetrics entries (Kalahari Cup, Autumn Classic)


def _day(d: str) -> str:
    x = date.fromisoformat(d)
    return f"{x:%a} {x:%b} {x.day}"


def section(today: date, events: list[Event], past_events: list[Event]) -> dict | None:
    """{'title', 'items'} ready for edition.json, or None when the box should not appear."""
    res = results()
    items = []
    # 1. Last game(s): score, and Elle's goals only when she scored.
    for d in recent_days(today):
        for g in [e for e in past_events if e.date == d.isoformat() and _is_game(e)]:
            opp = g.title.replace("Soccer game vs ", "").strip()
            r = res.get(g.date)
            if r:
                mda, them = int(r["mda"]), int(r["opp"])
                word = "won" if mda > them else "lost" if mda < them else "tied"
                line = f"<b>{_day(g.date)}:</b> MDA {word} {mda}–{them} vs {r.get('opponent', opp)}"
                goals = int(r.get("elle_goals") or 0)
                if goals:
                    line += f". <b>Elle scored {'a goal' if goals == 1 else f'{goals} goals'}!</b>"
                if r.get("notes"):
                    line += f" {r['notes']}"
            else:
                line = f"<b>{_day(g.date)}:</b> MDA played {opp}. Final score coming soon."
            items.append(line)
    # 2. Games and tournaments in the next 3 days.
    horizon = (today + timedelta(days=LOOKAHEAD_DAYS)).isoformat()
    upcoming = [e for e in events if today.isoformat() <= e.date <= horizon and "Elle" in e.kids
                and (_is_game(e) or _is_tournament(e))]
    seen_tourneys = {}
    for e in upcoming:
        if _is_tournament(e):
            seen_tourneys.setdefault(e.title, []).append(e)
            continue
        opp = e.title.replace("Soccer game vs ", "").strip()
        when = "Today" if e.date == today.isoformat() else _day(e.date)
        bits = [f"<b>{when}, {fmt_time(e.start)}:</b> vs {opp}"]
        if e.details:
            bits.append(e.details)            # "arrive 7:30 am, black-black-black"
        if e.location:
            bits.append(e.location.split(",")[0])
        items.append(" · ".join(bits))
    for title, evs in seen_tourneys.items():
        first, last = evs[0].date, evs[-1].date
        span = _day(first) if first == last else f"{_day(first)}–{date.fromisoformat(last):%a}"
        place = (evs[0].location or "").split(",")[0]
        items.append(f"<b>{span}:</b> {title}" + (f" in {place}" if place else ""))
    if not items:
        return None
    return {"title": "MDA Kicks &amp; Giggles", "items": items}
