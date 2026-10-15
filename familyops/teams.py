"""Kids' team boxes for the newspaper, in a pro sports schedule format (Jacob, 2026-10-10).

- 'MDA Kicks & Giggles': Elle's soccer (MDA U9G Black). Games and tournaments come from the PlayMetrics feed.
- 'Spartans Hoop Scoop': Ari's basketball (Motor City Evolution Spartans). Games come from data/schedules/ari-mce-basketball-*.yaml.

Each box shows only the LAST game (score, or "Final score coming soon.") and the NEXT game or tournament. Scores and
the kid's goals/points come from data/results/<kid>-<team>-*.yaml, which Jacob supplies; Spartans scores are also read
from the MCE league results page (familyops/mce.py), and Jacob's file wins. A box is shown only when there was a game
since the last paper or the next game/tournament is within 3 days. A zero stat is never printed.
Fridays: the Spartans box also prints the league's recap under the last game's final score, and appears whenever that
game was in the past week (MCE posts scores and recaps by Thursday; Jacob, 2026-10-15).
"""
from __future__ import annotations

import html
from dataclasses import dataclass
from datetime import date, timedelta

import yaml

from . import ROOT
from .model import Event, fmt_time

LOOKAHEAD_DAYS = 3
RECAP_WEEKDAY = 4     # Friday: the paper prints the posted recap of the past week's game
LOOKBACK_DAYS = 28   # how far back collect looks for each kid's last game


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


def _card(when: str, match: str, where: str = "", extra: str = "", recap: str = "") -> str:
    """One schedule entry, styled by build2.py (.gm-*)."""
    out = f"<span class='gm-when'>{when}</span><span class='gm-match'>{match}</span>"
    if where:
        out += f"<span class='gm-loc'>{where}</span>"
    if extra:
        out += f"<span class='gm-extra'>{extra}</span>"
    if recap:
        out += f"<span class='gm-recap'>{html.escape(recap, quote=False)}</span>"
    return out


def _extra(team: Team, e: Event) -> str:
    if not e.details:
        return ""
    if team.arrive_uniform:               # "arrive 7:30 am, black-black-black"
        arrive, _, uniform = e.details.partition(", ")
        return arrive[:1].upper() + arrive[1:] + (f" · Uniform: {uniform}" if uniform else "")
    return e.details


RESULT_WAIT_DAYS = 8   # after this, a game with no posted score stops saying "coming soon"


def section(team: Team, today: date, events: list[Event], past_events: list[Event],
            posted: dict[str, dict] | None = None) -> dict | None:
    """{'title', 'items'} ready for edition.json, or None when the box should not appear.
    Exactly two cards at most (Jacob, 2026-10-10): the LAST game and the NEXT game or tournament.
    The box appears only when a game was played since the last paper or the next one is within 3 days.
    `posted`: scores found online (MCE results page); Jacob's data/results file wins over them."""
    res = {**(posted or {})}
    for d, r in results(team).items():
        res[d] = {**res.get(d, {}), **r}
    t = today.isoformat()
    past = sorted((e for e in past_events if e.date < t and _is_game(team, e) and _opponent(team, e)),
                  key=lambda e: (e.date, e.start or ""))
    last = past[-1] if past else None
    tourneys: dict[str, list[Event]] = {}
    nxt: list[tuple[str, str, str]] = []           # (date, start, card)
    for e in events:
        if e.date < t:
            continue
        if _is_tournament(team, e):
            tourneys.setdefault(e.title, []).append(e)
        elif _is_game(team, e):
            when = "Today" if e.date == t else _day(e.date)
            if e.start and "TBD" not in (e.details or ""):
                when += f" · {fmt_time(e.start)}"
            nxt.append((e.date, e.start or "", _card(when, _matchup(team, e), place(e.location), _extra(team, e))))
    for title, evs in tourneys.items():
        first, last_day = evs[0].date, evs[-1].end_date or evs[-1].date
        span = _day(first) if first == last_day else f"{_day(first)}–{_day(last_day)}"
        nxt.append((first, "", _card(f"Tournament · {span}", _clean(title), place(evs[0].location))))
    nxt.sort(key=lambda x: (x[0], x[1]))
    recent = {d.isoformat() for d in recent_days(today)}
    horizon = (today + timedelta(days=LOOKAHEAD_DAYS)).isoformat()
    friday = today.weekday() == RECAP_WEEKDAY and last and (today - date.fromisoformat(last.date)).days <= 7
    r_last = res.get(last.date) if last else None
    recap = (r_last or {}).get("recap", "") if friday and r_last and team.score_key in r_last else ""
    if not ((last and last.date in recent) or (nxt and nxt[0][0] <= horizon) or recap):
        return None
    items = []
    if last:
        opp, r = _opponent(team, last), res.get(last.date)
        if r and team.score_key in r:
            us, them, opp = int(r[team.score_key]), int(r["opp"]), r.get("opponent", opp)
            a = f"<b>{team.name} {us}</b>" if us > them else f"{team.name} {us}"
            b = f"<b>{opp} {them}</b>" if them > us else f"{opp} {them}"
            n = int(r.get(team.stat_key) or 0)
            extra = f"<b>{team.kid} scored {team.stat_one if n == 1 else team.stat_many.format(n=n)}!</b>" if n else ""
            if r.get("notes"):
                extra = (extra + " " + r["notes"]).strip()
            items.append(_card(f"Final · {_day(last.date)}", f"{a}, {b}", place(last.location), extra, recap))
        else:
            fresh = (today - date.fromisoformat(last.date)).days <= RESULT_WAIT_DAYS
            items.append(_card(f"Last game · {_day(last.date)}", f"{team.name} vs {opp}", place(last.location),
                               "Final score coming soon." if fresh else ""))
    if nxt:
        items.append(nxt[0][2])
    return {"title": team.title, "items": items}
