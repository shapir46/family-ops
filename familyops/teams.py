"""Kids' team boxes for the newspaper, in a pro sports schedule format (Jacob, 2026-10-10).

- 'MDA Kicks & Giggles': Elle's soccer (MDA U9G Black). Games and tournaments come from the PlayMetrics feed.
- 'Spartans Hoop Scoop': Ari's basketball (Motor City Evolution Spartans). Games come from data/schedules/ari-mce-basketball-*.yaml.

Each box shows only the LAST game (score, or "Final score coming soon.") and the NEXT game or tournament. Scores and
the kid's goals/points come from data/results/<kid>-<team>-*.yaml, which Jacob supplies; Spartans scores are also read
from the MCE league results page (familyops/mce.py), and Jacob's file wins. A box is shown only when there was a game
since the last paper or the next game/tournament is within 3 days. A zero stat is never printed.
Tournament week (Jacob, 2026-10-19): when a tournament starts within the next 7 days, the box lists every day of it,
each game with its time, field, arrival and uniform, plus the trip's other days (data/schedules files with the team's
`trip_source` label, e.g. a Cedar Point day), until the tournament ends.
Spartans (Jacob, 2026-10-19): the box appears ONLY in the first paper after MCE posts the last game's score and recap
(usually by Thursday), with the recap under the final score and the next game. Before that, and after that paper, no box.
"""
from __future__ import annotations

import html
import json
from dataclasses import dataclass
from datetime import date, timedelta

import yaml

from . import ROOT
from .model import Event, fmt_time

LOOKAHEAD_DAYS = 3
TOURNAMENT_WEEK_DAYS = 7   # a tournament starting this soon gets its full day-by-day schedule in the box
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
    recap_only: bool = False       # shown only in the first paper after the league posts the score and recap
    trip_source: str = ""          # data/schedules label of a tournament trip's extra days (e.g. a Cedar Point visit)


MDA = Team(key="mda", title="MDA Kicks &amp; Giggles", name="MDA", kid="Elle", source="PlayMetrics",
           game_prefix="Soccer game vs ", results_glob="elle-mda-*.yaml", score_key="mda", stat_key="elle_goals",
           stat_one="a goal", stat_many="{n} goals", arrive_uniform=True, trip_source="MDA tournament trip")
SPARTANS = Team(key="spartans", title="Spartans Hoop Scoop", name="Spartans", kid="Ari", source="MCE league schedule",
                game_prefix="Basketball game vs ", results_glob="ari-spartans-*.yaml", score_key="spartans",
                stat_key="ari_points", stat_one="1 point", stat_many="{n} points", recap_only=True)
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
    if team.arrive_uniform:               # "arrive 7:30 am, black-black-black" ("arrive 8:30 am edt, tbd" at tournaments)
        arrive, _, uniform = e.details.partition(", ")
        arrive = arrive.replace(" edt", "").replace(" est", "")
        return arrive[:1].upper() + arrive[1:] + (f" · Uniform: {uniform}" if uniform and uniform.lower() != "tbd" else "")
    return e.details


def _recap_printed(team: Team, game_date: str, today: date) -> bool:
    """True when an earlier paper (state/<day>.json after the game, before today; Sundays have no paper) already
    printed this game's recap."""
    final = f"Final · {_day(game_date)}"
    for p in sorted((ROOT / "state").glob("*.json")):
        d = p.stem
        if not (game_date < d < today.isoformat()) or date.fromisoformat(d).weekday() == 6:
            continue
        box = (json.loads(p.read_text()) or {}).get(team.key) or {}
        if any(final in i and "gm-recap" in i for i in box.get("items") or []):
            return True
    return False


RESULT_WAIT_DAYS = 8   # after this, a game with no posted score stops saying "coming soon"


def section(team: Team, today: date, events: list[Event], past_events: list[Event],
            posted: dict[str, dict] | None = None) -> dict | None:
    """{'title', 'items'} ready for edition.json, or None when the box should not appear.
    Exactly two cards at most (Jacob, 2026-10-10): the LAST game and the NEXT game or tournament.
    The box appears only when a game was played since the last paper or the next one is within 3 days; a
    `recap_only` team's box appears only in the first paper after its last game's score and recap are posted.
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
    week = _tournament_week(team, today, events, tourneys)
    recent = {d.isoformat() for d in recent_days(today)}
    horizon = (today + timedelta(days=LOOKAHEAD_DAYS)).isoformat()
    r_last = res.get(last.date) if last else None
    recap = ""
    if team.recap_only:
        recap = (r_last or {}).get("recap", "") if r_last and team.score_key in r_last else ""
        if not recap or _recap_printed(team, last.date, today):
            return None
    elif not ((last and last.date in recent) or (nxt and nxt[0][0] <= horizon) or week):
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
    if week:
        items += week
    elif nxt:
        items.append(nxt[0][2])
    return {"title": team.title, "items": items}


def _tournament_week(team: Team, today: date, events: list[Event], tourneys: dict[str, list[Event]]) -> list[str]:
    """Tournament card + one card per remaining game or trip day, when a tournament starts within the next 7 days
    (or is under way); [] otherwise."""
    t = today.isoformat()
    soon = (today + timedelta(days=TOURNAMENT_WEEK_DAYS - 1)).isoformat()
    for title, evs in sorted(tourneys.items(), key=lambda kv: kv[1][0].date):
        first, last_day = evs[0].date, evs[-1].end_date or evs[-1].date
        if not (first <= soon and last_day >= t):
            continue
        span = _day(first) if first == last_day else f"{_day(first)}–{_day(last_day)}"
        cards = [_card(f"Tournament · {span}", _clean(title), place(evs[0].location))]
        days = [e for e in events if t <= e.date <= last_day and first <= e.date and
                (_is_game(team, e) or (team.trip_source and team.trip_source in e.sources and team.kid in e.kids))]
        for e in sorted(days, key=lambda e: (e.date, e.start or "")):
            when = ("Today" if e.date == t else _day(e.date)) + (f" · {fmt_time(e.start)}" if e.start else " · All day")
            if _is_game(team, e):
                cards.append(_card(when, _matchup(team, e), place(e.location), _extra(team, e)))
            else:
                cards.append(_card(when, _clean(e.title).replace(" (all day)", ""), place(e.location)))
        return cards
    return []
