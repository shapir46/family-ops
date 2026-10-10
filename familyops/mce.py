"""Motor City Evolution league results page -> game scores for Ari's Spartans box (Jacob, 2026-10-10).

MCE posts the previous weekend's scores and short recaps at the page in data/schedules/ari-mce-basketball-*.yaml
(`results_url`). The page groups games under headings like "ROOKIE LEAGUE: SEPTEMBER 28:" and writes each game as
"Spartans 21, Crush 2" followed by a recap paragraph. Other divisions have teams with the same names (the Rookie League
also has Spartans), so a game counts only when it is under Ari's division heading (`division`, e.g. "College") and its
date AND both team names match a game on Ari's schedule. Two matches the same day without a way to tell them apart are
skipped.
Ari's points are read from the recap only when it names him in full ("Ari Shapiro ... six points").
Unconfirmed = silent: anything that doesn't parse is skipped, never guessed.
"""
from __future__ import annotations

import html as htmllib
import re
from datetime import date

import requests

MONTHS = ["JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST", "SEPTEMBER", "OCTOBER",
          "NOVEMBER", "DECEMBER"]
HEADING = re.compile(r"^(?P<league>[A-Z][A-Z0-9 &'/.-]*?)\s*:\s*(?:[A-Z]+DAY,?\s+)?(?P<month>" + "|".join(MONTHS)
                     + r")\.?\s+(?P<day>\d{1,2})(?:ST|ND|RD|TH)?\s*:?\s*$")
GAME = re.compile(r"^(?P<a>[A-Za-z][\w .'&/-]*?)\s+(?P<sa>\d{1,3})\s*,\s*(?P<b>[A-Za-z][\w .'&/-]*?)\s+(?P<sb>\d{1,3})\s*:?\s*$")
WORDS = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve thirteen "
                                     "fourteen fifteen sixteen seventeen eighteen nineteen twenty".split())}
WORDS.update({"twenty-" + w: 20 + i for w, i in list(WORDS.items())[1:10]})
NUM = r"(\d{1,2}|" + "|".join(sorted(WORDS, key=len, reverse=True)) + r")"
# "six of his eight points" -> 8 (his total); "all six of his points" -> 6; "eight points", "(12pts)".
POINTS = re.compile(NUM + r" of (?:his|her) " + NUM + r" (?:points|pts)\b|" + NUM + r"\s*(?:of (?:his|her) )?(?:points|pts)\b", re.I)


def _lines(page: str) -> list[str]:
    t = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", page)
    t = re.sub(r"(?i)<br\s*/?>|</?(p|div|span|h\d|li|section)\b[^>]*>", "\n", t)
    t = htmllib.unescape(re.sub(r"<[^>]+>", " ", t)).replace("​", " ").replace("\xa0", " ")
    return [ln.strip() for ln in (re.sub(r"[ \t]+", " ", x) for x in t.split("\n")) if ln.strip()]


def _year(month: int, day: int, today: date) -> date:
    """Headings have no year: take the most recent such date that isn't more than a few days in the future."""
    for y in (today.year, today.year - 1):
        try:
            d = date(y, month, day)
        except ValueError:
            continue
        if (d - today).days <= 3:
            return d
    return date(today.year - 1, month, day)


def parse(page: str, today: date) -> list[dict]:
    """[{league, date, a, sa, b, sb, recap}] in page order."""
    games, league, when, cur = [], None, None, None
    for ln in _lines(page):
        h = HEADING.match(ln) if ln == ln.upper() else None
        if h:
            league = h["league"].strip().title()
            when = _year(MONTHS.index(h["month"]) + 1, int(h["day"]), today)
            cur = None
            continue
        g = GAME.match(ln)
        if g and when:
            cur = {"league": league, "date": when.isoformat(), "a": g["a"].strip(), "sa": int(g["sa"]),
                   "b": g["b"].strip(), "sb": int(g["sb"]), "recap": ""}
            games.append(cur)
            continue
        if cur is not None and ln != ":":
            cur["recap"] = (cur["recap"] + " " + ln.lstrip(": ")).strip()
    return games


def player_points(recap: str, player: str) -> int | None:
    """Points for `player` (full name) when the recap states them in the same sentence, else None."""
    for sentence in re.split(r"(?<=[.!?])\s+", recap):
        i = sentence.find(player)
        if i < 0:
            continue
        rest = sentence[i + len(player):]
        rest = re.split(r"\b(?:while|and|but|as|whereas)\b(?= [A-Z])", rest)[0]   # stop at the next player's clause
        m = POINTS.search(rest)
        if m:
            n = (m.group(2) or m.group(3)).lower()
            return int(n) if n.isdigit() else WORDS.get(n)
    return None


def results(cfg: dict, schedule: list[dict], today: date, page: str | None = None) -> dict[str, dict]:
    """{date: {team_key: ours, 'opp': theirs, 'opponent', '<stat_key>'?, 'source'}} for games on Ari's schedule.
    cfg = the schedule file's results block: {url, team, division, player} plus score_key, stat_key."""
    if page is None:
        page = requests.get(cfg["url"], timeout=30, headers={"User-Agent": "Mozilla/5.0 family-ops"}).text
    team = cfg["team"]
    wanted = {}
    for e in schedule:
        t = e.get("title", "")
        if e.get("kind") == "game" and " vs " in t:
            wanted[str(e["date"])] = t.split(" vs ", 1)[1].replace(" (tentative)", "").strip().lower()
    division = (cfg.get("division") or "").lower()
    found: dict[str, list[dict]] = {}
    for g in parse(page, today):
        opp = wanted.get(g["date"])
        if not opp or (division and division not in (g["league"] or "").lower()):
            continue
        if g["a"].lower() == team.lower() and g["b"].lower() == opp:
            us, them, opp_name = g["sa"], g["sb"], g["b"]
        elif g["b"].lower() == team.lower() and g["a"].lower() == opp:
            us, them, opp_name = g["sb"], g["sa"], g["a"]
        else:
            continue
        r = {cfg["score_key"]: us, "opp": them, "opponent": opp_name, "source": "MCE league results"}
        pts = player_points(g["recap"], cfg["player"]) if cfg.get("player") else None
        if pts is not None:
            r[cfg["stat_key"]] = pts
        found.setdefault(g["date"], []).append(r)
    out = {}
    for d, rs in found.items():
        named = [r for r in rs if cfg["stat_key"] in r]
        if len(rs) == 1 or len(named) == 1:      # two same-name games that day: keep only the one whose recap names Ari
            out[d] = rs[0] if len(rs) == 1 else named[0]
    return out


def results_for(team, today: date) -> dict[str, dict]:
    """Scores for `team` (teams.SPARTANS) from the results page named in its league schedule file(s)."""
    import yaml
    from . import ROOT
    out = {}
    for path in sorted((ROOT / "data/schedules").glob("ari-mce-basketball-*.yaml")):
        s = yaml.safe_load(path.read_text())
        cfg = s.get("results")
        if cfg and cfg.get("url"):
            out.update(results({**cfg, "score_key": team.score_key, "stat_key": team.stat_key}, s["events"], today))
    return out
