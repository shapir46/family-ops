# family-ops

Jacob Shapiro's family automation. This is a **private** repo because it holds kids' names, schools, schedules and email conventions. Never copy its contents into a public repo, gist or artifact shared beyond Jacob.

## What runs here
- **Daily, 6:30 AM America/New_York:** run the `family-digest` skill (Steps 1–6), then the `daily-scoop` skill (Step 7), in that order. The scoop reuses the digest's gathered data.
- Recipients and destinations: the digest goes by Outlook email to jacob@ivanhoecompanies.com and Rebekah.Shapiro@gmail.com, and the scoop goes to the home printer relay.

## Layout
| Path | What |
|---|---|
| `.claude/skills/family-digest/SKILL.md` | Steps 1–6 and the run report |
| `.claude/skills/daily-scoop/SKILL.md` | Step 7: the Fairfax Daily Scoop |
| `data/family.md` | Established child facts, attribution rules, bus/SACC exclusion |
| `data/bps-calendar-2026-27.md`, `data/tbe-religious-school-2026-27.md` | Static calendars (part of the instructions) |
| `data/lunch-menus.md` | Monthly BPS lunch PDF URLs |
| `data/schedules/` | Activity schedules Jacob supplies (e.g. Ari's MCE basketball) |
| `scoop/` | Newspaper build kit (build2.py, art.py, render.py, setup.sh, edition.json sample). `scoop/README.md` holds Jacob's standing newspaper rules and overrides the skill. hedcut.py is retired. |
| `logs/` | riddle-log.md and content-log.md, appended by every run |
| `docs/original-routine-prompt-2026-10-10.md` | The Cowork routine prompt this repo was split from (secrets redacted). Reference only. |
| `docs/cowork-export/` | Verbatim export of the Cowork project docs and family-related memory as of 2026-10-10, with `MANIFEST.sha256`. Reference only; edit the working copies instead. |

## Hard rules
- **Mail and calendars only through the Microsoft 365 (Outlook) connector.** Never use Gmail, Google Calendar or any other mail connector, for reading or sending.
- **Secrets come from the environment, never the repo:** `RELAY_TOKEN` (print relay) and `PLAYMETRICS_ICS_URL` (Elle's soccer feed). Never echo, log, commit or put either into a digest, newspaper, artifact or commit message.
- **Never re-transmit a credential URL** found in email (see the link rules in the family-digest skill).
- **Mail filing (Step 6) only after a successful send.** The Outlook `Family-Digest/Processed` folder and the `Digest-First-*` / `Digest-Hold-*` categories are the digest's carry-forward memory. Keep their names and rules exactly as written.

## Keeping knowledge in the repo
When Jacob confirms a new fact (a new activity, teacher, schedule, correction or preference), write it into the right `data/` file or skill, with the date and source, then commit and push to `main`. Never keep it only in a session. Runs commit their own log appends and newly found lunch-menu URLs directly to `main`.

## Shadow mode (migration testing)
When a run's prompt says **SHADOW mode**, run both skills with these overrides and nothing else changed:
- **Send:** email the digest to jacob@ivanhoecompanies.com only (not Rebekah), subject `[SHADOW] Family Digest — {Month D, YYYY}`.
- **Step 6:** skip it entirely. Do not add categories, move, or delete any Outlook message. The live Cowork routine still owns the Family-Digest folder.
- **Newspaper:** build it and check it fully, but **do not print**. Deliver the PDF with SendUserFile only.
- **Logs and repo:** do not append to `logs/` and do not commit or push anything. Shadow runs must leave no trace that the live run would see.
- **Run report:** end with the normal run report plus a line on anything in the skills that did not work in this environment (missing tool, blocked host, unset variable).
