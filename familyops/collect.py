"""Collect every scripted source into state/YYYY-MM-DD.json, and say which Claude-side sources are due."""
from __future__ import annotations

import json
import traceback
from datetime import date, datetime, timedelta, timezone

import yaml

from . import ROOT, almanac, announce, calendars, family, fantasy, feeds, lunch, mce, playmetrics, schedules, teams, weather
from .model import Event, conflicts, merge

STATE_DIR = ROOT / "state"
SRC_STATE = ROOT / "cache/sources.json"
WINDOW_DAYS = 10


def _src_state() -> dict:
    return json.loads(SRC_STATE.read_text()) if SRC_STATE.exists() else {}


def mark_checked(name: str, when: date) -> None:
    """Record a successful check of a source (Claude calls this for weekly/yearly checks it performed)."""
    s = _src_state()
    s[name] = when.isoformat()
    SRC_STATE.parent.mkdir(exist_ok=True)
    SRC_STATE.write_text(json.dumps(s, indent=1, sort_keys=True))


def due(today: date) -> list[dict]:
    """Non-daily sources that are stale and need Claude or Jacob."""
    reg = yaml.safe_load((ROOT / "sources.yaml").read_text())["sources"]
    st = _src_state()
    out = []
    for name, s in reg.items():
        if s["cadence"] == "daily" or s["fetch"] == "script":
            continue  # scripted sources refresh themselves inside collect()
        if s.get("pending"):
            out.append({"source": name, "who": s["fetch"], "what": s["what"], "why": "not supplied yet"})
            continue
        last = st.get(name)
        age = (today - date.fromisoformat(last)).days if last else None
        if s["cadence"] == "yearly":
            # School-year facts roll over in August; before that they are current by definition.
            sy = str(family.load().get("school_year", ""))
            start_year = today.year if today.month >= 8 else today.year - 1
            want = f"{start_year}-{str(start_year + 1)[2:]}"
            if sy != want and today.month in (7, 8, 9):
                out.append({"source": name, "who": s["fetch"], "what": s["what"],
                            "why": f"school year {want} has started; data is for {sy}"})
            continue
        if age is None or age >= s["max_age_days"]:
            out.append({"source": name, "who": s["fetch"], "what": s["what"],
                        "why": "never checked" if age is None else f"last checked {age} days ago"})
    return out


def collect(today: date) -> dict:
    end = today + timedelta(days=WINDOW_DAYS)
    meta = {"sources": {}, "warnings": []}
    groups: list[list[Event]] = []

    def run(name, fn):
        try:
            res = fn()
            meta["sources"][name] = {"ok": True, "count": len(res) if isinstance(res, list) else None}
            return res
        except Exception as e:  # noqa: BLE001 - every failure is reported, none is fatal
            meta["sources"][name] = {"ok": False, "error": f"{type(e).__name__}: {e}"}
            meta["warnings"].append(f"{name} failed: {e}")
            return [] if name not in ("lunch", "weather", "almanac", "fantasy", "playmetrics_feed", "mce_results") else None

    # Priority order matters for merge(): the richest source for an event goes first.
    pm_text = run("playmetrics_feed", playmetrics.fetch)
    pm_text = pm_text if isinstance(pm_text, str) else None
    groups.append(run("playmetrics", lambda: playmetrics.events(today, end, pm_text) if pm_text else []))
    back = today - timedelta(days=teams.LOOKBACK_DAYS)   # the team boxes show each kid's last game
    pm_past = run("playmetrics_past", lambda: playmetrics.events(back, today - timedelta(days=1), pm_text)) if pm_text else []
    groups.append(run("schedules", lambda: schedules.events(today, end)))
    groups.append(run("feeds", lambda: feeds.events(today, end)))        # data/feeds.yaml (Ari's swim calendars)
    sched_past = run("schedules_past", lambda: schedules.events(back, today - timedelta(days=1)))
    mce_scores = run("mce_results", lambda: mce.results_for(teams.SPARTANS, today))
    groups.append(run("district_calendar", lambda: calendars.bps_events(today, end)))
    events = merge([e for g in groups for e in g])

    lunch_today = run("lunch", lambda: lunch.for_day(today))
    if lunch_today and lunch_today.get("error"):
        meta["warnings"].append(f"lunch: {lunch_today['error']}")
    if today.day >= 24:  # quietly try to cache next month's menu once it is posted
        nxt = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
        try:
            lunch.month_menu(nxt.year, nxt.month)
        except Exception:  # noqa: BLE001 - not posted yet is normal
            pass
    wx = run("weather", lambda: weather.get(today))
    ff = run("fantasy", fantasy.get) if fantasy.config() else None
    alm = run("almanac", lambda: [almanac.day(today), almanac.day(today + timedelta(days=1))])

    return {
        "date": today.isoformat(),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "window": {"start": today.isoformat(), "end": end.isoformat()},
        "kids": {k: {"color": v["color"], "initial": v["initial"]} for k, v in family.kids().items()},
        "events": [e.to_dict() for e in events],
        "actions": [],
        "fyi": [],
        "conflicts": conflicts([e.to_dict() for e in events]),
        "lunch": lunch_today,
        "weather": wx,
        "mda": teams.section(teams.MDA, today, events, pm_past),              # Elle's 'MDA Kicks & Giggles' box, or None (hide)
        "spartans": teams.section(teams.SPARTANS, today, events, sched_past, mce_scores or {}),  # Ari's 'Spartans Hoop Scoop' box, or None (hide)
        "fantasy": ff,    # Ari's ESPN league summary, or None (not configured / failed: print nothing)
        "ari_fantasy": fantasy.box(ff, today),   # the newspaper's 'Ari's Fantasy Team' box, or None (hide)
        "almanac": alm,   # [today, tomorrow]: holidays, and Shabbat sunset on Fridays
        "announcements": announce.for_day(today.isoformat(), events),   # today's field trips -> the paper's special announcement band, or None
        "due": due(today),
        "delivery": {"email": None, "dashboard": None, "print": None, "filed": None},
        "meta": meta,
    }


def save(state: dict) -> str:
    STATE_DIR.mkdir(exist_ok=True)
    p = STATE_DIR / f"{state['date']}.json"
    p.write_text(json.dumps(state, indent=1, ensure_ascii=False))
    return str(p)


def add(state: dict, events: list[dict] = (), actions: list[dict] = (), fyi: list[dict] = ()) -> dict:
    """Merge Claude-collected items (Outlook calendars, email) into the state. Outlook events go after the
    scripted ones, so PlayMetrics and league schedules keep priority on duplicates."""
    have = [Event(**{k: v for k, v in e.items() if k != "id"}) for e in state["events"]]
    new = [Event(**{k: v for k, v in e.items() if k != "id"}) for e in events]
    state["events"] = [e.to_dict() for e in merge(have + new)]
    state["conflicts"] = conflicts(state["events"])
    state["actions"] += list(actions)
    state["fyi"] += list(fyi)
    return state
