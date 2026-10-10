from datetime import date

from familyops import ROOT, playmetrics

TEXT = (ROOT / "tests/fixtures/sample.ics").read_text()


def evs(start=date(2026, 10, 10), end=date(2026, 10, 31)):
    return playmetrics.events(start, end, TEXT)


def test_rrule_exdate_and_override():
    practices = [(e.date, e.start) for e in evs() if e.kind == "practice"]
    # Tue/Thu from Oct 13, COUNT=6: 13, 15(EXDATE), 20(moved to 17:30), 22, 27, 29
    assert practices == [("2026-10-13", "18:00"), ("2026-10-20", "17:30"), ("2026-10-22", "18:00"),
                         ("2026-10-27", "18:00"), ("2026-10-29", "18:00")]
    moved = next(e for e in evs() if e.date == "2026-10-20")
    assert moved.location.startswith("Derby Middle School")


def test_utc_converted_and_game_details():
    g = next(e for e in evs() if e.kind == "game")
    assert (g.date, g.start, g.end) == ("2026-10-17", "12:30", "13:30")  # 16:30Z = 12:30 EDT
    assert g.title == "Soccer game vs Test FC Red"
    assert g.details == "arrive 12:00 pm, black-black-black"
    assert g.location.startswith("Spencer Park Field 2")


def test_all_day_cancelled_and_window():
    cup = [e for e in evs() if e.title == "Kalahari Cup"]
    assert len(cup) == 1 and cup[0].start is None
    assert not any(e.date == "2026-10-16" for e in evs())  # cancelled
    assert [e.date for e in evs(date(2026, 10, 22), date(2026, 10, 22))] == ["2026-10-22"]


def test_no_credentials_leak():
    z = next(e for e in evs() if "Zoom" in e.title)
    blob = repr(z.to_dict())
    assert "SECRET" not in blob and "abc123" not in blob and "http" not in blob
    assert z.location == "Zoom"
