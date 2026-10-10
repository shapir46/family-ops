from datetime import date

from familyops import ROOT, playmetrics, schedules, teams
from familyops.teams import MDA, SPARTANS, _card

TEXT = (ROOT / "tests/fixtures/sample.ics").read_text()


def ev(start, end):
    return playmetrics.events(start, end, TEXT)


def test_upcoming_game_within_3_days_with_details(monkeypatch):
    monkeypatch.setattr(teams, "results", lambda t: {})
    today = date(2026, 10, 15)  # Thu; fixture game Sat Oct 17 12:30
    s = teams.section(MDA, today, ev(today, date(2026, 10, 25)), ev(date(2026, 10, 12), date(2026, 10, 14)))
    assert s["title"] == "MDA Kicks &amp; Giggles"
    assert s["items"] == [_card("Sat Oct 17 · 12:30 pm", "MDA vs Test FC Red", "Spencer Park Field 2, Rochester Hills",
                                       "Arrive 12:00 pm · Uniform: black-black-black")]


def test_hidden_when_nothing_recent_and_nothing_within_3_days(monkeypatch):
    monkeypatch.setattr(teams, "results", lambda t: {})
    today = date(2026, 10, 12)  # Mon; next game Oct 17 is 5 days out, no games Sat/Sun before
    assert teams.section(MDA, today, ev(today, date(2026, 10, 22)), ev(date(2026, 10, 9), date(2026, 10, 11))) is None


def test_monday_reports_saturday_game_and_goals_only_when_scored(monkeypatch):
    today = date(2026, 10, 19)  # Mon: covers Sat Oct 17 (game) and Sun Oct 18
    past = ev(date(2026, 10, 16), date(2026, 10, 18))
    monkeypatch.setattr(teams, "results", lambda t: {"2026-10-17": {"mda": 3, "opp": 1, "elle_goals": 2, "opponent": "Test FC Red"}})
    s = teams.section(MDA, today, ev(today, date(2026, 10, 29)), past)
    assert s["items"][0] == _card("Final · Sat Oct 17", "<b>MDA 3</b>, Test FC Red 1", "Spencer Park Field 2, Rochester Hills",
                                         "<b>Elle scored 2 goals!</b>")
    monkeypatch.setattr(teams, "results", lambda t: {"2026-10-17": {"mda": 0, "opp": 2, "elle_goals": 0}})
    s = teams.section(MDA, today, ev(today, date(2026, 10, 29)), past)
    assert "MDA 0, <b>Test FC Red 2</b>" in s["items"][0] and "scored" not in s["items"][0]


def test_missing_result_says_coming_soon(monkeypatch):
    monkeypatch.setattr(teams, "results", lambda t: {})
    s = teams.section(MDA, date(2026, 10, 18), [], ev(date(2026, 10, 17), date(2026, 10, 17)))
    assert "MDA vs Test FC Red" in s["items"][0] and "Final score coming soon." in s["items"][0]


def test_tournament_grouped_once(monkeypatch):
    monkeypatch.setattr(teams, "results", lambda t: {})
    today = date(2026, 10, 21)
    s = teams.section(MDA, today, ev(today, date(2026, 10, 31)), [])
    assert s["items"] == [_card("Tournament · Fri Oct 23", "Kalahari Cup", "Sandusky, OH")]


def test_place_formats():
    assert teams.place("Spencer Park Field 2, 3701 John R Rd, Rochester Hills, MI 48307, United States") == "Spencer Park Field 2, Rochester Hills"
    assert teams.place("Sandusky, OH, USA") == "Sandusky, OH"
    assert teams.place(None) == ""
    assert teams.place("Berkshire Middle School, 21707 W 14 Mile Rd, Beverly Hills") == "Berkshire Middle School, Beverly Hills"


def bb(start, end):
    return schedules.events(start, end)


def test_spartans_upcoming_game(monkeypatch):
    monkeypatch.setattr(teams, "results", lambda t: {})
    today = date(2026, 10, 15)  # Thu; Spartans vs Hoosiers Sat Oct 17 9:55
    s = teams.section(SPARTANS, today, bb(today, date(2026, 10, 25)), bb(date(2026, 10, 12), date(2026, 10, 14)))
    assert s == {"title": "Spartans Hoop Scoop",
                 "items": [_card("Sat Oct 17 · 9:55 am", "Spartans vs Hoosiers", "Berkshire Middle School, Beverly Hills")]}


def test_spartans_monday_final_and_points(monkeypatch):
    today = date(2026, 10, 12)  # Mon: reports Sat Oct 10 vs Tigers
    monkeypatch.setattr(teams, "results", lambda t: {"2026-10-10": {"spartans": 24, "opp": 18, "ari_points": 6}})
    s = teams.section(SPARTANS, today, bb(today, date(2026, 10, 22)), bb(date(2026, 10, 9), date(2026, 10, 11)))
    assert s["items"] == [_card("Final · Sat Oct 10", "<b>Spartans 24</b>, Tigers 18", "Berkshire Middle School, Beverly Hills",
                                "<b>Ari scored 6 points!</b>")]
    monkeypatch.setattr(teams, "results", lambda t: {"2026-10-10": {"spartans": 10, "opp": 12, "ari_points": 0}})
    s = teams.section(SPARTANS, today, [], bb(date(2026, 10, 9), date(2026, 10, 11)))
    assert "Spartans 10, <b>Tigers 12</b>" in s["items"][0] and "scored" not in s["items"][0]


def test_spartans_hidden_midweek(monkeypatch):
    monkeypatch.setattr(teams, "results", lambda t: {})
    today = date(2026, 10, 13)  # Tue: no game Mon, next game Sat (4 days out)
    assert teams.section(SPARTANS, today, bb(today, date(2026, 10, 23)), bb(date(2026, 10, 10), date(2026, 10, 12))) is None


def test_spartans_playoffs_and_tournament(monkeypatch):
    monkeypatch.setattr(teams, "results", lambda t: {})
    s = teams.section(SPARTANS, date(2026, 11, 12), bb(date(2026, 11, 12), date(2026, 11, 22)), [])
    assert s["items"][0] == _card("Fri Nov 13", "Spartans · Playoffs (if qualified)", "Berkshire Middle School, Beverly Hills",
                                  "Evening playoff games and first-place practices; Ari's division likely plays Saturday. Times TBD.")
    assert s["items"][1].startswith("<span class='gm-when'>Sat Nov 14</span>")
    s = teams.section(SPARTANS, date(2026, 12, 26), bb(date(2026, 12, 26), date(2027, 1, 5)), [])
    assert s["items"] == [_card("Tournament · Mon Dec 28–Wed Dec 30", "Holiday HOOPMANIA tournament (save the date)", "Location TBD")]
