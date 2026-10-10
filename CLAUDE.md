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
| `data/bps-calendar-2026-27.md` | Static district calendar (part of the instructions). Sunday School is at Temple Israel (calendar pending); Temple Beth El was dropped 2026-10-10. |
| `data/lunch-menus.yaml` | Monthly BPS lunch PDF URLs |
| `data/schedules/` | Activity schedules Jacob supplies (e.g. Ari's MCE basketball) |
| `scoop/` | Newspaper build kit (build2.py, art.py, render.py, setup.sh, edition.json sample). `scoop/README.md` holds Jacob's standing newspaper rules and overrides the skill. hedcut.py is retired. |
| `logs/` | riddle-log.md and content-log.md, appended by every run |
| `docs/original-routine-prompt-2026-10-10.md` | The Cowork routine prompt this repo was split from (secrets redacted). Reference only. |
| `docs/cowork-export/` | Verbatim export of the Cowork project docs and family-related memory as of 2026-10-10, with `MANIFEST.sha256`. Reference only; edit the working copies instead. Historical: its Temple Beth El material no longer applies. |

## v2 toolkit (in progress; see docs/architecture-v2.md)
The `familyops/` package does the mechanical work, so the model doesn't have to:
| Path | What |
|---|---|
| `sources.yaml` | Every source with its cadence (daily / weekly / monthly / yearly), who fetches it, and when it goes stale |
| `data/family.yaml` | Kids' grades, colors, initials, audiences; GSRP half-day rule |
| `data/calendars/*.yaml` | BPS calendar as data (tests prove it matches the prose original); Temple Israel's goes here when supplied |
| `data/schedules/*.yaml` | League schedules as data (keep in sync with the `.md` copies) |
| `data/lunch-menus.yaml` | Lunch PDF URLs per month; new months are found and added automatically |
| `cache/` | Parsed lunch months, source check dates |
| `state/YYYY-MM-DD.json` | The day's single record: events, actions, FYI, lunch, weather, conflicts, due checks, delivery flags |

Commands (`./fo ...` from the repo root). `./fo` uses the repo's own `.venv`, created by `scripts/bootstrap.sh`, which a SessionStart hook runs. Never use the system `python3` for this code: it can lack packages or ship a broken `cryptography`.
- `collect [--date D]`: PlayMetrics, league schedules, the district calendar, lunch and weather go into the state file. Prints source health, warnings, and which weekly/yearly checks are due.
- `add --events f.json [--actions f.json] [--fyi f.json]`: merges the Outlook calendar events and email items Claude gathered. Duplicates merge, and the scripted sources keep priority.
- `check-email --html f.html --to a,b [--shadow]`: pre-send validation (weekday/date pairs, bus/SACC, credential URLs, secrets, recipients, allowed HTML). A non-zero exit means do not send.
- `checked <source>`: record that a weekly/yearly source was re-checked.
- Tests: `./fo test`. Run them before pushing any change to `familyops/` or `data/`.
- Python for anything else, including the newspaper's build2.py and render.py: `.venv/bin/python` (or `./fo python ...`).

## Hard rules
- **Mail and calendars only through the Microsoft 365 (Outlook) connector.** Never use Gmail, Google Calendar or any other mail connector, for reading or sending.
- **Secrets come from the environment, never the repo:** `RELAY_TOKEN` (print relay) and `PLAYMETRICS_ICS_URL` (Elle's soccer feed). Never echo, log, commit or put either into a digest, newspaper, artifact or commit message.
- **Never re-transmit a credential URL** found in email (see the link rules in the family-digest skill).
- **Mail filing (Step 6) only after a successful send.** The Outlook `Family-Digest/Processed` folder and the `Digest-First-*` / `Digest-Hold-*` categories are the digest's carry-forward memory. Keep their names and rules exactly as written.

## Keeping knowledge in the repo
When Jacob confirms a new fact (a new activity, teacher, schedule, correction or preference), write it into the right `data/` file or skill, with the date and source, then commit and push to `main`. Never keep it only in a session. Runs commit their own log appends and newly found lunch-menu URLs directly to `main`.

## Shadow mode (migration testing)
When a run's prompt says **SHADOW mode**, run both skills with these overrides and nothing else changed:
- **Send:** email the digest to jacob@ivanhoecompanies.com only, subject `[SHADOW] Family Digest — {Month D, YYYY}`.
- **Never email Rebekah in shadow mode**: not as To, Cc or Bcc, not a forward, not a fallback or error notice. Every outbound message in a shadow run goes to jacob@ivanhoecompanies.com alone. Before any send, check the recipient list and stop if it holds anyone else.
- **Step 6:** skip it entirely. Do not add categories, move, or delete any Outlook message. The live Cowork routine still owns the Family-Digest folder.
- **Newspaper:** build it and check it fully, but **do not print**. Deliver the PDF with SendUserFile only.
- **Logs and repo:** do not append to `logs/` and do not commit or push anything. Shadow runs must leave no trace that the live run would see.
- **Run report:** end with the normal run report plus a line on anything in the skills that did not work in this environment (missing tool, blocked host, unset variable).
