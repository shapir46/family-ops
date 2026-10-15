"""Ari's ESPN fantasy football league -> a small summary for the newspaper and dashboard, plus the newspaper's
"Ari's Fantasy Team" box (box(): Fri, the Saturday Weekend Edition, Mon and Tue only; Jacob, 2026-10-15).

Reads ESPN's league API (the JSON the ESPN Fantasy site itself uses). League and team ids live in
data/family.yaml (fantasy:). A league that is "viewable to public" needs nothing else; a private league needs
the ESPN login cookies, either as an environment network secret (header `Cookie: espn_s2=...; SWID={...}` for
lm-api-reads.fantasy.espn.com, never visible to sessions) or as env ESPN_S2 + ESPN_SWID. Secrets: never in the repo
or any output.
Unconfirmed = silent: on any failure the summary is omitted, never guessed.
"""
from __future__ import annotations

import os
from datetime import date

import requests

from . import family

API = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{season}/segments/0/leagues/{league}"
VIEWS = ["mTeam", "mMatchupScore", "mSettings", "mStandings", "mBoxscore"]   # mBoxscore: starters' points
BOX_VIEWS = ["mMatchupScore", "mBoxscore"]   # one earlier week's box score (scoringPeriodId)
POS = {1: "QB", 2: "RB", 3: "WR", 4: "TE", 5: "K", 16: "D/ST"}
NOT_STARTING = {20, 21}   # ESPN lineup slots: bench, IR


def config() -> dict | None:
    f = family.load().get("fantasy") or {}
    return f if f.get("league_id") and f.get("team_id") else None


def fetch(cfg: dict, period: int | None = None) -> dict:
    """The league, with the current week's box score; with `period`, only that week's matchups and box score."""
    cookies = {}
    if os.environ.get("ESPN_S2") and os.environ.get("ESPN_SWID"):
        cookies = {"espn_s2": os.environ["ESPN_S2"], "SWID": os.environ["ESPN_SWID"]}
    params = [("view", v) for v in (BOX_VIEWS if period else VIEWS)] + ([("scoringPeriodId", period)] if period else [])
    r = requests.get(API.format(season=cfg["season"], league=cfg["league_id"]),
                     params=params, cookies=cookies, timeout=30,
                     headers={"User-Agent": "family-ops"})
    if r.status_code == 401:
        raise PermissionError("ESPN league is private: make it viewable to public, or add the ESPN cookies "
                              "(network secret 'Cookie' for lm-api-reads.fantasy.espn.com, or env ESPN_S2/ESPN_SWID)")
    r.raise_for_status()
    return r.json()


def _team_name(t: dict) -> str:
    return (t.get("name") or f"{t.get('location', '')} {t.get('nickname', '')}").strip() or t.get("abbrev", "?")


def _pts(side: dict) -> float | None:
    for k in ("totalPointsLive", "totalPoints"):
        if side.get(k) is not None:
            return round(float(side[k]), 1)
    return None


def _proj(side: dict) -> float | None:
    v = side.get("totalProjectedPointsLive")
    return round(float(v), 1) if v is not None else None


def _top(side: dict, week: int) -> dict | None:
    """The side's highest-scoring starter that week (bench and IR don't count), or None without a box score."""
    best = None
    for e in (side.get("rosterForCurrentScoringPeriod") or {}).get("entries") or []:
        if e.get("lineupSlotId") in NOT_STARTING:
            continue
        player = (e.get("playerPoolEntry") or {}).get("player") or {}
        pts = next((st.get("appliedTotal") for st in player.get("stats") or []
                    if st.get("statSourceId") == 0 and st.get("scoringPeriodId") == week), None)
        if pts is None or not player.get("fullName"):
            continue
        if best is None or pts > best["pts"]:
            best = {"name": player["fullName"], "pos": POS.get(player.get("defaultPositionId")), "pts": round(float(pts), 1)}
    return best


def summarize(league: dict, team_id: int, prev: dict | None = None) -> dict:
    """`prev`: the league fetched for last week's scoring period, for last week's top players."""
    teams = {t["id"]: t for t in league["teams"]}
    me = teams[team_id]
    week = league.get("status", {}).get("currentMatchupPeriod") or league.get("scoringPeriodId")
    rec = me.get("record", {}).get("overall", {})
    # Standings: playoff seed if ESPN provides it, else by wins then points for.
    ordered = sorted(league["teams"], key=lambda t: (-t.get("record", {}).get("overall", {}).get("wins", 0),
                                                    -t.get("record", {}).get("overall", {}).get("pointsFor", 0)))
    rank = me.get("playoffSeed") or next(i for i, t in enumerate(ordered, 1) if t["id"] == team_id)
    out = {
        "league": league.get("settings", {}).get("name"),
        "team": _team_name(me),
        "record": f"{rec.get('wins', 0)}-{rec.get('losses', 0)}" + (f"-{rec['ties']}" if rec.get("ties") else ""),
        "rank": rank, "teams": len(teams), "week": week,
        "points_for": round(rec.get("pointsFor", 0), 1),
        "active": league.get("status", {}).get("isActive", True),
        "latest_period": league.get("status", {}).get("latestScoringPeriod"),
        "this_week": None, "last_week": None,
    }
    prev_boxes = {m.get("matchupPeriodId"): m for m in (prev or {}).get("schedule", [])
                  if team_id in (m.get("home", {}).get("teamId"), m.get("away", {}).get("teamId"))}
    for m in league.get("schedule", []):
        sides = [m.get("home", {}), m.get("away", {})]
        if team_id not in [s.get("teamId") for s in sides]:
            continue
        mine = next(s for s in sides if s.get("teamId") == team_id)
        opp = next((s for s in sides if s.get("teamId") != team_id), {})
        row = {"week": m.get("matchupPeriodId"), "opponent": _team_name(teams[opp["teamId"]]) if opp.get("teamId") in teams else "BYE",
               "score": _pts(mine), "opp_score": _pts(opp), "winner": m.get("winner")}
        if row["week"] in (week, (week or 0) - 1):
            box = m if row["week"] == week else prev_boxes.get(row["week"], {})
            bmine = next((s for s in (box.get("home", {}), box.get("away", {})) if s.get("teamId") == team_id), {})
            bopp = next((s for s in (box.get("home", {}), box.get("away", {})) if s.get("teamId") not in (None, team_id)), {})
            row.update(proj=_proj(mine), opp_proj=_proj(opp), top=_top(bmine, row["week"]), opp_top=_top(bopp, row["week"]))
        if row["week"] == week:
            out["this_week"] = row
        elif week and row["week"] == week - 1:
            row["result"] = ("W" if (m.get("winner") == "HOME") == (m.get("home", {}).get("teamId") == team_id) else "L") \
                if m.get("winner") in ("HOME", "AWAY") else "T"
            out["last_week"] = row
    return out


def get() -> dict | None:
    cfg = config()
    if not cfg:
        return None
    league = fetch(cfg)
    week = league.get("status", {}).get("currentMatchupPeriod") or league.get("scoringPeriodId")
    try:   # last week's box score only adds its top players; the summary stands without it
        prev = fetch(cfg, week - 1) if week and week > 1 else None
    except Exception:  # noqa: BLE001
        prev = None
    return summarize(league, int(cfg["team_id"]), prev)


# --- The newspaper box (Jacob, 2026-10-12) ---------------------------------------------------------------------
SHOW_DAYS = {0, 1, 4, 5}   # Mon, Tue, Fri, Sat (Weekend Edition, covers Sunday); hidden Wed and Thu, and there is no Sunday paper
TOP_DAYS = {0, 1}          # Mon and Tue also show each team's top performer


def _n(x: float | None) -> str:
    return f"{x:.1f}"


def _ordinal(n: int) -> str:
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def _scored(row: dict | None) -> bool:
    return bool(row) and bool(row.get("score") or row.get("opp_score"))


def _final(row: dict) -> bool:
    return row.get("winner") in ("HOME", "AWAY", "TIE")


def _player(p: dict) -> str:
    pos = f", {p['pos']}" if p.get("pos") and p["pos"] != "D/ST" else ""
    return f"<b>{p['name']}</b>{pos}, {_n(p['pts'])} pts"


def box(s: dict | None, today: date) -> dict | None:
    """The 'Ari's Fantasy Team' box, {title, items}, or None (hide it). During the NFL (fantasy) season only, on
    Fri/Sat/Mon/Tue: the current matchup with its score and projected score; Mon and Tue add each team's top
    performer. Tuesday shows the week just played, even after ESPN has moved on to the next week."""
    if not s or not s.get("active") or today.weekday() not in SHOW_DAYS:
        return None
    row = s.get("this_week")
    if today.weekday() == 1 and not _scored(row):
        row = s.get("last_week")
        if row and s.get("latest_period") and s["latest_period"] > row["week"] + 1:
            row = None   # an old week (season over): print nothing
    elif row and _final(row):
        row = None       # Mon/Thu/Sat with the current week already final: the season is over
    if not row or row.get("score") is None or row.get("opp_score") is None:
        return None
    me, them = row["score"], row["opp_score"]
    items = [f"{s['record'].replace('-', '–')}, {_ordinal(s['rank'])} of {s['teams']}",
             f"<b>Week {row['week']}</b> vs {row['opponent']}"]
    if _final(row):
        res = "W" if me > them else "L" if me < them else "T"
        items.append(f"Final: <b>{res} {_n(me)}–{_n(them)}</b>")
    else:
        state = "no games yet" if not (me or them) else "leading" if me > them else "trailing" if me < them else "tied"
        items.append(f"Score: <b>{_n(me)}–{_n(them)}</b>, {state}")
        if row.get("proj") is not None and row.get("opp_proj") is not None and (row["proj"], row["opp_proj"]) != (me, them):
            items.append(f"Projected: {_n(row['proj'])}–{_n(row['opp_proj'])}")
    if today.weekday() in TOP_DAYS:
        if row.get("top") and row["top"]["pts"] > 0:
            items.append("Ari&#8217;s top player: " + _player(row["top"]))
        if row.get("opp_top") and row["opp_top"]["pts"] > 0:
            items.append("Their top player: " + _player(row["opp_top"]))
    return {"title": f"Ari&#8217;s Fantasy Team: {s['team']}", "items": items}
