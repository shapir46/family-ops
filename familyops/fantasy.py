"""Ari's ESPN fantasy football league -> a small summary for the newspaper and dashboard.

Reads ESPN's league API (the JSON the ESPN Fantasy site itself uses). League and team ids live in
data/family.yaml (fantasy:). A league that is "viewable to public" needs nothing else; a private league needs
the ESPN login cookies, either as an environment network secret (header `Cookie: espn_s2=...; SWID={...}` for
lm-api-reads.fantasy.espn.com, never visible to sessions) or as env ESPN_S2 + ESPN_SWID. Secrets: never in the repo
or any output.
Unconfirmed = silent: on any failure the summary is omitted, never guessed.
"""
from __future__ import annotations

import os

import requests

from . import family

API = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{season}/segments/0/leagues/{league}"
VIEWS = ["mTeam", "mMatchupScore", "mSettings", "mStandings"]


def config() -> dict | None:
    f = family.load().get("fantasy") or {}
    return f if f.get("league_id") and f.get("team_id") else None


def fetch(cfg: dict) -> dict:
    cookies = {}
    if os.environ.get("ESPN_S2") and os.environ.get("ESPN_SWID"):
        cookies = {"espn_s2": os.environ["ESPN_S2"], "SWID": os.environ["ESPN_SWID"]}
    r = requests.get(API.format(season=cfg["season"], league=cfg["league_id"]),
                     params=[("view", v) for v in VIEWS], cookies=cookies, timeout=30,
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


def summarize(league: dict, team_id: int) -> dict:
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
        "this_week": None, "last_week": None,
    }
    for m in league.get("schedule", []):
        sides = [m.get("home", {}), m.get("away", {})]
        if team_id not in [s.get("teamId") for s in sides]:
            continue
        mine = next(s for s in sides if s.get("teamId") == team_id)
        opp = next((s for s in sides if s.get("teamId") != team_id), {})
        row = {"week": m.get("matchupPeriodId"), "opponent": _team_name(teams[opp["teamId"]]) if opp.get("teamId") in teams else "BYE",
               "score": _pts(mine), "opp_score": _pts(opp), "winner": m.get("winner")}
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
    return summarize(fetch(cfg), int(cfg["team_id"]))
