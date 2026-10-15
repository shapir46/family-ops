from datetime import date

from familyops import ROOT, mce, playmetrics, schedules, teams
from familyops.model import Event
from familyops.teams import MDA, SPARTANS, _card

TEXT = (ROOT / "tests/fixtures/sample.ics").read_text()
SPENCER = "Spencer Park Field 2, Rochester Hills"
BERKSHIRE = "Berkshire Middle School, Beverly Hills"
NEXT_MDA = _card("Sat Oct 17 · 12:30 pm", "MDA vs Test FC Red", SPENCER, "Arrive 12:00 pm · Uniform: black-black-black")
KALAHARI = _card("Tournament · Fri Oct 23", "Kalahari Cup", "Sandusky, OH")


def ev(start, end):
    return playmetrics.events(start, end, TEXT)


def bb(start, end):
    return schedules.events(start, end)


def no_results(monkeypatch):
    monkeypatch.setattr(teams, "results", lambda t: {})


# --- MDA: last game + next game/tournament only -------------------------------------------------

def test_next_game_within_3_days(monkeypatch):
    no_results(monkeypatch)
    today = date(2026, 10, 15)  # Thu; no earlier game in the fixture
    s = teams.section(MDA, today, ev(today, date(2026, 10, 25)), ev(date(2026, 9, 17), date(2026, 10, 14)))
    assert s == {"title": "MDA Kicks &amp; Giggles", "items": [NEXT_MDA]}


def test_hidden_when_nothing_recent_and_next_is_far(monkeypatch):
    no_results(monkeypatch)
    today = date(2026, 10, 12)  # Mon; next game Oct 17 is 5 days out
    assert teams.section(MDA, today, ev(today, date(2026, 10, 22)), ev(date(2026, 9, 14), date(2026, 10, 11))) is None


def test_monday_final_then_only_the_next_item(monkeypatch):
    today = date(2026, 10, 19)  # Mon: Sat Oct 17 game; next is the Kalahari Cup (one card, not every upcoming item)
    past = ev(date(2026, 9, 21), date(2026, 10, 18))
    monkeypatch.setattr(teams, "results", lambda t: {"2026-10-17": {"mda": 3, "opp": 1, "elle_goals": 2, "opponent": "Test FC Red"}})
    s = teams.section(MDA, today, ev(today, date(2026, 10, 29)), past)
    assert s["items"] == [_card("Final · Sat Oct 17", "<b>MDA 3</b>, Test FC Red 1", SPENCER, "<b>Elle scored 2 goals!</b>"), KALAHARI]
    monkeypatch.setattr(teams, "results", lambda t: {"2026-10-17": {"mda": 0, "opp": 2, "elle_goals": 0}})
    s = teams.section(MDA, today, ev(today, date(2026, 10, 29)), past)
    assert "MDA 0, <b>Test FC Red 2</b>" in s["items"][0] and "scored" not in s["items"][0]


def test_last_game_shown_midweek_when_next_is_close(monkeypatch):
    no_results(monkeypatch)
    today = date(2026, 10, 21)  # Wed: last game Sat Oct 17 (no score yet), Kalahari Cup Fri
    s = teams.section(MDA, today, ev(today, date(2026, 10, 31)), ev(date(2026, 9, 23), date(2026, 10, 20)))
    assert s["items"] == [_card("Last game · Sat Oct 17", "MDA vs Test FC Red", SPENCER, "Final score coming soon."), KALAHARI]


def test_old_game_without_score_stops_saying_coming_soon(monkeypatch):
    no_results(monkeypatch)
    today = date(2026, 10, 28)
    nxt = Event(date="2026-10-29", start="18:00", title="Soccer game vs Late FC", kids=["Elle"], kind="game", sources=["PlayMetrics"])
    s = teams.section(MDA, today, [nxt], ev(date(2026, 9, 30), date(2026, 10, 27)))
    assert s["items"][0] == _card("Last game · Sat Oct 17", "MDA vs Test FC Red", SPENCER)
    assert s["items"][1] == _card("Thu Oct 29 · 6:00 pm", "MDA vs Late FC")


def test_place_formats():
    assert teams.place("Spencer Park Field 2, 3701 John R Rd, Rochester Hills, MI 48307, United States") == SPENCER
    assert teams.place("Sandusky, OH, USA") == "Sandusky, OH"
    assert teams.place(None) == ""
    assert teams.place("Berkshire Middle School, 21707 W 14 Mile Rd, Beverly Hills") == BERKSHIRE


# --- Spartans ------------------------------------------------------------------------------------

POSTED = {"2026-10-10": {"spartans": 24, "opp": 18, "opponent": "Tigers", "ari_points": 6, "source": "MCE league results"}}


def test_spartans_last_and_next(monkeypatch):
    no_results(monkeypatch)
    today = date(2026, 10, 15)  # Thu: last = Sat Oct 10 vs Tigers (score posted online), next = Sat Oct 17 vs Hoosiers
    s = teams.section(SPARTANS, today, bb(today, date(2026, 10, 25)), bb(date(2026, 9, 17), date(2026, 10, 14)), POSTED)
    assert s == {"title": "Spartans Hoop Scoop", "items": [
        _card("Final · Sat Oct 10", "<b>Spartans 24</b>, Tigers 18", BERKSHIRE, "<b>Ari scored 6 points!</b>"),
        _card("Sat Oct 17 · 9:55 am", "Spartans vs Hoosiers", BERKSHIRE)]}


def test_jacobs_result_wins_over_posted(monkeypatch):
    monkeypatch.setattr(teams, "results", lambda t: {"2026-10-10": {"spartans": 24, "opp": 18, "ari_points": 8}})
    today = date(2026, 10, 12)
    s = teams.section(SPARTANS, today, bb(today, date(2026, 10, 22)), bb(date(2026, 9, 14), date(2026, 10, 11)), POSTED)
    assert "Ari scored 8 points!" in s["items"][0]


def test_spartans_monday_without_score(monkeypatch):
    no_results(monkeypatch)
    today = date(2026, 10, 12)
    s = teams.section(SPARTANS, today, bb(today, date(2026, 10, 22)), bb(date(2026, 9, 14), date(2026, 10, 11)), {})
    assert s["items"][0] == _card("Last game · Sat Oct 10", "Spartans vs Tigers", BERKSHIRE, "Final score coming soon.")


def test_spartans_hidden_midweek(monkeypatch):
    no_results(monkeypatch)
    today = date(2026, 10, 13)  # Tue: no game Mon, next game Sat (4 days out)
    assert teams.section(SPARTANS, today, bb(today, date(2026, 10, 23)), bb(date(2026, 9, 15), date(2026, 10, 12)), POSTED) is None


def test_spartans_playoffs_and_tournament(monkeypatch):
    no_results(monkeypatch)
    today = date(2026, 11, 12)
    s = teams.section(SPARTANS, today, bb(today, date(2026, 11, 22)), bb(date(2026, 10, 15), date(2026, 11, 11)))
    assert s["items"][1] == _card("Fri Nov 13", "Spartans · Playoffs (if qualified)", BERKSHIRE,
                                  "Evening playoff games and first-place practices; Ari's division likely plays Saturday. Times TBD.")
    s = teams.section(SPARTANS, date(2026, 12, 26), bb(date(2026, 12, 26), date(2027, 1, 5)), bb(date(2026, 11, 28), date(2026, 12, 25)))
    assert s["items"] == [_card("Tournament · Mon Dec 28–Wed Dec 30", "Holiday HOOPMANIA tournament (save the date)", "Location TBD")]


# --- MCE results page ----------------------------------------------------------------------------

PAGE = """<html><body><p>Evolution Basketball League Results</p>
<p>ROOKIE LEAGUE:  OCTOBER 10:</p><p>Spartans 30, Tigers 2</p><p>:</p><p>Rookie recap, not Ari's division.</p>
<p>COLLEGE DIVISION: SATURDAY, OCTOBER 10:</p>
<p>Tigers 18, Spartans 24</p><p>:</p><p>Ari Shapiro scored six of his ten points in the first half, while Sam Lee had 12 points.</p>
<p>Hoosiers 20, Duke 19</p><p>:</p><p>Close one.</p></body></html>"""


def test_mce_parse_matches_division_date_and_both_teams():
    sched = [{"date": date(2026, 10, 10), "kind": "game", "title": "Basketball game vs Tigers"}]
    cfg = {"url": "x", "team": "Spartans", "player": "Ari Shapiro", "score_key": "spartans", "stat_key": "ari_points"}
    got = mce.results({**cfg, "division": "College"}, sched, date(2026, 10, 12), page=PAGE)
    assert got == {"2026-10-10": {"spartans": 24, "opp": 18, "opponent": "Tigers", "ari_points": 10, "source": "MCE league results",
                                  "recap": "Ari Shapiro scored six of his ten points in the first half, while Sam Lee had 12 points."}}
    # Without a division, the Rookie "Spartans 30, Tigers 2" also matches; the recap naming Ari decides.
    assert mce.results(cfg, sched, date(2026, 10, 12), page=PAGE)["2026-10-10"]["spartans"] == 24
    # Two same-name games and no way to tell them apart: skipped, never guessed.
    assert mce.results({**cfg, "player": None}, sched, date(2026, 10, 12), page=PAGE) == {}


def test_mce_player_points():
    r = "Max Doe scored six of his eight points early. Reece Roe scored all six of his points. Beau Poe (12pts) ran the floor."
    assert mce.player_points(r, "Max Doe") == 8
    assert mce.player_points(r, "Reece Roe") == 6
    assert mce.player_points(r, "Beau Poe") == 12
    assert mce.player_points(r, "Nobody") is None


PAGE_ABBREV = """<html><body><p>BOYS LEAGUE: SATURDAY, OCT 10</p>
<p>Knicks 28, Hoosiers 20</p><p>:</p><p>Knicks recap.</p>
<p>Spartans 31, Tigers 24</p><p>:</p><p>The Spartans rallied in the fourth. Ari Shapiro added 4pts.</p></body></html>"""


def test_mce_abbreviated_heading_division_list_and_recap():
    # MCE's Oct 2026 page: "BOYS LEAGUE: SATURDAY, OCT 10" (abbreviated month, no "College").
    sched = [{"date": date(2026, 10, 10), "kind": "game", "title": "Basketball game vs Tigers"}]
    cfg = {"url": "x", "team": "Spartans", "player": "Ari Shapiro", "score_key": "spartans", "stat_key": "ari_points",
           "division": ["College", "Boys League"]}
    got = mce.results(cfg, sched, date(2026, 10, 15), page=PAGE_ABBREV)["2026-10-10"]
    assert (got["spartans"], got["opp"], got["ari_points"]) == (31, 24, 4)
    assert got["recap"] == "The Spartans rallied in the fourth. Ari Shapiro added 4pts."
    assert mce.results({**cfg, "division": "College"}, sched, date(2026, 10, 15), page=PAGE_ABBREV) == {}
    assert [g["date"] for g in mce.parse("<p>ROOKIE LEAGUE: SEPT 28:</p><p>A 1, B 2</p>", date(2026, 10, 1))] == ["2026-09-28"]


def test_mce_short_recap_cuts_at_a_sentence():
    assert mce.short_recap("One two three. Four five six. Seven.", max_words=6) == "One two three. Four five six."
    assert mce.short_recap("A very long first sentence here.", max_words=2) == "A very long first sentence here."


def test_spartans_friday_prints_the_recap(monkeypatch):
    no_results(monkeypatch)
    posted = {"2026-10-10": {**POSTED["2026-10-10"], "recap": "Spartans & friends won."}}
    past = bb(date(2026, 9, 18), date(2026, 10, 15))
    fri = teams.section(SPARTANS, date(2026, 10, 16), bb(date(2026, 10, 16), date(2026, 10, 26)), past, posted)
    assert fri["items"][0] == _card("Final · Sat Oct 10", "<b>Spartans 24</b>, Tigers 18", BERKSHIRE,
                                    "<b>Ari scored 6 points!</b>", "Spartans & friends won.")
    assert "Spartans &amp; friends won." in fri["items"][0]
    # Not on other days.
    thu = teams.section(SPARTANS, date(2026, 10, 15), bb(date(2026, 10, 15), date(2026, 10, 25)), past, posted)
    assert "gm-recap" not in thu["items"][0]
    # Friday with the next game more than 3 days away (bye week): the box still appears for the recap.
    far = [e for e in bb(date(2026, 10, 16), date(2026, 10, 30)) if e.date > "2026-10-20"]
    assert "gm-recap" in teams.section(SPARTANS, date(2026, 10, 16), far, past, posted)["items"][0]
    # No recap posted: Friday falls back to the normal rules.
    assert "gm-recap" not in teams.section(SPARTANS, date(2026, 10, 16), bb(date(2026, 10, 16), date(2026, 10, 26)), past,
                                           POSTED)["items"][0]
