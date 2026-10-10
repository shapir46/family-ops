"""The YAML calendars must match the prose originals they were transcribed from."""
import re
from datetime import date

import yaml

from familyops import ROOT, calendars

PROSE = {
    "bps-2026-27.yaml": ROOT / "data/bps-calendar-2026-27.md",
    "tbe-rs-2026-27.yaml": ROOT / "data/tbe-religious-school-2026-27.md",
}
DAY = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}


def prose_starts(path):
    """(weekday, month, day) of the first date in every '- **Ddd, Mon D' bullet."""
    out = []
    for m in re.finditer(r"^- \*\*(\w{3})(?:-\w{3})?, (\w{3}) (\d+)", path.read_text(), re.M):
        out.append((m.group(1), m.group(2), int(m.group(3))))
    return out


def test_yaml_dates_match_prose_weekdays():
    for cal, prose in PROSE.items():
        entries = yaml.safe_load((calendars.CAL_DIR / cal).read_text())["entries"]
        yaml_starts = sorted({(e["date"].strftime("%b"), e["date"].day): e["date"] for e in entries}.items(),
                             key=lambda kv: kv[1])
        prose = prose_starts(prose)
        prose_keys = {(mon, d) for _, mon, d in prose}
        assert {k for k, _ in yaml_starts} == prose_keys, cal
        for wd, mon, d in prose:
            dt = dict(yaml_starts)[(mon, d)]
            assert dt.weekday() == DAY[wd], f"{cal}: {wd} {mon} {d} is really {dt:%a}"


def test_half_day_skips_lila_closure_includes_her():
    half = calendars.bps_events(date(2026, 10, 13), date(2026, 10, 13))
    assert half[0].status == "half_day" and "Lila" not in half[0].kids and "Leo" in half[0].kids
    closed = calendars.bps_events(date(2026, 11, 3), date(2026, 11, 3))
    assert closed[0].status == "no_school" and "Lila" in closed[0].kids


def test_jk_k_half_day_is_leo_only():
    ev = calendars.bps_events(date(2026, 9, 2), date(2026, 9, 3))
    assert len(ev) == 2 and all(e.kids == ["Leo"] for e in ev)


def test_recess_weekdays_only():
    ev = calendars.bps_events(date(2026, 12, 23), date(2027, 1, 1))
    assert [e.date for e in ev] == ["2026-12-23", "2026-12-24", "2026-12-25", "2026-12-28",
                                    "2026-12-29", "2026-12-30", "2026-12-31", "2027-01-01"]


def test_religious_school_sunday_and_no_school_sunday():
    s = calendars.tbe_events(date(2026, 10, 18), date(2026, 10, 18))
    assert s[0].kind == "religious_school" and s[0].start == "09:30" and "Ruach" not in s[0].details
    s = calendars.tbe_events(date(2026, 10, 25), date(2026, 10, 25))
    assert "Ruach Singers" in s[0].details
    n = calendars.tbe_events(date(2026, 11, 29), date(2026, 11, 29))
    assert n[0].status == "no_religious_school"


def test_shabbaton_splits_kids():
    ev = calendars.tbe_events(date(2027, 4, 11), date(2027, 4, 11))
    rs = [e for e in ev if e.kind == "religious_school"]
    assert rs[0].kids == ["Elle"]
    assert any(e.kids == ["Ari"] and "Shabbaton" in e.title for e in ev)
