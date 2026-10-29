"""Daily Sudoku: a kids' sudoku that alternates with the crossword (Jacob, 2026-10-19).

The puzzle is made from the edition's date (same date, same puzzle), so the daily run writes nothing for it. Every
puzzle is checked to have exactly one solution.
- 4x4 (Oct 20-29, 2026): rows, columns and the four 2x2 boxes each hold 1-4.
- 5x5 (from Oct 31, 2026; Jacob, 2026-10-29): rows, columns and five thick-outlined shapes of five squares (made
  fresh from the date, each lightly tinted) each hold 1-5.

  python sudoku.py 2026-10-20 [5]      print that day's puzzle and answer (5 = the 5x5 kind)
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


# ---------------------------------------------------------------- 5x5 with shaped regions (Jacob, 2026-10-29)
GIVENS5 = 10      # of 25 squares
TINTS = ['#fdf0d5', '#e2effa', '#e5f4de', '#f8e3ee', '#ece6fa']


def _regions5(rng: random.Random) -> list[list[int]]:
    """Five connected shapes of five squares covering the 5x5 grid (region number per square); no shape is a
    straight row or column."""
    while True:
        reg = [[-1] * 5 for _ in range(5)]
        sizes = [0] * 5
        for k, (r, c) in enumerate(rng.sample([(r, c) for r in range(5) for c in range(5)], 5)):
            reg[r][c], sizes[k] = k, 1
        stuck = False
        while min(sizes) < 5 and not stuck:
            k = min(range(5), key=lambda k: (sizes[k], rng.random()))
            nb = [(r + dr, c + dc) for r in range(5) for c in range(5) if reg[r][c] == k
                  for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                  if 0 <= r + dr < 5 and 0 <= c + dc < 5 and reg[r + dr][c + dc] == -1]
            if not nb:
                stuck = True
                break
            r, c = rng.choice(nb)
            reg[r][c] = k; sizes[k] += 1
        if stuck:
            continue
        cells = lambda k: [(r, c) for r in range(5) for c in range(5) if reg[r][c] == k]
        if any(len({r for r, _ in cells(k)}) == 1 or len({c for _, c in cells(k)}) == 1 for k in range(5)):
            continue
        return reg


def _ok5(g, reg, r, c, v) -> bool:
    return (v not in g[r] and all(g[i][c] != v for i in range(5))
            and all(g[i][j] != v for i in range(5) for j in range(5) if reg[i][j] == reg[r][c]))


def _count5(g, reg, limit: int = 2, rng: random.Random | None = None, out: list | None = None) -> int:
    for r in range(5):
        for c in range(5):
            if not g[r][c]:
                n, vals = 0, [1, 2, 3, 4, 5]
                if rng: rng.shuffle(vals)
                for v in vals:
                    if _ok5(g, reg, r, c, v):
                        g[r][c] = v
                        n += _count5(g, reg, limit - n, rng, out)
                        g[r][c] = 0
                        if n >= limit:
                            return n
                return n
    if out is not None and not out:
        out.append([row[:] for row in g])
    return 1


def make5(seed: str, givens: int = GIVENS5):
    """(puzzle with 0 for blanks, solution, regions) for this seed (the edition's ISO date)."""
    rng = random.Random("sudoku5-" + seed)
    while True:
        reg = _regions5(rng)
        found = []
        _count5([[0] * 5 for _ in range(5)], reg, 1, rng, found)
        if found:
            break
    sol = found[0]
    puz = [row[:] for row in sol]
    cells = [(r, c) for r in range(5) for c in range(5)]; rng.shuffle(cells)
    filled = 25
    for r, c in cells:
        if filled <= givens:
            break
        keep, puz[r][c] = puz[r][c], 0
        if _count5([row[:] for row in puz], reg) != 1:
            puz[r][c] = keep
        else:
            filled -= 1
    return puz, sol, reg


def svg5(puz, reg, cell: int = 30) -> str:
    out, o = [], 2
    for r in range(5):
        for c in range(5):
            x, y = c * cell + o, r * cell + o
            out.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="{TINTS[reg[r][c]]}" stroke="#8a8a8a" stroke-width="0.6"/>')
            if puz[r][c]:
                out.append(f'<text x="{x + cell / 2}" y="{y + cell * .72}" text-anchor="middle" font-size="{cell * .62:.1f}" '
                           f'font-family="PF,serif" font-weight="700" fill="#161410" style="font-variant-numeric:lining-nums">{puz[r][c]}</text>')
    walls = []
    for r in range(5):
        for c in range(5):
            x, y = c * cell + o, r * cell + o
            if c < 4 and reg[r][c] != reg[r][c + 1]: walls.append(f'M{x + cell},{y} V{y + cell}')
            if r < 4 and reg[r][c] != reg[r + 1][c]: walls.append(f'M{x},{y + cell} H{x + cell}')
    out.append(f'<path d="{" ".join(walls)}" stroke="#161410" stroke-width="2.4" stroke-linecap="square" fill="none"/>')
    out.append(f'<rect x="{o}" y="{o}" width="{5 * cell}" height="{5 * cell}" fill="none" stroke="#161410" stroke-width="2.4"/>')
    w = 5 * cell + 2 * o
    return (f'<svg class="sd-grid" viewBox="0 0 {w} {w}" width="{w}" height="{w}" xmlns="http://www.w3.org/2000/svg" '
            f'role="img" aria-label="sudoku grid">{"".join(out)}</svg>')


HOW_TO5 = ("<b>How to play:</b> Fill each empty square with 1, 2, 3, 4 or 5. Every row, every column and every "
           "thick-outlined shape of five squares must have 1, 2, 3, 4 and 5, each one time. <b>Tip:</b> look for a row, "
           "column or shape with only one empty square, and fill in the number that's missing.")


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


def html_box(seed: str, how_to: bool, title: str = "Daily Sudoku", size: int = 4) -> str:
    if size == 5:
        puz, sol, reg = make5(seed)
        grid, how = svg5(puz, reg), HOW_TO5
    else:
        puz, sol = make(seed)
        grid, how = svg(puz), HOW_TO
    help_html = f"<p class='sd-how'>{how}</p>" if how_to else ""
    key = " / ".join("".join(map(str, row)) for row in sol)
    return (f"<div class='box2 xw sd'><h3 style='margin:0 0 3px'>{title}</h3><div class='xw-body'>{grid}{help_html}</div>"
            f"<div class='xw-key'>Answer, row by row: {key}</div></div>")


if __name__ == "__main__":
    seed = sys.argv[1] if len(sys.argv) > 1 else "2026-10-20"
    if len(sys.argv) > 2 and sys.argv[2] == "5":
        puz, sol, reg = make5(seed)
        for p, s, g in zip(puz, sol, reg):
            print(" ".join(str(v or ".") for v in p), "   ", " ".join(map(str, s)), "   ", " ".join("ABCDE"[k] for k in g))
    else:
        puz, sol = make(seed)
        for p, s in zip(puz, sol):
            print(" ".join(str(v or ".") for v in p), "   ", " ".join(map(str, s)))
