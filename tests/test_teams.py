import json
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


# --- Spartans: shown only in the first paper after MCE posts the score and recap (Jacob, 2026-10-19) ---

RECAP = "The Spartans & friends rallied in the fourth."
POSTED = {"2026-10-10": {"spartans": 24, "opp": 18, "opponent": "Tigers", "ari_points": 6, "source": "MCE league results",
                         "recap": RECAP}}
NO_RECAP = {"2026-10-10": {k: v for k, v in POSTED["2026-10-10"].items() if k != "recap"}}


def fresh(monkeypatch, printed=False):
    no_results(monkeypatch)
    monkeypatch.setattr(teams, "_recap_printed", lambda t, d, today: printed)


def test_spartans_shows_final_recap_and_next(monkeypatch):
    fresh(monkeypatch)
    today = date(2026, 10, 15)  # Thu: Sat Oct 10 vs Tigers, score and recap posted; next = Sat Oct 17 vs Hoosiers
    s = teams.section(SPARTANS, today, bb(today, date(2026, 10, 25)), bb(date(2026, 9, 17), date(2026, 10, 14)), POSTED)
    assert s == {"title": "Spartans Hoop Scoop", "items": [
        _card("Final · Sat Oct 10", "<b>Spartans 24</b>, Tigers 18", BERKSHIRE, "<b>Ari scored 6 points!</b>", RECAP),
        _card("Sat Oct 17 · 9:55 am", "Spartans vs Hoosiers", BERKSHIRE)]}
    assert "Spartans &amp; friends" in s["items"][0]


def test_spartans_shown_even_when_next_game_is_far(monkeypatch):
    fresh(monkeypatch)
    far = [e for e in bb(date(2026, 10, 16), date(2026, 10, 30)) if e.date > "2026-10-20"]
    s = teams.section(SPARTANS, date(2026, 10, 16), far, bb(date(2026, 9, 18), date(2026, 10, 15)), POSTED)
    assert "gm-recap" in s["items"][0]


def test_spartans_hidden_until_the_recap_is_posted(monkeypatch):
    fresh(monkeypatch)
    today = date(2026, 10, 12)  # Mon after the game, next game in 5 days: no score yet, no "coming soon" box
    args = (SPARTANS, today, bb(today, date(2026, 10, 22)), bb(date(2026, 9, 14), date(2026, 10, 11)))
    assert teams.section(*args, {}) is None
    assert teams.section(*args, NO_RECAP) is None   # a score without its recap is not enough
    assert teams.section(SPARTANS, date(2026, 10, 16), bb(date(2026, 10, 16), date(2026, 10, 26)),
                         bb(date(2026, 9, 18), date(2026, 10, 15)), NO_RECAP) is None   # next game within 3 days: still hidden


def test_spartans_hidden_after_the_recap_was_printed(monkeypatch):
    fresh(monkeypatch, printed=True)
    today = date(2026, 10, 16)
    assert teams.section(SPARTANS, today, bb(today, date(2026, 10, 26)), bb(date(2026, 9, 18), date(2026, 10, 15)), POSTED) is None


def test_recap_printed_reads_earlier_papers(monkeypatch, tmp_path):
    (tmp_path / "state").mkdir()
    monkeypatch.setattr(teams, "ROOT", tmp_path)
    card = _card("Final · Sat Oct 10", "<b>Spartans 24</b>, Tigers 18", BERKSHIRE, "", RECAP)
    box = lambda items: json.dumps({"spartans": {"title": "Spartans Hoop Scoop", "items": items}})
    (tmp_path / "state/2026-10-11.json").write_text(box([card]))                    # Sunday: no paper, doesn't count
    (tmp_path / "state/2026-10-15.json").write_text(box([_card("Final · Sat Oct 10", "x", BERKSHIRE)]))   # no recap
    assert not teams._recap_printed(SPARTANS, "2026-10-10", date(2026, 10, 16))
    (tmp_path / "state/2026-10-16.json").write_text(box([card]))                    # Friday's paper printed it
    assert not teams._recap_printed(SPARTANS, "2026-10-10", date(2026, 10, 16))     # today's own state doesn't count
    assert teams._recap_printed(SPARTANS, "2026-10-10", date(2026, 10, 17))


def test_jacobs_result_wins_over_posted(monkeypatch):
    fresh(monkeypatch)
    monkeypatch.setattr(teams, "results", lambda t: {"2026-10-10": {"spartans": 24, "opp": 18, "ari_points": 8}})
    today = date(2026, 10, 15)
    s = teams.section(SPARTANS, today, bb(today, date(2026, 10, 25)), bb(date(2026, 9, 17), date(2026, 10, 14)), POSTED)
    assert "Ari scored 8 points!" in s["items"][0] and "gm-recap" in s["items"][0]


def test_spartans_playoffs_and_tournament(monkeypatch):
    fresh(monkeypatch)
    def posted_for(past):
        last = max(e.date for e in past if teams._is_game(SPARTANS, e) and teams._opponent(SPARTANS, e))
        return {last: {"spartans": 30, "opp": 20, "recap": "Recap."}}
    today = date(2026, 11, 12)
    past = bb(date(2026, 10, 15), date(2026, 11, 11))
    s = teams.section(SPARTANS, today, bb(today, date(2026, 11, 22)), past, posted_for(past))
    assert s["items"][1] == _card("Fri Nov 13", "Spartans · Playoffs (if qualified)", BERKSHIRE,
                                  "Evening playoff games and first-place practices; Ari's division likely plays Saturday. Times TBD.")
    past = bb(date(2026, 10, 15), date(2026, 12, 25))   # reaches back to the last game, whose recap is posted
    s = teams.section(SPARTANS, date(2026, 12, 26), bb(date(2026, 12, 26), date(2027, 1, 5)), past, posted_for(past))
    assert s["items"][1] == _card("Tournament · Mon Dec 28–Wed Dec 30", "Holiday HOOPMANIA tournament (save the date)", "Location TBD")


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
