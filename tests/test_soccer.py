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
    assert s["items"] == ["<b>Sat Oct 17, 12:30 pm:</b> vs Test FC Red · arrive 12:00 pm, black-black-black · Spencer Park Field 2"]


def test_hidden_when_nothing_recent_and_nothing_within_3_days(monkeypatch):
    monkeypatch.setattr(soccer, "results", lambda: {})
    today = date(2026, 10, 12)  # Mon; next game Oct 17 is 5 days out, no games Sat/Sun before
    assert soccer.section(today, ev(today, date(2026, 10, 22)), ev(date(2026, 10, 9), date(2026, 10, 11))) is None


def test_monday_reports_saturday_game_and_goals_only_when_scored(monkeypatch):
    today = date(2026, 10, 19)  # Mon: covers Sat Oct 17 (game) and Sun Oct 18
    past = ev(date(2026, 10, 16), date(2026, 10, 18))
    monkeypatch.setattr(soccer, "results", lambda: {"2026-10-17": {"mda": 3, "opp": 1, "elle_goals": 2, "opponent": "Test FC Red"}})
    s = soccer.section(today, ev(today, date(2026, 10, 29)), past)
    assert s["items"][0] == "<b>Sat Oct 17:</b> MDA won 3–1 vs Test FC Red. <b>Elle scored 2 goals!</b>"
    monkeypatch.setattr(soccer, "results", lambda: {"2026-10-17": {"mda": 0, "opp": 2, "elle_goals": 0}})
    s = soccer.section(today, ev(today, date(2026, 10, 29)), past)
    assert s["items"][0] == "<b>Sat Oct 17:</b> MDA lost 0–2 vs Test FC Red" and "scored" not in s["items"][0]


def test_missing_result_says_coming_soon(monkeypatch):
    monkeypatch.setattr(soccer, "results", lambda: {})
    s = soccer.section(date(2026, 10, 18), [], ev(date(2026, 10, 17), date(2026, 10, 17)))
    assert s["items"] == ["<b>Sat Oct 17:</b> MDA played Test FC Red. Final score coming soon."]


def test_tournament_grouped_once(monkeypatch):
    monkeypatch.setattr(soccer, "results", lambda: {})
    today = date(2026, 10, 21)
    s = soccer.section(today, ev(today, date(2026, 10, 31)), [])
    assert s["items"] == ["<b>Fri Oct 23:</b> Kalahari Cup in Sandusky"]
