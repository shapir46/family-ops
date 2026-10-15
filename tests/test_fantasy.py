import json
from datetime import date

from familyops import ROOT, fantasy

LEAGUE = json.loads((ROOT / "tests/fixtures/espn-league.json").read_text())


def test_summary_record_rank_and_matchups():
    s = fantasy.summarize(LEAGUE, 3)
    assert (s["team"], s["record"], s["rank"], s["teams"], s["week"]) == ("Ari's Touchdown Tigers", "4-1", 2, 3, 6)
    assert s["this_week"] == {"week": 6, "opponent": "Bloomfield Blitz", "score": 70.5, "opp_score": 61.8, "winner": "UNDECIDED",
                              "proj": None, "opp_proj": None, "top": None, "opp_top": None}
    assert s["last_week"]["result"] == "W" and s["last_week"]["opponent"] == "End Zone Eagles"


def test_not_configured_is_silent(monkeypatch):
    monkeypatch.setattr(fantasy, "config", lambda: None)
    assert fantasy.get() is None


def _summary(**this_week):
    row = {"week": 6, "opponent": "Bloomfield Blitz", "score": 70.5, "opp_score": 61.8, "winner": "UNDECIDED",
           "proj": 112.4, "opp_proj": 98.0, "top": {"name": "Jahmyr Gibbs", "pos": "RB", "pts": 24.1},
           "opp_top": {"name": "Rams D/ST", "pos": "D/ST", "pts": 9.0}}
    row.update(this_week)
    last = {"week": 5, "opponent": "End Zone Eagles", "score": 118.4, "opp_score": 97.1, "winner": "HOME",
            "result": "W", "proj": None, "opp_proj": None, "top": {"name": "Josh Allen", "pos": "QB", "pts": 30.2},
            "opp_top": None}
    return {"team": "Ari's Touchdown Tigers", "record": "4-1", "rank": 2, "teams": 10, "week": 6, "active": True,
            "latest_period": 6, "this_week": row, "last_week": last}


def test_top_player_is_a_starter_with_that_weeks_points():
    def entry(slot, name, pos, pts, week=6):
        return {"lineupSlotId": slot, "playerPoolEntry": {"player": {
            "fullName": name, "defaultPositionId": pos, "stats": [{"statSourceId": 1, "scoringPeriodId": week, "appliedTotal": 99.0},
                                                                   {"statSourceId": 0, "scoringPeriodId": week, "appliedTotal": pts}]}}}
    side = {"rosterForCurrentScoringPeriod": {"entries": [entry(20, "Bench Guy", 2, 40.0), entry(2, "Jahmyr Gibbs", 2, 24.1),
                                                          entry(0, "Jared Goff", 1, 18.3), entry(21, "Hurt Guy", 3, 50.0)]}}
    assert fantasy._top(side, 6) == {"name": "Jahmyr Gibbs", "pos": "RB", "pts": 24.1}
    assert fantasy._top({}, 6) is None


def test_box_only_fri_sat_mon_tue():
    s = _summary()
    shown = {d: fantasy.box(s, date(2026, 10, d)) is not None for d in range(12, 19)}   # Mon Oct 12 .. Sun Oct 18
    assert shown == {12: True, 13: True, 14: False, 15: False, 16: True, 17: True, 18: False}
    assert fantasy.box(None, date(2026, 10, 12)) is None
    assert fantasy.box({**s, "active": False}, date(2026, 10, 12)) is None


def test_box_score_projection_and_top_players():
    mon = fantasy.box(_summary(), date(2026, 10, 12))
    assert mon["title"] == "Ari&#8217;s Fantasy Team: Ari's Touchdown Tigers"
    assert mon["items"] == ["4–1, 2nd of 10", "<b>Week 6</b> vs Bloomfield Blitz", "Score: <b>70.5–61.8</b>, leading",
                            "Projected: 112.4–98.0", "Ari&#8217;s top player: <b>Jahmyr Gibbs</b>, RB, 24.1 pts",
                            "Their top player: <b>Rams D/ST</b>, 9.0 pts"]
    fri = fantasy.box(_summary(score=0.0, opp_score=0.0), date(2026, 10, 16))
    assert fri["items"][2:] == ["Score: <b>0.0–0.0</b>, no games yet", "Projected: 112.4–98.0"]   # no top players on Fri


def test_tuesday_shows_the_week_just_played():
    # ESPN has already moved on to week 7 (no points yet): Tuesday reports week 6, final.
    s = _summary(score=0.0, opp_score=0.0)
    s["last_week"] = {**s["this_week"], "week": 6, "score": 121.0, "opp_score": 99.5, "winner": "AWAY", "proj": None,
                      "opp_proj": None, "top": {"name": "Josh Allen", "pos": "QB", "pts": 30.2}}
    s["this_week"] = {**s["this_week"], "week": 7, "opponent": "Next Team"}
    tue = fantasy.box(s, date(2026, 10, 13))
    assert tue["items"][1:4] == ["<b>Week 6</b> vs Bloomfield Blitz", "Final: <b>W 121.0–99.5</b>",
                                 "Ari&#8217;s top player: <b>Josh Allen</b>, QB, 30.2 pts"]


def test_box_hidden_after_the_season():
    assert fantasy.box(_summary(winner="HOME"), date(2026, 10, 16)) is None   # Friday, current week already final
