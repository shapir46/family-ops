import sys

from familyops import ROOT

sys.path.insert(0, str(ROOT / "scoop"))
import sudoku  # noqa: E402


def valid(g):
    rows = all(sorted(r) == [1, 2, 3, 4] for r in g)
    cols = all(sorted(g[r][c] for r in range(4)) == [1, 2, 3, 4] for c in range(4))
    boxes = all(sorted(g[r][c] for r in (br, br + 1) for c in (bc, bc + 1)) == [1, 2, 3, 4] for br in (0, 2) for bc in (0, 2))
    return rows and cols and boxes


def test_every_puzzle_has_one_answer_that_matches_its_givens():
    for day in range(1, 200):
        puz, sol = sudoku.make(f"2026-x-{day}")
        assert valid(sol)
        assert sum(v > 0 for r in puz for v in r) == sudoku.GIVENS
        assert all(p in (0, s) for pr, sr in zip(puz, sol) for p, s in zip(pr, sr))
        assert sudoku.count_solutions([r[:] for r in puz]) == 1


def test_same_date_same_puzzle_and_how_to_switch():
    assert sudoku.make("2026-10-20") == sudoku.make("2026-10-20") != sudoku.make("2026-10-22")
    assert "How to play" in sudoku.html_box("2026-10-20", how_to=True)
    assert "How to play" not in sudoku.html_box("2026-11-03", how_to=False)
