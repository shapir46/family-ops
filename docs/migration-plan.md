# Family Digest + Fairfax Daily Scoop: move to Claude Code

Status: plan only. Nothing has changed yet. The current routine is still live and runs tomorrow at 6:30 AM ET.

## 1. What exists today (inventory)

**Routine:** "Family digest" (`trig_01TDs2yyMLWr9tB7RWYJuDob`)
- Schedule: daily 6:30 AM America/New_York. Runs as a **Cowork remote** session on Sonnet 5.5 in auto mode.
- Bound to Claude project `01a016c3-…` and gets that project's files and memory.
- Last run (Oct 10) succeeded in about 12 minutes. It cost about **$6.49** and used 367K tokens of context.
- Connectors attached: Microsoft_365, Google_Drive, Plaud, Slack, Docusign, Resy, Uber_Eats, Claude_Code_Remote. **Only Microsoft_365 is actually used.**
- The prompt is about 50 KB and is saved as `family-digest-prompt.md`, with the token redacted.

**What the prompt does:**

| Step | Work | Depends on |
|---|---|---|
| 1a / 1b | Read the Outlook `Family-Digest` folder and carried-forward mail in `Processed` | M365 `outlook_email_search`, `read_resource`, subagents |
| 2 | Search 6 Outlook calendars (default, Family, Ari, Elle, Lila, Leo) | M365 `outlook_calendar_search` |
| 2b | Read the PlayMetrics ICS feed (Elle, U9G Black) | WebFetch, plus an **ICS URL that is a credential** |
| 2c / 2c-ii | BPS 2026-27 calendar and TBE Religious School calendar | Static tables inside the prompt |
| 3–4 | Parse, dedupe and build the 4-section mobile HTML | Many rules (bus/SACC exclusion, child attribution, link and credential rules) |
| Lunch | Monthly BPS PDF | Hard-coded URL per month that Jacob edits by hand each month |
| 5 | Email to Jacob and Rebekah | `outlook_send_mail`; Artifact as fallback |
| 6 | Tag and move mail to Processed, purge expired mail | `outlook_batch_modify_labels`, `outlook_batch_delete_messages` |
| 7 | Build and print the Fairfax Daily Scoop | Project files, NWS, sports sites, maxpreps, **curl to print.jacobshapiro.net** with `RELAY_TOKEN` |

**State that lives OUTSIDE the prompt. This is where things get lost.**
1. **Cowork project files (Projects tool, `claude/fairfax-scoop/`):** build2.py, art.py, hedcut.py, render.py, setup.sh, edition.json, README.md, riddle-log.md, plus a **content log** ("Fairfax Daily Scoop — content log (never repeat anything below)").
2. **Ari's MCE basketball schedule.** Jacob uploaded the PDF in a run session on Oct 10, and it was saved as a project doc. Other facts told to Claude in run sessions may also be in project docs or memory.
3. **Project memory** (the session has `post-turn-memory`): outlook-operating-instructions.md, overview.md, profile.md, people/…. The email-scan routine also reads these.
4. **Outlook state:** the Family-Digest and Processed folders, plus the `Digest-First-*` / `Digest-Hold-*` categories. This stays in Outlook, and the new setup has to keep exactly the same conventions.
5. **Secrets:** `RELAY_TOKEN` is in plain text inside the prompt, and the PlayMetrics ICS URL is a credential.

**Related routine, out of scope unless you want it:** "Weekly school packets" (`trig_01L8BXb9…`, Fridays). It depends on memory files in a *different* project (`01a09420-…`): quarton-curriculum.md, math-packets-log.md, im-grade3/5 scope. It is a strong second candidate for the same move.

## 2. Target design

**Repo:** a new **private** repo, e.g. `shapir46/family-ops`. Do NOT use `dc-trip-2026`, because it is **public**.

```
family-ops/
  CLAUDE.md                      # who the family is, hard rules (no Gmail, never re-send credentials, bus/SACC exclusion, phone formatting)
  .claude/skills/
    family-digest/SKILL.md       # Steps 1–6, ported verbatim first
    daily-scoop/SKILL.md         # Step 7
  data/
    family.md                    # established child facts: teachers, activities, attribution rules
    bps-calendar-2026-27.yaml    # Step 2c table
    tbe-religious-school-2026-27.yaml
    lunch-menus.yaml             # month -> PDF URL (the run appends a new month itself)
    schedules/ari-mce-basketball.md
  scoop/                         # build2.py art.py hedcut.py render.py setup.sh README.md edition.sample.json
  logs/riddle-log.md             # appended daily, committed by the run
  logs/scoop-content-log.md
  scripts/                       # phase 4: deterministic helpers
```

**Secrets go in environment variables, never in the repo:** `RELAY_TOKEN` and `PLAYMETRICS_ICS_URL`. Rotate the relay token after cutover, since it has been sitting in a prompt.

**Network:** the Default environment is on *trusted* access. In my test, curl to every host this task needs was blocked except npm:
- print.jacobshapiro.net (required, because printing uses curl)
- forecast.weather.gov
- calendar.playmetrics.com
- resources.finalsite.net
- www.birmingham.k12.mi.us
- maxpreps.com, cbssports.com, nfl.com, nhl.com

WebFetch may reach some of these anyway, but printing will fail until print.jacobshapiro.net is allowed. Change it under the environment's **Edit → Network access → Allowed domains** (https://code.claude.com/docs/en/cloud-environments#network-access). The alternative is a separate "family" environment with those domains allowed.

**Connector:** attach **only Microsoft_365** to the new routine. A smaller tool list means less to go wrong.

**Learned facts:** today, when you tell a run session "Ari plays flag football", it lands in memory or project docs. In the new setup, that fact becomes a commit to `data/family.md`, so it is versioned and the next run sees it. The daily run commits its own log appends (riddle log, content log, new lunch URL) straight to `main`.

## 3. Migration phases

**Phase 0 — Export everything (no changes to the live system)**
- [ ] Get every file under `claude/fairfax-scoop/` and the basketball schedule doc out of the Cowork project, byte-for-byte.
- [ ] Export the project memory files relevant to family (and to the school packets, if that routine is in scope).
- [ ] Save the exact current prompt (done, redacted) and the routine config (done).

**Phase 1 — Build the repo (verbatim port)**
- [ ] Create the private repo and commit the kit and logs unchanged.
- [ ] Split the prompt into CLAUDE.md, the two skills and `data/*` with no change in behavior. Diff the split against the original so no rule is dropped. Every one of the roughly 120 rules gets a home.
- [ ] Have the prompt read `RELAY_TOKEN` and the ICS URL from the environment.
- [ ] Replace Cowork-only tool names (`project_read`/`project_write`, `mcp__cowork__create_artifact`, `/mnt/user-data/outputs`) with repo paths and git commits.

**Phase 2 — Shadow runs (2–3 days)**
- [ ] Create a Claude Code routine at **6:00 AM** (before the live one) in **read-only shadow mode**:
  - Email only Jacob, with subject `[SHADOW] Family Digest — …`.
  - **Skip Step 6.** It must not move or tag mail, or the live run would see an empty folder.
  - Build the newspaper but **do not print**.
  - Write logs to a `shadow/` branch only.
- [ ] Compare each shadow digest with the live one: items, dates, links, child attribution.

**Phase 3 — Cutover (one morning)**
- [ ] **Disable** the old routine. Disable only, do not delete, so its history and prompt are kept.
- [ ] Switch the new routine to full mode at 6:30 AM. It sends to both recipients, files mail, prints and commits logs.
- [ ] Never run both in write mode on the same day, or you get two emails, two printouts and double-filed mail.
- [ ] Rotate `RELAY_TOKEN`.

**Phase 4 — Hardening (optional, cuts cost and errors)**
Move the deterministic parts out of the prompt into tested scripts:
- ICS parsing and RRULE expansion
- Static-calendar window lookup
- Weekday/date checks
- Retention math for `Digest-First` / `Digest-Hold`
- Lunch PDF day-cell parsing
- Overflow and page-count checks for the newspaper
- Printing

The model keeps judgment work only: reading mail, dedupe, attribution and writing. Today's run costs about $6.50 a day; this phase should cut that substantially.

**Phase 5 — Cleanup (after about 2 weeks clean)**
- [ ] Delete the old routine, and archive or trim the Cowork project docs.
- [ ] Optionally move the school-packets routine the same way.

## 4. Things to watch
- **Double-run risk** during the transition. See Phase 3.
- **The Processed folder is the carry-forward memory.** The new run must use the same category names, the same 7-day undated rule, and the same purge rule.
- **Mid-month lunch URL.** The new run should commit a newly found URL itself, rather than asking Jacob to edit a prompt.
- **Run-session conversations** (Jacob replying to a run, uploading PDFs) are the other source of drift. In Claude Code, a reply like that becomes a commit to `data/`.
- **No family data in public repos.** This includes kids' names, schools, emails and calendar feeds.
