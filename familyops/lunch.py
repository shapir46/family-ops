"""BPS elementary lunch menu (Bingham Farms, Greenfield, Pierce, Quarton): monthly PDF -> {day: entree}.

Parsed by word position, not text order: column bounds come from the weekday header, rows from the
day numbers, and each cell's words are read top to bottom. Results are cached per month in cache/.
"""
from __future__ import annotations

import io
import json
import re
from datetime import date

import pdfplumber
import requests
import yaml

from . import ROOT

MENUS_PAGE = "https://www.birmingham.k12.mi.us/programs-services/food-services/menus"
CACHE = ROOT / "cache"
URLS = ROOT / "data/lunch-menus.yaml"
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
HALF = re.compile(r"½\s*DAY|1/2\s*DAY", re.I)
NO_SCHOOL = re.compile(r"NO\s+SCHOOL", re.I)


def parse_pdf(data: bytes) -> dict:
    """{'month': 'October', 'days': {'1': {...}}}. Each day: entree (str|None), half_day, no_school, theme."""
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        page = pdf.pages[0]
        words = page.extract_words(keep_blank_chars=False, use_text_flow=False, x_tolerance=1.5)
        text = page.extract_text() or ""
    month = next((m for m in ["January", "February", "March", "April", "May", "June", "July", "August",
                              "September", "October", "November", "December"] if f"{m} Elementary" in text
                  or re.search(rf"\b{m}\b", text[:300])), None)
    header = {}
    for w in sorted(words, key=lambda w: w["top"]):  # topmost occurrence: menu text can say "Friday" too
        if w["text"] in DAYS and w["text"] not in header:
            header[w["text"]] = w
    if len(header) < 5:
        raise ValueError("weekday header not found")
    header_y = max(w["bottom"] for w in header.values())
    centers = [(header[d]["x0"] + header[d]["x1"]) / 2 for d in DAYS]
    bounds = [0] + [(centers[i] + centers[i + 1]) / 2 for i in range(4)] + [page.width]
    stop_y = min((w["top"] for w in words if w["text"] == "Cold" and w["top"] > header_y), default=page.height)

    def col(x):
        return next(i for i in range(5) if bounds[i] <= x < bounds[i + 1])

    # Day numbers: a 1-2 digit token, optionally glued to a #theme ("5#BrunchforLunch"), at the top-left of a cell.
    nums = []
    for w in words:
        m = re.match(r"^(\d{1,2})(#\w+)?$", w["text"])
        if m and header_y < w["top"] < stop_y and 1 <= int(m.group(1)) <= 31:
            nums.append({"day": int(m.group(1)), "col": col(w["x0"]), "top": w["top"], "x0": w["x0"], "w": w,
                         "theme": m.group(2)})
    # Keep only numbers that lead a cell: smallest-x token in its column for that row band.
    nums.sort(key=lambda n: (n["top"], n["x0"]))
    row_tops = sorted({round(n["top"]) for n in nums})
    rows = []
    for t in row_tops:
        if not rows or t - rows[-1] > 20:
            rows.append(t)
    cells = {}
    for n in nums:
        r = min(range(len(rows)), key=lambda i: abs(rows[i] - n["top"]))
        key = (r, n["col"])
        if key not in cells or n["x0"] < cells[key]["x0"]:
            cells[key] = {**n, "row": r}
    days = {}
    for (r, c), n in cells.items():
        y0 = rows[r] - 2
        y1 = rows[r + 1] - 2 if r + 1 < len(rows) else stop_y
        cw = [w for w in words if y0 <= w["top"] < y1 and bounds[c] <= (w["x0"] + w["x1"]) / 2 < bounds[c + 1]
              and w is not n["w"]]
        cw.sort(key=lambda w: (round(w["top"] / 3), w["x0"]))
        txt = " ".join(w["text"] for w in cw)
        txt = re.sub(r"\s+", " ", txt).strip()
        theme = (n["theme"] or "").lstrip("#") or None
        if not theme and (m := re.match(r"^(#\w+)\s*", txt)):
            theme, txt = m.group(1).lstrip("#"), txt[m.end():]
        half = bool(HALF.search(txt))
        closed = bool(NO_SCHOOL.search(txt))
        entree = None if (half or closed) else _tidy(txt)
        days[str(n["day"])] = {"weekday": DAYS[c], "entree": entree, "half_day": half, "no_school": closed,
                               "theme": theme}
    return {"month": month, "days": dict(sorted(days.items(), key=lambda kv: int(kv[0])))}


def _tidy(t: str) -> str | None:
    t = re.sub(r"\b(Day!!|Day!)\s*", lambda m: m.group(0), t)
    t = re.sub(r"\s+([,.])", r"\1", t).strip(" ,")
    return t or None


def check(parsed: dict, year: int, month: int) -> list[str]:
    """Sanity checks: weekday of each day number matches the real calendar; Wednesdays are pizza."""
    problems = []
    for d, v in parsed["days"].items():
        real = date(year, month, int(d)).strftime("%A")
        if real != v["weekday"]:
            problems.append(f"day {d}: grid column {v['weekday']} but {real} on the calendar")
        if real == "Wednesday" and v["entree"] and "pizza" not in v["entree"].lower():
            problems.append(f"day {d}: Wednesday without pizza ({v['entree'][:40]})")
    return problems


def known_url(year: int, month: int) -> str | None:
    urls = yaml.safe_load(URLS.read_text()) or {}
    return (urls.get("menus") or {}).get(f"{year}-{month:02d}")


def find_url(year: int, month: int) -> str | None:
    """This month's Quarton elementary menu PDF on the BPS menus page. The page lists several elementary
    menus (e.g. a Wednesday-pizza and a Thursday group), so each candidate is opened and only one whose
    header names Quarton is accepted."""
    name = date(year, month, 1).strftime("%B")
    html = requests.get(MENUS_PAGE, timeout=30).text
    links = list(dict.fromkeys(re.findall(r'href="(https?://[^"]+\.pdf)"', html, re.I)))
    tags = {name.lower(), name[:3].lower(), name[:4].lower()}
    cands = [u for u in links if "ele" in u.lower().rsplit("/", 1)[-1]
             and any(t in u.lower().rsplit("/", 1)[-1] for t in tags)]
    for u in cands:
        try:
            data = requests.get(u, timeout=60).content
            with pdfplumber.open(io.BytesIO(data)) as pdf:
                head = (pdf.pages[0].extract_text() or "")[:400]
        except Exception:  # noqa: BLE001 - try the next candidate
            continue
        if "Quarton" in head and name in head:
            return u
    return None


def remember_url(year: int, month: int, url: str) -> None:
    """Record a newly found month in data/lunch-menus.yaml (the run commits it)."""
    doc = yaml.safe_load(URLS.read_text()) or {}
    doc.setdefault("menus", {})[f"{year}-{month:02d}"] = url
    URLS.write_text("# BPS elementary lunch menu PDFs (Bingham Farms, Greenfield, Pierce, Quarton). One per month.\n"
                    "# The daily run finds a missing month on the BPS menus page, adds it here and commits.\n"
                    + yaml.safe_dump(doc, sort_keys=False))


def month_menu(year: int, month: int, refresh: bool = False) -> dict:
    """Cached parse for a month; fetches and parses the PDF when missing or `refresh`."""
    CACHE.mkdir(exist_ok=True)
    path = CACHE / f"lunch-{year}-{month:02d}.json"
    if path.exists() and not refresh:
        return json.loads(path.read_text())
    url = known_url(year, month)
    if not url:
        url = find_url(year, month)
        if not url:
            raise LookupError(f"no lunch menu PDF found for {year}-{month:02d}")
        remember_url(year, month, url)
    data = requests.get(url, timeout=60).content
    parsed = parse_pdf(data)
    parsed.update({"url": url, "year": year, "month_num": month, "problems": check(parsed, year, month)})
    path.write_text(json.dumps(parsed, indent=1))
    return parsed


def for_day(d: date) -> dict:
    """{'line': str, 'source': ..., 'problems': [...]} for the digest/newspaper lunch line."""
    if d.weekday() >= 5:
        return {"line": "No school today.", "entree": None}
    try:
        m = month_menu(d.year, d.month)
    except Exception as e:  # noqa: BLE001 - reported, never guessed
        return {"line": f"Lunch menu: source needs updating for {d:%B}.", "entree": None, "error": str(e)}
    cell = m["days"].get(str(d.day))
    if cell is None:
        return {"line": "Lunch menu: today's cell could not be read.", "entree": None}
    if cell["no_school"]:
        return {"line": "No school today.", "entree": None}
    if cell["half_day"]:
        return {"line": "Half day, no lunch served.", "entree": None, "half_day": True}
    return {"line": cell["entree"], "entree": cell["entree"], "theme": cell.get("theme"),
            "problems": m.get("problems", [])}
