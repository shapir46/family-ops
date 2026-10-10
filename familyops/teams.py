"""Kids' team boxes for the newspaper, in a pro sports schedule format (Jacob, 2026-10-10).

- 'MDA Kicks & Giggles': Elle's soccer (MDA U9G Black). Games and tournaments come from the PlayMetrics feed.
- 'Spartans Hoop Scoop': Ari's basketball (Motor City Evolution Spartans). Games come from data/schedules/ari-mce-basketball-*.yaml.

Scores and the kid's goals/points come from data/results/<kid>-<team>-*.yaml, which Jacob supplies. A box is shown
only when there was a game since the last paper or a game/tournament within the next 3 days. A zero stat is never printed.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import yaml

from . import ROOT
from .model import Event, fmt_time

LOOKAHEAD_DAYS = 3


@dataclass(frozen=True)
class Team:
    key: str            # state / edition.json field
    title: str          # box heading (HTML)
    name: str           # our side of the matchup: "MDA vs Opponent"
    kid: str
    source: str         # Event.sources label the games come from
    game_prefix: str    # event title before the opponent's name
    results_glob: str   # data/results/<glob>
    score_key: str      # our score's key in the results file
    stat_key: str       # the kid's goals/points key
    stat_one: str       # "a goal"
    stat_many: str      # "{n} goals"
    arrive_uniform: bool = False   # details read "arrive 7:30 am, black-black-black"


MDA = Team(key="mda", title="MDA Kicks &amp; Giggles", name="MDA", kid="Elle", source="PlayMetrics",
           game_prefix="Soccer game vs ", results_glob="elle-mda-*.yaml", score_key="mda", stat_key="elle_goals",
           stat_one="a goal", stat_many="{n} goals", arrive_uniform=True)
SPARTANS = Team(key="spartans", title="Spartans Hoop Scoop", name="Spartans", kid="Ari", source="MCE league schedule",
                game_prefix="Basketball game vs ", results_glob="ari-spartans-*.yaml", score_key="spartans",
                stat_key="ari_points", stat_one="1 point", stat_many="{n} points")
TEAMS = [MDA, SPARTANS]


def results(team: Team) -> dict[str, dict]:
    out = {}
    for p in sorted((ROOT / "data/results").glob(team.results_glob)):
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


def _ours(team: Team, e: Event) -> bool:
    return team.source in e.sources and team.kid in e.kids


def _is_game(team: Team, e: Event) -> bool:
    return _ours(team, e) and e.kind == "game"


def _is_tournament(team: Team, e: Event) -> bool:
    # PlayMetrics: all-day entries (Kalahari Cup, Autumn Classic). League schedules: titles naming a tournament.
    return _ours(team, e) and e.kind == "event" and (e.start is None if team.source == "PlayMetrics" else "tournament" in e.title.lower())


def _clean(title: str) -> str:
    return title.replace(" (tentative)", "")


def _opponent(team: Team, e: Event) -> str | None:
    t = _clean(e.title)
    return t[len(team.game_prefix):].strip() if t.startswith(team.game_prefix) else None


def _matchup(team: Team, e: Event) -> str:
    """'MDA vs Opponent', or 'Spartans · Playoffs (if qualified)' when the opponent isn't known."""
    opp = _opponent(team, e)
    if opp:
        return f"{team.name} vs {opp}"
    what = _clean(e.title).split(" ", 1)[-1]          # "Basketball playoffs (if qualified)" -> "playoffs (if qualified)"
    return f"{team.name} · {what[:1].upper() + what[1:]}"


def _day(d: str) -> str:
    x = date.fromisoformat(d)
    return f"{x:%a} {x:%b} {x.day}"


def place(loc: str | None) -> str:
    """'Spencer Park Field 2, 3701 John R Rd, Rochester Hills, MI 48307, USA' -> 'Spencer Park Field 2, Rochester Hills'.
    'Sandusky, OH, USA' -> 'Sandusky, OH'. 'Berkshire Middle School, 21707 W 14 Mile Rd, Beverly Hills' ->
    'Berkshire Middle School, Beverly Hills'."""
    if not loc:
        return ""
    parts = [p.strip() for p in loc.split(",") if p.strip()]
    state_i = next((i for i, p in enumerate(parts) if len(p.split()[0]) == 2 and p.split()[0].isupper()), None)
    if state_i is None:                   # no state: "Place, street, City"
        return f"{parts[0]}, {parts[-1]}" if len(parts) >= 3 else parts[0]
    city = parts[state_i - 1] if state_i >= 1 else ""
    if state_i == 1:                      # "City, ST, USA": a tournament town
        return f"{city}, {parts[state_i].split()[0]}"
    field = parts[0]
    return field if field == city else f"{field}, {city}"


def _card(when: str, match: str, where: str = "", extra: str = "") -> str:
    """One schedule entry, styled by build2.py (.gm-*)."""
    out = f"<span class='gm-when'>{when}</span><span class='gm-match'>{match}</span>"
    if where:
        out += f"<span class='gm-loc'>{where}</span>"
    if extra:
        out += f"<span class='gm-extra'>{extra}</span>"
    return out


def _extra(team: Team, e: Event) -> str:
    if not e.details:
        return ""
    if team.arrive_uniform:               # "arrive 7:30 am, black-black-black"
        arrive, _, uniform = e.details.partition(", ")
        return arrive[:1].upper() + arrive[1:] + (f" · Uniform: {uniform}" if uniform else "")
    return e.details


def section(team: Team, today: date, events: list[Event], past_events: list[Event]) -> dict | None:
    """{'title', 'items'} ready for edition.json, or None when the box should not appear.
    Items read like a pro sports schedule: date · time, 'Team vs Opponent', location, extra line."""
    res = results(team)
    items = []
    # 1. Last game(s): final score, and the kid's goals/points only when nonzero.
    for d in recent_days(today):
        for g in [e for e in past_events if e.date == d.isoformat() and _is_game(team, e) and _opponent(team, e)]:
            opp = _opponent(team, g)
            r = res.get(g.date)
            if r:
                us, them, opp = int(r[team.score_key]), int(r["opp"]), r.get("opponent", opp)
                a = f"<b>{team.name} {us}</b>" if us > them else f"{team.name} {us}"
                b = f"<b>{opp} {them}</b>" if them > us else f"{opp} {them}"
                extra = ""
                n = int(r.get(team.stat_key) or 0)
                if n:
                    extra = f"<b>{team.kid} scored {team.stat_one if n == 1 else team.stat_many.format(n=n)}!</b>"
                if r.get("notes"):
                    extra = (extra + " " + r["notes"]).strip()
                items.append(_card(f"Final · {_day(g.date)}", f"{a}, {b}", place(g.location), extra))
            else:
                items.append(_card(_day(g.date), f"{team.name} vs {opp}", place(g.location), "Final score coming soon."))
    # 2. Games and tournaments in the next 3 days.
    horizon = (today + timedelta(days=LOOKAHEAD_DAYS)).isoformat()
    upcoming = [e for e in events if today.isoformat() <= e.date <= horizon and (_is_game(team, e) or _is_tournament(team, e))]
    tourneys: dict[str, list[Event]] = {}
    for e in upcoming:
        if _is_tournament(team, e):
            tourneys.setdefault(e.title, []).append(e)
            continue
        when = "Today" if e.date == today.isoformat() else _day(e.date)
        if e.start and "TBD" not in (e.details or ""):
            when += f" · {fmt_time(e.start)}"
        items.append(_card(when, _matchup(team, e), place(e.location), _extra(team, e)))
    for title, evs in tourneys.items():
        first, last = evs[0].date, evs[-1].end_date or evs[-1].date
        span = _day(first) if first == last else f"{_day(first)}–{_day(last)}"
        items.append(_card(f"Tournament · {span}", _clean(title), place(evs[0].location)))
    if not items:
        return None
    return {"title": team.title, "items": items}
