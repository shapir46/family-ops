# family-ops v2 — architecture plan

Status: proposal, 2026-10-10. Nothing here is built yet. v1 (the verbatim port) keeps running in shadow mode until v2 replaces it.

## Decisions (Jacob, 2026-10-10)
- **Printer is color.** The newspaper uses the kid color chips and colored timeline blocks fully, but every child also carries an initial so nothing depends on color alone.
- **The dashboard is served from the Mac mini** (the machine behind print.jacobshapiro.net), not from a claude.ai artifact.
  - The daily run POSTs the day's state to it, the same way it posts to the print relay.
  - Done checkmarks are stored on the Mac mini, and the next run reads them back.
  - Access goes behind a login Jacob controls (e.g. Cloudflare Access with Jacob's and Rebekah's emails). The family device gets its own credential.
  - This repo holds the server code under `home-server/`; Jacob deploys it.
- **Email is daily only.** Weekly, monthly and yearly work happens inside the daily run and surfaces only when it needs Jacob.
- **Build order as planned.**

## Goals
1. **One collection, many outputs.** Gather once a day into one structured file. The digest email, the newspaper and the dashboard all render from that file, so they never disagree.
2. **Each source on its own cadence.** Mail and live calendars daily; league schedules weekly; lunch menus monthly; school-year calendars yearly.
3. **Efficient.** Claude does only what needs judgment: reading email, attributing items to a child and writing short copy. Scripts do everything mechanical. Today's run uses about 367K tokens and costs about $6.50; the target is well under half that.
4. **Reliable.** Validated before anything goes out, safe to re-run, a missed day heals itself, and failures are reported plainly.

## Today's problem
v1 is one 50 KB prompt that does everything in the model's head: parsing ICS feeds, expanding recurrences, reading a lunch PDF grid, checking weekday/date pairs, retention arithmetic, HTML layout. These are exactly the steps where a model is slow, expensive and occasionally wrong. Each output is also written separately, so the newspaper and the digest can drift apart.

## The pipeline

```
                ┌──────────── Claude (judgment) ────────────┐
  Outlook mail ─┤ read, extract items, attribute child,      │
  Outlook cals ─┤ classify (event / action / FYI), write copy│──┐
                └────────────────────────────────────────────┘  │
                ┌──────────── scripts (mechanical) ──────────┐  ▼
  PlayMetrics ICS, league schedules, BPS district calendar, Temple Israel calendar (pending),    │ state/today.json ──► validate ──┬─► digest email (Outlook)
  lunch menu, weather (NWS API), sports scores               │   (one schema)                 ├─► dashboard (Mac mini)
                └────────────────────────────────────────────┘                                └─► newspaper PDF ─► printer
```

**`state/YYYY-MM-DD.json`** is the single source of truth for the day:
- `events[]`: date, start/end, title, child(ren), location, source(s), dedupe key
- `actions[]`: due date, what to do, child, links, status (open / done)
- `fyi[]`
- `lunch`, `weather`, `sports`, `school_status`
- `meta`: which sources ran, cache ages, warnings

Scripts own:
- dedupe keys
- weekday/date checks
- the bus/SACC filter
- retention math for `Digest-First` / `Digest-Hold`
- rendering of all three outputs

Claude owns only the fields that need judgment.

## Source registry and cadences
`sources.yaml` lists every source with its cadence, how it is fetched, where its cache lives, and when it goes stale. **A daily run refreshes any source that is stale**, not only the ones "due" today. A missed Sunday or a failed 1st of the month then repairs itself on the next run, with no separate routines to babysit.

| Cadence | Source | Fetched by | Cache |
|---|---|---|---|
| **Daily** | Outlook `Family-Digest` mail (new + carried-forward Processed) | Claude, via the M365 connector | — |
| **Daily** | 6 Outlook calendars (default, Family, Ari, Elle, Lila, Leo), today+10 days | Claude, via the M365 connector | — |
| **Daily** | PlayMetrics ICS (Elle soccer), today+10 days | script | `cache/playmetrics.json` |
| **Daily** | Weather (NWS API, JSON) | script | — |
| **Daily** | Sports scores (newspaper) | Claude + web, confirmed in 2 sources | — |
| **Weekly (Sun)** | League schedules: MCE basketball (Ari), Snaptivities flag football (Ari), PlayMetrics full season | script / Claude for PDFs | `data/schedules/*.yaml` |
| **Weekly (Sun)** | Week-ahead summary + health check (stale caches, unset variables, failed fetches) | script | — |
| **Monthly (1st)** | BPS lunch menu PDF: find, parse once into a day→entrée table | script (Claude only if parsing fails) | `cache/lunch-YYYY-MM.json` |
| **Yearly (Aug)** | BPS district calendar, Temple Israel Sunday School calendar, teachers/grades/classrooms, activity seasons | Jacob supplies, Claude structures | `data/calendars/*.yaml`, `data/family.yaml` |

Static calendars move from prose into **YAML** (date, label, who it affects, kind). Scripts can then query them instead of the model re-reading 80 lines every morning. In August the run emails Jacob a "new school year" checklist naming exactly what to supply.

## Routines
- **One daily routine at 6:30 AM ET.** It collects, builds state, validates, then sends the email, updates the dashboard, prints the newspaper and files the mail. Weekly, monthly and yearly work runs inside it when a source is stale. One routine means one place to look.
- Optional: a light **midday dashboard refresh** (calendars only, no email or print) if you want the dashboard to reflect same-day changes.

## Reliability rules
- **Validate before sending.** A script checks:
  - every weekday/date pair is real
  - no bus/SACC items
  - no credential or tracking-token URLs (ShulCloud `login_link`, ClassDojo `ctt=`)
  - no secrets
  - recipients are correct (shadow → Jacob only)
  - HTML uses only the connector's allowed tags

  If validation fails, the run stops before sending and reports why.
- **Idempotent.** The day's state file records `sent`, `printed` and `filed`. A re-run skips whatever already happened: no double emails, double prints or double filing.
- **Fallbacks:**
  - Send fails → publish the digest as an artifact, skip filing, push-notify. (Same as v1.)
  - Print fails → push-notify, keep the PDF.
- **Tests.** The scripts get pytest tests with fixture files: a real ICS with RRULE/EXDATE, a lunch PDF, retention edge cases, the dedupe matrix. Tests run before any change is pushed.
- **Cheaper email reading.** Bodies are stripped to text by a script before Claude reads them. The extraction subagents use a smaller model and return only structured items that match the schema.

## Outputs

### 1. Daily digest email
Same four sections as today (☀️ Today, ⚡ Needs Action, 📋 FYI, 🗓️ Next 10 Days), same recipients, same phone formatting. The change is that it is rendered by a template from `state.json` instead of written freehand. It adds a link to the dashboard, and **items marked done on the dashboard drop out of Needs Action** the next morning.

### 2. Fairfax Daily Scoop v2 (newspaper)
Keeps the masthead, the three columns, the Artic & Big Bear comic and every standing rule in `scoop/README.md`. Changes:
- **Kid color chips.** Each child gets one color and initial, used identically in the newspaper, the dashboard and the email. "Who" is readable at a glance.
- **"Today" timeline graphic.** A horizontal day bar with each event as a colored block, instead of a text list.
- **Icons**, as original inline SVG: weather (sun, cloud, rain, snow), lunch tray, soccer, basketball, football, ballet, school, Religious School, half day, no school.
- **Countdown box.** Days until the next big thing (Halloween, a half day, a birthday, the ski trip).
- **Week strip.** A 7-day mini calendar with icons in place of the "Coming Up" text list.
- **Clearer type hierarchy.** Fewer, larger headings, one idea per box, more white space, short lines.
- **Layout checks stay automatic.** The one-page check, the overflow check and a PNG review.

### 3. Live dashboard
Served from the Mac mini (see Decisions) for Jacob and Rebekah, phone-first:
- Today (school status, timeline, lunch, weather)
- Needs Action, with a **Done** checkbox shared between you
- Next 10 days, filterable by child
- FYI
- "Updated 6:34 AM" and health status

The daily run POSTs `state.json` to the Mac mini, and the page renders from it. Done flags are written back to the Mac mini, and the next run reads them.

**Family device (later):** a "wall mode" of the same page with large type, auto-refresh, no Done buttons, and landscape tablet layout. Because the dashboard already runs on the Mac mini, the device is either a tablet in kiosk mode or an e-ink frame that pulls a rendered image. Decided when we get there.

## Progress
- **Step 1 (foundation): done 2026-10-10.** Built so far:
  - family, calendars and schedules as data
  - ICS/PlayMetrics parser
  - lunch finder and parser
  - NWS weather
  - merge/dedupe and same-child conflict detection
  - pre-send validator and retention rules
  - source registry with stale-driven cadence
  - `collect` CLI
  - 24 tests
- **First shadow run, 2026-10-10 (manual), on Sonnet 5.5:**
  - Took about 9 minutes and cost about $4.10, versus $6.49 for the Cowork run.
  - Sent to Jacob only, passed `check-email`, built the newspaper without printing, filed nothing.
  - Fixed afterwards: the routine's system python3 lacked pdfplumber, so there is now a repo venv via `scripts/bootstrap.sh`, the `./fo` wrapper and a SessionStart hook. The weekday checker misread ranges like "Fri–Sun, Oct 23–25"; that is fixed and tested.
- **Next: step 2.** Render the digest email from `state.json` and shadow-compare it against v1.

## Build order (each step shadow-tested before it replaces v1)
1. **Schema + scripts for the mechanical sources:** ICS, static calendars as YAML, lunch parse, weather, validation, tests.
2. **Digest rendered from state.** Compare against v1's shadow output for a few days.
3. **Dashboard:** server code in `home-server/`, Jacob deploys it on the Mac mini behind a login, and Done connects to Needs Action.
4. **Newspaper v2:** design pass, new components, rendered from the same state.
5. **Cutover:** disable the Cowork routine, go live, rotate the relay token.
6. **Family device.**
