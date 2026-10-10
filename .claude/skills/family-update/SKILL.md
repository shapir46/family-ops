---
name: family-update
description: Record a change to the family's facts or schedules (a new activity, teacher, schedule, calendar, school change, correction, or a rule about what the digest should include or drop). Use whenever Jacob gives family information, sends a calendar/schedule PDF or photo, or corrects something the digest got wrong. Writes only to data/, runs the checks, commits, and every output picks it up on its next run.
---

# Family update

Family data is the single source of truth for every output: the digest email, the newspaper and the dashboard. It lives only in `data/`. Never put a family fact into a routine prompt, the newspaper kit, or the dashboard code. Read `data/CLAUDE.md` first: it says which file holds what.

## Steps
1. **Classify each item** in Jacob's message (he may send several at once):
   - fact about a person: kid, grade, teacher, room, school, congregation → `data/family.yaml`, plus the prose in `data/family.md` when the rule needs words
   - recurring activity or league schedule → `data/schedules/<kid>-<activity>-<season>.yaml`
   - a school/congregation year calendar (district, Sunday School) → `data/calendars/<name>-YYYY-YY.yaml`
   - a rule about what to include, drop or attribute ("drop X", "Y is Elle's") → `data/family.md`
   - a lunch-menu URL → `data/lunch-menus.yaml`
   - anything about layout or wording of an output → not data: say which command to use instead (`/newspaper-design`, `/digest-format`, `/dashboard-design`)
2. **From a PDF or photo:** extract every dated entry. Keep Jacob's source wording in a `label`/`notes` field. Do not summarize away details.
3. **Every entry gets a date and a source:** `(Jacob, YYYY-MM-DD)` or the document name.
4. **Check before saving:**
   - every weekday/date pair (`./fo python -c "from familyops import validate; ..."` or a test)
   - no overlap with existing data you'd be contradicting; if you would, say so
   - anything ambiguous, such as which kid, a missing year, or a time range: ask ONE short question, but still save the unambiguous parts
5. **Removing something** (a school, team or activity that ended): delete the data file or entry and every rule that refers to it, so nothing stale lingers. Archives under `docs/` stay as history.
6. `./fo test` must pass. Then run `./fo collect --no-save` and confirm the change shows up (or stops showing up).
7. **Commit and push to `main`.** The message says what changed and who confirmed it.
8. **Transition (until the Cowork routine is retired):** if the change affects what the live digest shows, also apply it to the live Cowork routine prompt (`trig_01TDs2yyMLWr9tB7RWYJuDob`). Read the current prompt, edit it with a script, send it back, and verify the stored prompt matches byte for byte. Delete this step at cutover.
9. **Reply in 2–4 lines:** what changed, where it lives, and that it takes effect on the next morning run. If you asked a question, put it last.
