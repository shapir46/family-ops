# family-ops

Jacob Shapiro's family automation. This is a **private** repo because it holds kids' names, schools, schedules and email conventions. Never copy its contents into a public repo, gist or artifact shared beyond Jacob.

## What runs here
- **Daily, about 6:30 AM America/New_York** (Claude Code routine "Family digest", live since 2026-10-10): run the `family-digest` skill (Steps 1–6), then the `daily-scoop` skill (Step 7), in that order. The scoop reuses the digest's gathered data. The run then commits its log appends, the day's `state/` file, the day's newspaper PDF (`editions/`) and any new lunch-menu URL to `main`. The old Cowork routine is retired (disabled, not deleted).
- Recipients and destinations: the digest goes by Outlook email to jacob@ivanhoecompanies.com and Rebekah.Shapiro@gmail.com, and the scoop goes to the home printer relay.

## Three areas: where every change goes
| You want to… | Command | Changes only |
|---|---|---|
| Add or correct family facts, schedules, calendars, or include/drop rules | `/family-update` | `data/` |
| Change the newspaper's look or content rules | `/newspaper-design` | `scoop/` |
| Change the digest email's layout or wording | `/digest-format` | digest skill, Steps 4–5 |
| Build or change the dashboard | `/dashboard-design` | `dashboard/` |

Family data is shared: all three outputs read it, so a fact is changed once, in `data/`, and never copied into an output. Each folder has its own short `CLAUDE.md`; read it before working there. Jacob's how-to is `docs/HOW-TO-UPDATE.md`.

## Layout
| Path | What |
|---|---|
| `data/` | Family facts, calendars, schedules, lunch URLs: the single source of truth (see `data/CLAUDE.md`) |
| `familyops/`, `./fo` | Collectors, merge/dedupe, validation, CLI. `./fo collect`, `./fo add`, `./fo check-email`, `./fo checked`, `./fo test`. Always use `./fo` or `.venv/bin/python`, never the system `python3`. |
| `state/YYYY-MM-DD.json` | The day's single record that every output renders from |
| `editions/YYYY-MM-DD.pdf` | Every printed newspaper, committed by the daily run; the digest links to today's (private: GitHub sign-in with repo access) |
| `.claude/skills/` | `family-digest` and `daily-scoop` (the daily run), plus the four entry points above |
| `scoop/` | Newspaper kit; `scoop/README.md` holds its standing rules |
| `dashboard/` | Family dashboard (not built yet) |
| `sources.yaml`, `cache/`, `logs/` | Source cadences, cached lunch menus, newspaper logs |
| `docs/` | Plans and history (`architecture-v2.md`, the original Cowork prompt, the Cowork export). Reference only. |

## Hard rules
- **Mail and calendars only through the Microsoft 365 (Outlook) connector.** Never use Gmail, Google Calendar or any other mail connector, for reading or sending.
- **Secrets come from the environment, never the repo:** `RELAY_TOKEN` (print relay), `PLAYMETRICS_ICS_URL` (Elle's soccer feed), `ESPN_S2` / `ESPN_SWID` (ESPN login cookies for Ari's fantasy league), `PAPER_LINK_KEY` (signs the digest's no-login newspaper link; `./fo paper-link` uses it), and `XAI_API_KEY` (Grok illustrations for the newspaper; `scoop/illustrate.py` uses it). Never echo, log, commit or put any of them into a digest, newspaper, artifact or commit message.
- **Never re-transmit a credential URL** found in email (see the link rules in the family-digest skill).
- **Mail filing (Step 6) only after a successful send.** The Outlook `Family-Digest/Processed` folder and the `Digest-First-*` / `Digest-Hold-*` categories are the digest's carry-forward memory. Keep their names and rules exactly as written. **Never delete or move a message that is already in Processed** (Jacob manages that folder; 2026-10-11): the run only files new mail into it.

## Keeping knowledge in the repo
When Jacob confirms a new fact (a new activity, teacher, schedule, correction or preference), record it with the `/family-update` procedure, even when he doesn't type the command. Never keep it only in a session. Daily runs commit their own log appends and newly found lunch-menu URLs directly to `main`.

## Shadow mode (testing changes without affecting the live run)
When a run's prompt says **SHADOW mode**, run both skills with these overrides and nothing else changed:
- **Send:** email the digest to jacob@ivanhoecompanies.com only, subject `[SHADOW] Family Digest — {Month D, YYYY}`.
- **Never email Rebekah in shadow mode**: not as To, Cc or Bcc, not a forward, not a fallback or error notice. Every outbound message in a shadow run goes to jacob@ivanhoecompanies.com alone. Before any send, check the recipient list and stop if it holds anyone else.
- **Step 6:** skip it entirely. Do not add categories, move, or delete any Outlook message. The live run owns the Family-Digest folder.
- **Newspaper:** build it and check it fully, but **do not print**. Deliver the PDF with SendUserFile only.
- **Logs and repo:** do not append to `logs/` and do not commit or push anything. Shadow runs must leave no trace that the live run would see.
- **Run report:** end with the normal run report plus a line on anything in the skills that did not work in this environment (missing tool, blocked host, unset variable).
