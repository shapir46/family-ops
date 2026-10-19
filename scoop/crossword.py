"""Daily Crossword: a small kids' crossword built from 4-5 answers about the day's paper (Jacob, 2026-10-19).

The daily run supplies only the words and clues (edition.json `crossword`); this module finds a connected grid in
which every word crosses at least one other, numbers it, and draws it as inline SVG. A layout is valid only when
words touch nothing but their crossings (no stray two-letter runs), so the printed puzzle always has one answer.

  python crossword.py PUMPKIN JUICE ROCKET SHARE    try a word list and print the grid
"""
from __future__ import annotations

import html
import re
import sys

ACROSS, DOWN = (0, 1), (1, 0)   # (row step, col step) is (0, 1) for across


def clean(word: str) -> str:
    return re.sub(r"[^A-Z]", "", word.upper())


def _fits(grid: dict, word: str, r: int, c: int, d: tuple) -> int | None:
    """Number of crossings if `word` can go at (r, c) in direction d, else None."""
    dr, dc = d
    if grid.get((r - dr, c - dc)) or grid.get((r + dr * len(word), c + dc * len(word))):
        return None                                    # must not run into another word end-to-end
    crossings = 0
    for i, ch in enumerate(word):
        p = (r + dr * i, c + dc * i)
        have = grid.get(p)
        if have:
            if have != ch:
                return None
            crossings += 1
            continue
        side1, side2 = (p[0] + dc, p[1] + dr), (p[0] - dc, p[1] - dr)   # the perpendicular neighbours
        if grid.get(side1) or grid.get(side2):
            return None
    return crossings


def _place(grid: dict, word: str, r: int, c: int, d: tuple) -> dict:
    g = dict(grid)
    for i, ch in enumerate(word):
        g[(r + d[0] * i, c + d[1] * i)] = ch
    return g


def _candidates(grid: dict, placed: list, word: str):
    seen = set()
    for (pr, pc), ch in list(grid.items()):
        for i, wch in enumerate(word):
            if wch != ch:
                continue
            for d in (ACROSS, DOWN):
                # the existing letter at (pr, pc) must belong to a word running the other way
                if any(pd == d and _covers(pw, prr, pcc, pd, pr, pc) for pw, prr, pcc, pd in placed):
                    continue
                r, c = pr - d[0] * i, pc - d[1] * i
                if (r, c, d) in seen:
                    continue
                seen.add((r, c, d))
                if _fits(grid, word, r, c, d):
                    yield r, c, d


def _covers(word, r, c, d, pr, pc) -> bool:
    return any((r + d[0] * i, c + d[1] * i) == (pr, pc) for i in range(len(word)))


def _area(grid: dict) -> tuple:
    rs = [p[0] for p in grid]; cs = [p[1] for p in grid]
    h, w = max(rs) - min(rs) + 1, max(cs) - min(cs) + 1
    return (max(h, w), h * w)


def layout(words: list[str], max_side: int = 11) -> list[tuple] | None:
    """[(word, row, col, dir)] with the top-left cell at (0, 0), every word crossing another; None if impossible."""
    order = sorted(dict.fromkeys(words), key=len, reverse=True)
    best = None

    def search(grid, placed, rest):
        nonlocal best
        if best and _area(grid) >= _area(best[0]):
            return
        if not rest:
            best = (grid, placed)
            return
        for k, w in enumerate(rest):
            for r, c, d in _candidates(grid, placed, w):
                g = _place(grid, w, r, c, d)
                if _area(g)[0] <= max_side:
                    search(g, placed + [(w, r, c, d)], rest[:k] + rest[k + 1:])

    first = order[0]
    search(_place({}, first, 0, 0, ACROSS), [(first, 0, 0, ACROSS)], order[1:])
    if not best:
        return None
    grid, placed = best
    r0, c0 = min(p[0] for p in grid), min(p[1] for p in grid)
    return [(w, r - r0, c - c0, d) for w, r, c, d in placed]


def build(entries: list) -> dict:
    """entries: [[answer, clue], ...] -> {'svg', 'across', 'down', 'answers'} or {'error'}."""
    if not 4 <= len(entries) <= 5:
        return {"error": f"needs 4-5 words, got {len(entries)}"}
    clues = {}
    for ans, clue in entries:
        w = clean(ans)
        if not 3 <= len(w) <= 9:
            return {"error": f"'{ans}': answers are 3-9 letters"}
        clues[w] = clue
    if len(clues) != len(entries):
        return {"error": "repeated answer"}
    placed = layout(list(clues))
    if not placed:
        return {"error": "these words don't all cross; swap one for a word sharing letters with the others"}
    starts = sorted({(r, c) for _, r, c, _ in placed})
    num = {p: i + 1 for i, p in enumerate(starts)}
    across = sorted((num[(r, c)], clues[w]) for w, r, c, d in placed if d == ACROSS)
    down = sorted((num[(r, c)], clues[w]) for w, r, c, d in placed if d == DOWN)
    cells = {}
    for w, r, c, d in placed:
        for i, ch in enumerate(w):
            cells[(r + d[0] * i, c + d[1] * i)] = ch
    rows, cols = max(p[0] for p in cells) + 1, max(p[1] for p in cells) + 1
    return {"cells": cells, "num": num, "rows": rows, "cols": cols, "across": across, "down": down,
            "answers": [(num[(r, c)], "Across" if d == ACROSS else "Down", w) for w, r, c, d in
                        sorted(placed, key=lambda p: (num[(p[1], p[2])], p[3] == DOWN))]}


def svg(puzzle: dict, cell: int = 24) -> str:
    out = []
    for (r, c), _ in puzzle["cells"].items():
        x, y = c * cell + 1, r * cell + 1
        out.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="#fff" stroke="#161410" stroke-width="1.2"/>')
        if (r, c) in puzzle["num"]:
            out.append(f'<text x="{x + 1.8}" y="{y + 7.6}" font-size="7.5" font-family="LB,serif" fill="#161410">{puzzle["num"][(r, c)]}</text>')
    w, h = puzzle["cols"] * cell + 2, puzzle["rows"] * cell + 2
    return (f'<svg class="xw-grid" viewBox="0 0 {w} {h}" width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg" '
            f'role="img" aria-label="crossword grid">{"".join(out)}</svg>')


def html_box(spec: dict) -> tuple[str, str | None]:
    """(HTML for the Daily Crossword box, warning or None)."""
    p = build(spec.get("words") or [])
    if "error" in p:
        return "", f"CROSSWORD WARNING: {p['error']} (the crossword is left out)"
    cl = lambda xs: "".join(f"<li><b>{n}</b> {html.escape(t, quote=False)}</li>" for n, t in xs)
    key = " · ".join(f"{n} {d[0]}: {w}" for n, d, w in p["answers"])
    return (f"<div class='box2 xw'><h3 style='margin:0 0 3px'>{spec.get('title', 'Daily Crossword')}</h3>"
            f"<div class='xw-body'>{svg(p)}<div class='xw-clues'>"
            + (f"<div class='xw-h'>Across</div><ul class='xw-list'>{cl(p['across'])}</ul>" if p["across"] else "")
            + (f"<div class='xw-h'>Down</div><ul class='xw-list'>{cl(p['down'])}</ul>" if p["down"] else "")
            + f"</div></div><div class='xw-key'>Answers: {key}</div></div>"), None


if __name__ == "__main__":
    p = build([[w, "?"] for w in sys.argv[1:]])
    if "error" in p:
        sys.exit(p["error"])
    for r in range(p["rows"]):
        print(" ".join(p["cells"].get((r, c), ".") for c in range(p["cols"])))
    print(p["answers"])
