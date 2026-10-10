from datetime import date

from familyops import ROOT, playmetrics, soccer

TEXT = (ROOT / "tests/fixtures/sample.ics").read_text()


def ev(start, end):
    return playmetrics.events(start, end, TEXT)


def test_upcoming_game_within_3_days_with_details(monkeypatch):
    monkeypatch.setattr(soccer, "results", lambda: {})
    today = date(2026, 10, 15)  # Thu; fixture game Sat Oct 17 12:30
    s = soccer.section(today, ev(today, date(2026, 10, 25)), ev(date(2026, 10, 12), date(2026, 10, 14)))
    assert s["title"] == "MDA Kicks &amp; Giggles"
    assert s["items"] == [soccer._card("Sat Oct 17 · 12:30 pm", "MDA vs Test FC Red", "Spencer Park Field 2, Rochester Hills",
                                       "Arrive 12:00 pm · Uniform: black-black-black")]


def test_hidden_when_nothing_recent_and_nothing_within_3_days(monkeypatch):
    monkeypatch.setattr(soccer, "results", lambda: {})
    today = date(2026, 10, 12)  # Mon; next game Oct 17 is 5 days out, no games Sat/Sun before
    assert soccer.section(today, ev(today, date(2026, 10, 22)), ev(date(2026, 10, 9), date(2026, 10, 11))) is None


def test_monday_reports_saturday_game_and_goals_only_when_scored(monkeypatch):
    today = date(2026, 10, 19)  # Mon: covers Sat Oct 17 (game) and Sun Oct 18
    past = ev(date(2026, 10, 16), date(2026, 10, 18))
    monkeypatch.setattr(soccer, "results", lambda: {"2026-10-17": {"mda": 3, "opp": 1, "elle_goals": 2, "opponent": "Test FC Red"}})
    s = soccer.section(today, ev(today, date(2026, 10, 29)), past)
    assert s["items"][0] == soccer._card("Final · Sat Oct 17", "<b>MDA 3</b>, Test FC Red 1", "Spencer Park Field 2, Rochester Hills",
                                         "<b>Elle scored 2 goals!</b>")
    monkeypatch.setattr(soccer, "results", lambda: {"2026-10-17": {"mda": 0, "opp": 2, "elle_goals": 0}})
    s = soccer.section(today, ev(today, date(2026, 10, 29)), past)
    assert "MDA 0, <b>Test FC Red 2</b>" in s["items"][0] and "scored" not in s["items"][0]


def test_missing_result_says_coming_soon(monkeypatch):
    monkeypatch.setattr(soccer, "results", lambda: {})
    s = soccer.section(date(2026, 10, 18), [], ev(date(2026, 10, 17), date(2026, 10, 17)))
    assert "MDA vs Test FC Red" in s["items"][0] and "Final score coming soon." in s["items"][0]


def test_tournament_grouped_once(monkeypatch):
    monkeypatch.setattr(soccer, "results", lambda: {})
    today = date(2026, 10, 21)
    s = soccer.section(today, ev(today, date(2026, 10, 31)), [])
    assert s["items"] == [soccer._card("Tournament · Fri Oct 23", "Kalahari Cup", "Sandusky, OH")]


def test_place_formats():
    assert soccer.place("Spencer Park Field 2, 3701 John R Rd, Rochester Hills, MI 48307, United States") == "Spencer Park Field 2, Rochester Hills"
    assert soccer.place("Sandusky, OH, USA") == "Sandusky, OH"
    assert soccer.place(None) == ""
