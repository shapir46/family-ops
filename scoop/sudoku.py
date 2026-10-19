"""Daily Sudoku: a 4x4 kids' sudoku that alternates with the crossword (Jacob, 2026-10-19).

The puzzle is made from the edition's date (same date, same puzzle), so the daily run writes nothing for it. Every
puzzle is checked to have exactly one solution. Rows, columns and the four 2x2 boxes each hold 1, 2, 3 and 4.

  python sudoku.py 2026-10-20      print that day's puzzle and answer
"""
from __future__ import annotations

import random
import sys

GIVENS = 7        # numbers already filled in: enough for a 1st grader to start, few enough to be a puzzle
BASE = [[1, 2, 3, 4], [3, 4, 1, 2], [2, 1, 4, 3], [4, 3, 2, 1]]


def _ok(g: list[list[int]], r: int, c: int, v: int) -> bool:
    if v in g[r] or any(g[i][c] == v for i in range(4)):
        return False
    br, bc = r - r % 2, c - c % 2
    return all(g[i][j] != v for i in (br, br + 1) for j in (bc, bc + 1))


def count_solutions(g: list[list[int]], limit: int = 2) -> int:
    for r in range(4):
        for c in range(4):
            if not g[r][c]:
                n = 0
                for v in (1, 2, 3, 4):
                    if _ok(g, r, c, v):
                        g[r][c] = v
                        n += count_solutions(g, limit - n)
                        g[r][c] = 0
                        if n >= limit:
                            return n
                return n
    return 1


def solution(rng: random.Random) -> list[list[int]]:
    digits = [1, 2, 3, 4]; rng.shuffle(digits)
    g = [[digits[v - 1] for v in row] for row in BASE]
    bands = [[0, 1], [2, 3]]; rng.shuffle(bands)
    for b in bands: rng.shuffle(b)
    g = [g[r] for b in bands for r in b]
    stacks = [[0, 1], [2, 3]]; rng.shuffle(stacks)
    for s in stacks: rng.shuffle(s)
    g = [[row[c] for s in stacks for c in s] for row in g]
    return [list(r) for r in zip(*g)] if rng.random() < .5 else g


def make(seed: str, givens: int = GIVENS) -> tuple[list[list[int]], list[list[int]]]:
    """(puzzle with 0 for blanks, solution) for this seed (the edition's ISO date)."""
    rng = random.Random("sudoku-" + seed)
    sol = solution(rng)
    puz = [row[:] for row in sol]
    cells = [(r, c) for r in range(4) for c in range(4)]; rng.shuffle(cells)
    filled = 16
    for r, c in cells:
        if filled <= givens:
            break
        keep, puz[r][c] = puz[r][c], 0
        if count_solutions([row[:] for row in puz]) != 1:
            puz[r][c] = keep
        else:
            filled -= 1
    return puz, sol


def svg(puz: list[list[int]], cell: int = 30) -> str:
    out = []
    for r in range(4):
        for c in range(4):
            x, y = c * cell + 2, r * cell + 2
            out.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="#fff" stroke="#161410" stroke-width="0.8"/>')
            if puz[r][c]:
                out.append(f'<text x="{x + cell / 2}" y="{y + cell * .72}" text-anchor="middle" font-size="{cell * .62:.1f}" '
                           f'font-family="PF,serif" font-weight="700" fill="#161410" style="font-variant-numeric:lining-nums">{puz[r][c]}</text>')
    w = 4 * cell + 4
    out.append(f'<rect x="2" y="2" width="{4 * cell}" height="{4 * cell}" fill="none" stroke="#161410" stroke-width="2.4"/>')
    out.append(f'<path d="M{2 + 2 * cell},2 V{2 + 4 * cell} M2,{2 + 2 * cell} H{2 + 4 * cell}" stroke="#161410" stroke-width="2.4"/>')
    return (f'<svg class="sd-grid" viewBox="0 0 {w} {w}" width="{w}" height="{w}" xmlns="http://www.w3.org/2000/svg" '
            f'role="img" aria-label="sudoku grid">{"".join(out)}</svg>')


HOW_TO = ("<b>How to play:</b> Fill each empty square with 1, 2, 3 or 4. Every row, every column and every thick-lined "
          "box of four squares must have 1, 2, 3 and 4, each one time. <b>Tip:</b> look for a row, column or box with "
          "only one empty square, and fill in the number that's missing.")


def html_box(seed: str, how_to: bool, title: str = "Daily Sudoku") -> str:
    puz, sol = make(seed)
    help_html = f"<p class='sd-how'>{HOW_TO}</p>" if how_to else ""
    key = " / ".join("".join(map(str, row)) for row in sol)
    return (f"<div class='box2 xw sd'><h3 style='margin:0 0 3px'>{title}</h3><div class='xw-body'>{svg(puz)}{help_html}</div>"
            f"<div class='xw-key'>Answer, row by row: {key}</div></div>")


if __name__ == "__main__":
    puz, sol = make(sys.argv[1] if len(sys.argv) > 1 else "2026-10-20")
    for p, s in zip(puz, sol):
        print(" ".join(str(v or ".") for v in p), "   ", " ".join(map(str, s)))
