from datetime import date

from familyops import ROOT, feeds

FIX = ROOT / "tests/fixtures"
TEXTS = {"Swim · Red Group": (FIX / "swim-red.ics").read_text(),
         "Swim · Meets & Team Events": (FIX / "swim-team.ics").read_text()}


def _evs():
    return {(e.date, e.title): e for e in feeds.events(date(2026, 10, 30), date(2026, 11, 9), TEXTS)}


def test_swim_feeds_are_configured_for_ari():
    names = {f["name"]: f for f in feeds.config()}
    assert set(names) == set(TEXTS)
    assert all(f["kids"] == ["Ari"] and f["url"].startswith("https://calendar.google.com/") for f in names.values())


def test_swim_practices_and_events():
    evs = _evs()
    p = evs[("2026-11-02", "Swim practice")]
    assert (p.start, p.end, p.location, p.kind, p.kids, p.sources) == ("18:45", "20:00", "BHHS", "practice", ["Ari"], ["Swim · Red Group"])
    assert evs[("2026-11-03", "Swim practice (Red 1 & 2)")].location == "NHMS"
    clinic = evs[("2026-10-30", "Swim: Red Group Starts Clinic")]
    assert (clinic.kind, clinic.location, clinic.details) == ("event", "Cranbrook", "Pre-Registration Required")
    meet = evs[("2026-11-07", "Swim: Quacktackular Meet")]
    assert (meet.start, meet.location, meet.sources) == (None, "Birmingham Seaholm", ["Swim · Meets & Team Events"])
    assert ("2026-11-06", "No swim practice (all groups)") in evs


def test_club_calendar_drops_other_groups_only():
    titles = {t for _, t in _evs()}
    assert "Swim: White 2 Clinic" not in titles          # names another group only
    assert "Swim: Blue/Red 1 Clinic" in titles            # names Red too
