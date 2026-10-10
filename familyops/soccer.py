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


def place(loc: str | None) -> str:
    """'Spencer Park Field 2, 3701 John R Rd, Rochester Hills, MI 48307, USA' -> 'Spencer Park Field 2, Rochester Hills'.
    'Sandusky, OH, USA' -> 'Sandusky, OH'."""
    if not loc:
        return ""
    parts = [p.strip() for p in loc.split(",") if p.strip()]
    state_i = next((i for i, p in enumerate(parts) if len(p.split()[0]) == 2 and p.split()[0].isupper()), None)
    if state_i is None:
        return parts[0]
    city = parts[state_i - 1] if state_i >= 1 else ""
    if state_i == 1:                      # "City, ST, USA": a tournament town
        return f"{city}, {parts[state_i].split()[0]}"
    field = parts[0]
    return field if field == city else f"{field}, {city}"


TEAM = "MDA"


def _card(when: str, match: str, where: str = "", extra: str = "") -> str:
    """One schedule entry, styled by build2.py (.gm-*)."""
    out = f"<span class='gm-when'>{when}</span><span class='gm-match'>{match}</span>"
    if where:
        out += f"<span class='gm-loc'>{where}</span>"
    if extra:
        out += f"<span class='gm-extra'>{extra}</span>"
    return out


def section(today: date, events: list[Event], past_events: list[Event]) -> dict | None:
    """{'title', 'items'} ready for edition.json, or None when the box should not appear.
    Items read like a pro sports schedule: date · time, 'MDA vs Opponent', location, arrival + uniform."""
    res = results()
    items = []
    # 1. Last game(s): final score, and Elle's goals only when she scored.
    for d in recent_days(today):
        for g in [e for e in past_events if e.date == d.isoformat() and _is_game(e)]:
            opp = g.title.replace("Soccer game vs ", "").strip()
            r = res.get(g.date)
            if r:
                mda, them, opp = int(r["mda"]), int(r["opp"]), r.get("opponent", opp)
                a = f"<b>{TEAM} {mda}</b>" if mda > them else f"{TEAM} {mda}"
                b = f"<b>{opp} {them}</b>" if them > mda else f"{opp} {them}"
                extra = ""
                goals = int(r.get("elle_goals") or 0)
                if goals:
                    extra = f"<b>Elle scored {'a goal' if goals == 1 else f'{goals} goals'}!</b>"
                if r.get("notes"):
                    extra = (extra + " " + r["notes"]).strip()
                items.append(_card(f"Final · {_day(g.date)}", f"{a}, {b}", place(g.location), extra))
            else:
                items.append(_card(f"{_day(g.date)}", f"{TEAM} vs {opp}", place(g.location), "Final score coming soon."))
    # 2. Games and tournaments in the next 3 days.
    horizon = (today + timedelta(days=LOOKAHEAD_DAYS)).isoformat()
    upcoming = [e for e in events if today.isoformat() <= e.date <= horizon and "Elle" in e.kids
                and (_is_game(e) or _is_tournament(e))]
    tourneys: dict[str, list[Event]] = {}
    for e in upcoming:
        if _is_tournament(e):
            tourneys.setdefault(e.title, []).append(e)
            continue
        opp = e.title.replace("Soccer game vs ", "").strip()
        when = ("Today" if e.date == today.isoformat() else _day(e.date)) + f" · {fmt_time(e.start)}"
        extra = ""
        if e.details:                     # "arrive 7:30 am, black-black-black"
            arrive, _, uniform = e.details.partition(", ")
            extra = arrive[:1].upper() + arrive[1:] + (f" · Uniform: {uniform}" if uniform else "")
        items.append(_card(when, f"{TEAM} vs {opp}", place(e.location), extra))
    for title, evs in tourneys.items():
        first, last = evs[0].date, evs[-1].date
        span = _day(first) if first == last else f"{_day(first)}–{_day(last)}"
        items.append(_card(f"Tournament · {span}", title, place(evs[0].location)))
    if not items:
        return None
    return {"title": "MDA Kicks &amp; Giggles", "items": items}
