from datetime import date

from familyops import ROOT, lunch

FIX = ROOT / "tests/fixtures"


def parsed(month):
    return lunch.parse_pdf((FIX / f"lunch-2026-{month:02d}.pdf").read_bytes())


def test_october_grid():
    p = parsed(10)
    assert p["month"] == "October"
    assert sorted(map(int, p["days"])) == [1, 2, 5, 6, 7, 8, 9, 12, 13, 14, 15, 16, 19, 20, 21, 22, 23, 26, 27, 28, 29, 30]
    assert lunch.check(p, 2026, 10) == []
    assert p["days"]["8"]["entree"] == "Baked Whole Grain Chicken Drumstick with Baked Tater Tots"
    assert p["days"]["16"]["entree"].startswith("Fish & Chip Friday")  # "Friday" in a cell must not break the header
    assert p["days"]["13"]["half_day"] and p["days"]["30"]["half_day"]
    assert p["days"]["5"]["theme"] == "BrunchforLunch"


def test_october_half_days_match_district_calendar():
    from familyops import calendars
    p = parsed(10)
    half = {int(d) for d, v in p["days"].items() if v["half_day"]}
    district = {int(e.date[-2:]) for e in calendars.bps_events(date(2026, 10, 1), date(2026, 10, 31))
                if e.status == "half_day"}
    assert half == district == {13, 30}


def test_september_first_week_shift_is_flagged_not_hidden():
    p = parsed(9)
    probs = lunch.check(p, 2026, 9)
    assert any(x.startswith("day 1:") for x in probs)
    assert p["days"]["4"]["no_school"] and p["days"]["7"]["no_school"]
    assert "Pizza" in p["days"]["9"]["entree"]
