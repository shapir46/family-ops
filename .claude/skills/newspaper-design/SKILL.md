---
name: newspaper-design
description: Change how the Fairfax Daily Scoop looks or what kind of content it carries (layout, graphics, fonts, colors, sections, comic, puzzles, story rules, sports rules). Use for any newspaper format or design request. Works only in scoop/; family facts are never edited here.
---

# Newspaper design

Scope: `scoop/` only. Read `scoop/CLAUDE.md`, then `scoop/README.md`, which holds the standing rules. The newspaper's family content (schedule, lunch, school notes) comes from the day's `state/*.json`; to change those facts, use `/family-update` instead.

## Steps
1. **Restate the request** in one line as a rule or a design change.
2. **Content rules** (what goes in, sources, what never to print) → edit `scoop/README.md`, under "Standing requests" or "NEW STANDING RULES", dated `(Jacob, YYYY-MM-DD)`.
3. **Layout and graphics** → `build2.py` (page structure, CSS), `art.py` (comic and original SVG art), `render.py` (PDF output only).
   - Kid colors and initials come from `data/family.yaml` (shared with the dashboard and the email). Don't hard-code new ones.
   - Keep everything original. No third-party characters or logos.
4. **Preview before committing:**
   - Copy `scoop/` to the scratchpad and build with `scoop/edition.json`, or with today's state if it exists: `FONTDIR=./fonts ../.venv/bin/python build2.py && ../.venv/bin/python render.py newspaper.pdf` (run `sh setup.sh` first for fonts).
   - Must be exactly 1 page, and every column's content must be ≤ its bottom.
   - Render a PNG (`pdftoppm -r 100 -png`) and look at it.
   - Send Jacob the PNG with SendUserFile and a one-line summary.
5. If `edition.json` gains or loses a field, update the field list in `scoop/README.md` and the sample `edition.json` together.
6. Commit and push to `main`. The daily run uses the new design the next morning. Never print a preview.
