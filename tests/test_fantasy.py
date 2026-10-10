import json

from familyops import ROOT, fantasy

LEAGUE = json.loads((ROOT / "tests/fixtures/espn-league.json").read_text())


def test_summary_record_rank_and_matchups():
    s = fantasy.summarize(LEAGUE, 3)
    assert (s["team"], s["record"], s["rank"], s["teams"], s["week"]) == ("Ari's Touchdown Tigers", "4-1", 2, 3, 6)
    assert s["this_week"] == {"week": 6, "opponent": "Bloomfield Blitz", "score": 70.5, "opp_score": 61.8, "winner": "UNDECIDED"}
    assert s["last_week"]["result"] == "W" and s["last_week"]["opponent"] == "End Zone Eagles"


def test_not_configured_is_silent(monkeypatch):
    monkeypatch.setattr(fantasy, "config", lambda: None)
    assert fantasy.get() is None
