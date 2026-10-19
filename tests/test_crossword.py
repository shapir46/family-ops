import sys

from familyops import ROOT

sys.path.insert(0, str(ROOT / "scoop"))
import crossword  # noqa: E402


def words_in(p):
    """Every across/down run of 2+ letters in the built grid."""
    cells, runs = p["cells"], []
    for r in range(p["rows"]):
        runs += [w for w in "".join(cells.get((r, c), " ") for c in range(p["cols"])).split() if len(w) > 1]
    for c in range(p["cols"]):
        runs += [w for w in "".join(cells.get((r, c), " ") for r in range(p["rows"])).split() if len(w) > 1]
    return sorted(runs)


def test_builds_a_connected_grid_with_only_the_answers():
    entries = [["Rocket", "a"], ["share", "b"], ["NOCTURNAL", "c"], ["zoo", "d"], ["trails", "e"]]
    p = crossword.build(entries)
    assert words_in(p) == sorted(["ROCKET", "SHARE", "NOCTURNAL", "ZOO", "TRAILS"])   # no stray letter runs
    assert len(p["across"]) + len(p["down"]) == 5
    assert [n for n, _ in p["across"]] == sorted(n for n, _ in p["across"])


def test_refuses_words_that_cannot_all_cross():
    assert "error" in crossword.build([["cat", ""], ["dog", ""], ["bird", ""], ["fish", ""]])
    assert "error" in crossword.build([["one", ""], ["two", ""], ["six", ""]])          # too few words
    assert "error" in crossword.build([["ab", ""], ["bat", ""], ["tab", ""], ["bait", ""]])   # 2-letter answer


def test_html_box_has_clues_and_upside_down_key():
    box, warn = crossword.html_box({"words": [["PUMPKIN", "Orange & round"], ["JUICE", "b"], ["ROCKET", "c"], ["SHARE", "d"]]})
    assert warn is None and "Orange &amp; round" in box and "xw-key" in box and "PUMPKIN" in box
    box, warn = crossword.html_box({"words": [["cat", ""], ["dog", ""], ["bird", ""], ["fish", ""]]})
    assert box == "" and warn.startswith("CROSSWORD WARNING")
