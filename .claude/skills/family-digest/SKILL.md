---
name: family-digest
description: Build and send Jacob's daily Family Digest from the Outlook Family-Digest folder, six Outlook calendars, PlayMetrics, and the static BPS/TBE calendars; then file processed mail. Run daily (6:30 AM ET) or on request.
---

Produce Jacob Shapiro's daily Family Digest from his Outlook "Family-Digest" folder plus the calendar sources below, email it to him, then file the processed mail away.

## Context
Jacob forwards family and school email from his personal ProtonMail account (jacob@shapbox.com) to the plus address jacob+Family@ivanhoecompanies.com. Those messages are filed into an Outlook folder called "Family-Digest".

**The folder is self-clearing.** Once a message has been folded into a digest it is moved to the subfolder "Family-Digest/Processed" (Step 6), so anything still sitting directly in Family-Digest is unprocessed by definition. Its *information* is then carried forward out of the Processed folder on later runs until it expires:
- A **dated** item (event, deadline, game, form due date) keeps appearing until its date has passed.
- An **undated** item keeps appearing for 7 days from the date it FIRST appeared in a digest.

Because of this, do NOT apply a "last 24 hours" filter to new mail — read everything in Family-Digest. If a run ever fails, the mail simply waits there for tomorrow.

**Family facts, child attribution, the bus/SACC exclusion, and the activity schedules in `data/schedules/` live in `data/family.md`. Read it (and the schedules it points to) first; they are part of these instructions.**


**Jacob reads this digest on his phone.** Mobile readability governs every formatting decision below.

**Hard rule: never use Gmail, Google Calendar, or any other mail connector for this task — not for reading and not for sending.** If the Outlook send tool is unavailable or errors, do NOT substitute another mail tool. Instead:
1. Finish the digest anyway — the gathering and parsing is the expensive part.
2. **Publish it as an artifact** (Artifact tool), id `family-digest-{YYYY-MM-DD}`, titled `Family Digest — {Month D, YYYY}`. Pass the same semantic HTML the email body would have carried. This is the primary fallback: it persists across sessions and Jacob can open it on his phone from his artifact gallery without hunting for this conversation. It is his own work product and stays private to him.
3. Also write it to `Family-Digest-{YYYY-MM-DD}.html` in `out/` (git-ignored) and surface it with SendUserFile, as a local copy.
4. **Skip Step 6 entirely.** Nothing gets filed, so every message stays in Family-Digest and tomorrow's run picks it all up. A missed send costs nothing except the send.
5. Say plainly in the FIRST LINE of the run report that the send failed (e.g. because the session was read-only), and that the digest is in the artifact instead. Lead with it — do not bury it under the statistics. Also send a PushNotification, since nobody is watching the session.

**If the write tools appear later in the same session** — Jacob may surface them by replying — reload them with the same `select:`, then complete Step 5 and Step 6 in order. Do not rebuild the digest and do not publish a second artifact; send the one already written.

**Graph rate limiting.** The write tools are subject to per-user throttling and a run of consecutive `outlook_batch_modify_labels` calls can trip a 429. When that happens the error carries `retryAfterSeconds` — wait at least that long, then retry that one call. Do not treat a 429 as a send/file failure and do not skip the message.

The PlayMetrics ICS feed, the lunch-menu PDF (and the BPS food-services menus page used to find it), and the static district and religious-school tables below are explicitly permitted and are NOT covered by that hard rule.

## Step 1a — Gather new email
Call `outlook_email_search` with `folderName: "Family-Digest"`, `limit: 25`, `order: "newest"`. Page with `cursor`/`offset` until the folder is exhausted. Take everything — no date filter.

For each message, call `read_resource` on its `mail:///messages/{id}` URI to get the full body. The summary field alone is not enough; real dates, deadlines, and links are usually buried in the body. The body comes back nested as `body.content` (with `body.contentType` alongside it), not as a plain string — read it from there.

Bodies are large HTML and several at once will flood the context window. Delegate the reading to subagents in parallel — roughly five to eight messages per agent — and have each return only the extracted items, dates, categories, and links rather than the raw body. If a `read_resource` result is persisted to a file instead of returned inline, read that file and strip the HTML with python before parsing.

Keep each message's `id` and `parentFolderId` — Step 6 needs both. Note that `outlook_email_search` does NOT return `parentFolderId`; a `read_resource` on any single message does, so grab it there. For reference, the Family-Digest folder id is `AAMkAGNiZmJhNjY0LTY1ZDQtNGM0MS04NGI0LTY0YjU3ZmQ3ZWU4MwAuAAAAAABgOhHVgAzTQa51VEMgP5V7AQDRY7d2V9yyS7uAXxhzwAFgAAeNhYGiAAA=` and its Processed child is `AAMkAGNiZmJhNjY0LTY1ZDQtNGM0MS04NGI0LTY0YjU3ZmQ3ZWU4MwAuAAAAAABgOhHVgAzTQa51VEMgP5V7AQDRY7d2V9yyS7uAXxhzwAFgAAeNhYGoAAA=` — still verify with 6a rather than trusting these blindly.

## Step 1b — Rebuild carried-forward information
Call `outlook_email_search` with `folderName: "Processed"`, `limit: 25`, `order: "newest"`, paging until exhausted. Read each message the same way as Step 1a (and have the readers also return each message's `categories` array) and re-derive its items using Step 3.

Then apply retention to those items:
- Keep a **dated** item if its date is today or later. Drop it once the date has passed (end of day, America/Detroit).
- Keep an **undated** item if the message's `Digest-First-YYYY-MM-DD` category date is fewer than 7 days ago. Drop it at 7 days — a `Digest-First` date exactly 7 days before today is expired.
- One message can hold both kinds. Its still-future dated items keep appearing even after its undated content has aged out.

**Carried-forward items are woven into the normal sections.** Do NOT create a separate "carried forward" or "still open" section, and do not label items as repeats — a deadline that is still live should read exactly the same on day four as on day one.

If a Processed message carries no `Digest-First-` category, treat its first-seen date as today and note it in the run report.

## Step 2 — Gather calendar: Outlook (six calendars)
Jacob's iCloud calendars sync into Outlook, so there is no ICS fetching for them. Query each calendar below separately with `outlook_calendar_search`, using `query: "*"`, `afterDateTime` = today, `beforeDateTime` = today + 10 days, `order: "oldest"`, `limit: 25`. Page with `offset` until the window is covered. Issue all six searches in one parallel batch.

| Calendar | `calendarName` parameter | Attribute events to |
|---|---|---|
| Default / work calendar | omit the parameter entirely | no specific child |
| Family | `Family` | no specific child |
| Ari | `Ari` | **Ari** |
| Elle | `Elle` | **Elle** |
| Lila | `Lila` | **Lila** |
| Leo | `Leo` | **Leo** |

Notes:
- These names were verified working on 2026-08-20. `calendarName` is case-insensitive. Omitting it searches the default calendar only — it does NOT search all calendars, which is why each one needs its own call.
- A calendar returning no output means it simply has no events in the window, not that it is missing. Do not report an empty child calendar as an error, and do not go hunting for an alternate name.
- The child calendars often repeat the child's name in the event title ("Elle Soccer Practice"). Strip the redundant name from the title and let the child attribution carry it — render "Soccer practice, Elle", not "Elle Soccer Practice, Elle".
- The Family calendar sometimes names a child in an event title ("Lila Curriculum Night"). That title IS the source, so attribute it to that child — and it can legitimately resolve a child left unnamed in email, when an event matches the email's date, time and subject.

**Filter to family and school events only.** This matters most on the DEFAULT calendar, which is Jacob's work calendar. Drop anything that reads as work: internal Ivanhoe invites, recurring standups/1:1s, events whose attendees are @ivanhoecompanies.com addresses, Teams meetings tied to work threads, and vendor trainings and syncs (EliseAI is a recurring example). Also drop personal-finance reminders (stock buy/sell notes, bank withdrawals and similar) — never surface a trade or transfer instruction in the digest. Property-maintenance items at Ivanhoe-managed addresses (e.g. 2660 Comfort St) read as work when their attendees are Ivanhoe staff — drop those too. A clearly personal entry on the work calendar (a Lions game at Ford Field, a family trip) is NOT work — keep it. When an event on the default calendar is genuinely ambiguous, leave it out rather than cluttering the family view, and note the omission in the run report. The Family, Ari, Elle, Lila, and Leo calendars are family calendars by definition — do not apply the work filter to them, and do not drop household chores or errands that appear there.

## Step 2b — Gather calendar: PlayMetrics soccer feed
Fetch this one ICS feed with the web fetch tool (`WebFetch` or `mcp__workspace__web_fetch`, whichever the session has):

the URL in the `PLAYMETRICS_ICS_URL` environment variable (read it with `printenv PLAYMETRICS_ICS_URL`) — U9G BLACK, attribute every event to **Elle**.

- If the fetch tool refuses the URL (provenance or scheme error), do NOT fall back to curl, wget, Python requests, or any other fetch method — that is prohibited. Skip the feed, add one line at the end of the digest saying so, and continue. Elle's Outlook calendar carries most of the same events, just without arrival time and uniform.

Parsing the ICS response:
- Split on `BEGIN:VEVENT` / `END:VEVENT`. Read `SUMMARY`, `DTSTART`, `DTEND`, `LOCATION`, `DESCRIPTION`, and `RRULE`.
- **Unfold lines first** — ICS wraps long values onto continuation lines starting with a space or tab. PlayMetrics wraps heavily mid-URL and mid-sentence; failing to unfold produces garbled output.
- Unescape `\n`, `\,` and `\;` in DESCRIPTION and LOCATION.
- `DTSTART;VALUE=DATE:` or a bare `DTSTART;TZID=...:YYYYMMDD` with no time means an all-day event. A `Z` suffix is UTC; `TZID=` names a zone. Convert everything to America/Detroit before comparing dates.
- Expand recurring events (`RRULE` with FREQ=DAILY/WEEKLY/MONTHLY, honoring COUNT, UNTIL, BYDAY) into the today-through-today+10 window, respecting `EXDATE`. If an RRULE is too complex to expand confidently, include the series once with a note rather than guessing dates.
- Skip events with `STATUS:CANCELLED`.
- Keep only events falling in the today-through-today+10 window.

PlayMetrics specifics:
- Event titles are prefixed with the team name (e.g. "U9G BLACK - Game"). Strip the prefix and render as "Soccer game" / "Soccer practice" / the tournament name.
- The DESCRIPTION on games carries the opponent, arrival time, uniform, and field. Surface arrival time and uniform — those are the parts Jacob acts on. Example: "Soccer game vs MI Stars Elite, arrive 5:00 pm, white-black-white".
- Routine practices belong in ☀️ Today and 🗓️ Next 10 Days but NEVER in ⚡ Needs Action. Games, tournaments, and anything with travel may warrant Needs Action only if the email traffic shows a decision or payment attached.
- **PlayMetrics wins over Outlook on soccer dates.** It is the club's live system of record. Where the Family calendar shows a tournament on a weekend PlayMetrics does not, say so and flag the Outlook entry as likely mis-dated rather than reporting both as fact.

## Step 2c — BPS district calendar (static reference)
Read `data/bps-calendar-2026-27.md`. It is part of these instructions (do not fetch the district calendar). Pull any entry in the today-through-today+10 window.

## Step 2c-ii — Temple Beth El Religious School calendar (static reference)
Read `data/tbe-religious-school-2026-27.md`. It is part of these instructions, including its rendering rules. Pull any entry in the today-through-today+10 window.

## Step 2d — Deduplicate across sources
The same event will often appear two or three times. Before writing anything, merge duplicates.

- Match on date + start time + a rough title match. Two events an hour apart are two events; the same title at the same time is one.
- **The same newsletter routinely arrives twice** — once to jacob@shapbox.com and once to jacob+Family@ivanhoecompanies.com, seconds apart. Same subject and same sender is one item.
- **Carried-forward items dedupe against new mail.** If a newsletter arrives repeating something already carried forward from the Processed folder, show it once. If the new copy changed a detail, use the new copy and note only what changed.
- Elle's soccer will frequently land in the PlayMetrics feed, Elle's Outlook calendar, AND a Michigan Development Academy email. Show it once. Prefer the PlayMetrics version — it carries arrival time, uniform, and field, which the others usually lack.
- School events often appear on the Family calendar AND in a Quarton newsletter. Show once.
- A school newsletter and the district calendar describing the same half day are one item.
- A Temple Beth El email, the Family calendar, and the Religious School table describing the same Sunday are one item — name all contributing sources.
- **An email action item deduped against a calendar entry that already settles it.** If a signup or booking deadline appears in mail but the relevant child calendar already shows the booked slot, the action is done — put the slot in 🗓️ Next 10 Days (or ☀️ Today) and keep it out of ⚡ Needs Action. Same for a form or waiver whose confirmation-of-receipt email is also in the folder — that action is closed, so it goes in 📋 FYI at most.
- When merging, name every contributing source: <i>(PlayMetrics + MDA email)</i>, <i>(Outlook · Elle + PlayMetrics)</i>, <i>(BPS district calendar + Quarton School)</i>, <i>(TBE Religious School calendar + Outlook · Family)</i>.

## Step 2e — When sources are empty
If no new mail arrived but carried-forward items or calendar events exist, still send the digest and add a one-line note that no new mail arrived. If there is no new mail, nothing carried forward, and no events from any calendar source, send a one-line email saying so and stop — and skip Step 6, since there is nothing to file. Do not fabricate content.

## Step 3 — Parse email
This applies to both new mail (Step 1a) and Processed mail (Step 1b). These are forwarded messages, so:
- Strip the ProtonMail forwarding wrapper and Jacob's signature block ("Jacob Shapiro / 248-331-7906"). Report on the ORIGINAL sender and original send date, not the forward.
- Bodies are HTML — extract the readable text.
- Some messages are re-forwards of something already covered. Dedupe by original sender + original subject; if a duplicate carries new information, note only what changed.
- Ignore messages that are obviously tests, delivery confirmations, or forwarding-setup notices from Proton — EXCEPT flag any unconfirmed Proton forwarding request as an action item, since mail won't flow until Jacob confirms it. Tests and delivery confirmations still get filed in Step 6; they just contribute nothing to the digest.
- If a message is older than ~2 weeks at its original send date, treat it as stale and mention it only briefly. Exception: if a stale message describes an event still in the future, keep it and add a short "confirm this hasn't changed" caveat. If a calendar independently confirms that same future event, drop the caveat — the calendar is live and settles it.
- A message may be addressed to no child by name yet come from a teacher whose child is already established elsewhere in the mail. Cross-referencing a confirmed teacher-to-child assignment is not guessing; use it, and say which source established it. The Established child facts in the Context section are already confirmed — use them freely.
- **Where two sources disagree on a date, surface the conflict rather than picking one.** Teacher emails in particular sometimes list weekday/date pairs that do not line up with the actual calendar. Say so in one short clause and name both sources. Sanity-check every weekday/date pair against the real calendar before writing it.
- **Apply the bus/SACC exclusion from the Context section here.** Do not extract bus or SACC items as digest items at all.

While parsing, pull out every item and classify it for retention:
- **Dated items** — events, deadlines, games, pickups, form due dates. Record the specific date. This date drives both what appears in the digest and the `Digest-Hold-` category in Step 6.
- **Undated items** — policy changes, general announcements, standing information with no date attached.

### Extract links
Also pull out every **actionable link** in the body — registration portals, sign-up forms, PDF forms to download, payment pages, RSVP pages, how-to videos. Capture the real `href`, not the anchor text. These get attached to their matching action item in Step 4, and they travel with carried-forward items too.

Link handling rules:
- Match each link to the action it belongs to. A newsletter with eight links usually maps to three or four real actions — attach only the links that serve an action Jacob has to take, and drop navigational chrome ("view in browser", "unsubscribe", "manage preferences", social icons).
- Many of these are tracking redirects (Smore `out.smore.com/render/...`, ShulCloud `track.php?...`, PlayMetrics `email.mda.playmetrics.com/c/...`). Pass them through **exactly as found** — do not try to clean, shorten, or resolve them. If a Smore URL still contains the literal placeholder `__$u__`, the sender's merge did not run; include it anyway but append a short note that the link may not resolve and the item is also reachable from the school's site. **However, when the newsletter also prints the destination URL in plain text (often as the anchor text), prefer that plain URL — it came from the same email and it actually works.** In practice the Quarton PTA newsletters print plain destinations for nearly everything, so the `__$u__` wrappers should rarely need to appear at all.
- **Never re-transmit a credential.** If a URL embeds an auto-login token, session JWT, or password-reset key (ShulCloud `payment.php?login_link=eyJ...` is the known example; ClassDojo `ctt=` login buttons are another), do NOT include it as a link. Name the destination domain in plain text instead — "pay at tbebloomfieldhills.shulcloud.com" — and note the substitution in the run report. A signed document-viewing link with an `auth_key` (e.g. sportsforms.net waiver PDFs) is not an account credential and may be used, but do not surface it unless the action is still open. A Constant Contact `tn.jsp` registration link is a campaign link, not a credential — it may be used.
- If a link you have is truncated or you cannot reproduce it in full, do NOT reconstruct it. Name the destination in plain words instead.
- If the body names a destination in plain text but gives no link (e.g. "register at the SACC page"), say so in words rather than inventing a URL. Never construct a URL that was not in the email.
- If two messages carry the same link, include it once. When two newsletters carry different tracking URLs for the same underlying form, use the newer one.
- Do NOT surface the PlayMetrics ICS feed URL anywhere in the digest. It is a credential, not content.

## Step 4 — Write the digest
Four sections, in this order.

### ☀️ Today
The top section — the at-a-glance for the day Jacob is reading it.

- **School day status first.** If today is a no-school day, a half day, or a recess day per the BPS district calendar (Step 2c), that is the FIRST line of this section, bolded, even when nothing else is on. Example: "**No school today — Labor Day.**" or "**Half day today — AM only, dismissal 11:50.**" When a half day applies only to certain grades, say which child it affects and give the dismissal time — and say what the other kids are doing, so Jacob is not left guessing. Do not mention busing. This is the single most schedule-disrupting fact in the digest and must not be buried. During summer, before the first day of school, say so once and name the first day. On a Sunday, the Religious School status from Step 2c-ii plays the same role: lead with the Religious School bullet (or the "No Religious School today" line) when the date is inside the season.
- **Events today:** every family/school event on today's date, from all calendar sources and from dated email items. Bullet each one, leading with the bolded time, and name the child where the source identifies one. Note any overlap in one short clause. Routine daily dismissal times belong in the school-status line, not as their own bullets. If nothing is on, write a single line: "Nothing on the calendar today."
- **Lunch menu:** today's school lunch menu, per the source below.

**Lunch menu source.** Birmingham Public Schools publishes the elementary lunch menu as a monthly PDF. The menu covers **Bingham Farms, Greenfield, Pierce, and Quarton** elementaries, so it applies to the kids at Quarton. It does NOT cover Derby Middle School; there is no Derby menu configured, so never show a menu for a Derby student.
Known monthly URLs are listed in `data/lunch-menus.yaml` (fetch with the web fetch tool, which returns extracted text directly — no PDF tooling needed).


**Finding a new month's PDF.** The URL changes every month (the finalsite path is different each time). When today's month is not in the list above, find the current PDF by fetching the BPS food-services menus page: `https://www.birmingham.k12.mi.us/programs-services/food-services/menus` — look for the **Quarton** elementary menu link for the current month (the Bingham Farms / Greenfield / Pierce / Quarton elementary menu), fetch that PDF, and use it. This one page lookup is explicitly permitted. Do not go searching the wider web. If the menus page fetch fails, or no Quarton/current-month link is on it, fall back to the "source needs updating" line below. Once you find a working new-month URL, add it to `data/lunch-menus.yaml`, commit and push that change to `main`, and mention it in the run report.

Rendering rules:
- Show **today's entrée only**, as one short comma-separated line. Do not list the week.
- **Ignore the Fruit & Vegetable Bar completely.** The PDF carries a large "Daily Fruit & Vegetable Bar" grid beneath the entrée calendar, roughly half the document. Never include it, never summarize it, never mention it. The same goes for the standing "Cold Lunch Choice" row — skip it unless a day has no hot entrée at all.
- The menu grid runs Monday-Friday with the day number leading each cell. Wednesdays are usually Smart Slice cheese or pepperoni pizza — a useful sanity check that you have read the grid onto the right weekday. **Trust the day number in the cell above everything else.** The first week of school is a known exception where the columns are shifted, so the Wednesday-pizza heuristic misfires there; the day numbers stay correct. A good cross-check: the "No School!" / "½ DAY" cells should line up with the district calendar's no-school and half-day dates. **Known quirk:** the text extraction of these PDFs can come back with garbled weekday labels and can drop days; always match on the day number, sanity-check against the Wednesday-pizza pattern and the half-day dates, and if the cell for today cannot be read confidently, say so rather than guessing.
- If today is a weekend, a no-school day, a summer-break day, or a half day whose cell shows no entrée (half days are marked "½ Day !!" / "½ DAY" with no meal listed), say that in one line instead — e.g. "Lunch menu: no school today." Never invent menu items. This no-school line takes precedence over the month-mismatch line below.
- If the PDF's header month does not match today's month on a day that IS a school day (and no correct month's PDF can be found via the menus page), render "Lunch menu: source needs updating for {Month}" and flag it in the run report so Jacob can supply the new URL.
- Every item names its source, including the lunch line: <i>(BPS elementary lunch menu)</i>.

### ⚡ Needs Action
Anything with a deadline, a decision, or a task — from new mail and carried-forward items alike. One bullet each:
- Lead with the bolded date or **URGENT**, then what Jacob has to do, then the detail. Front-load — the first ~8 words have to carry the item, because that is all that fits on one phone line.
- Name the child if the source makes it clear.
- **Attach the relevant link** extracted in Step 3 as an `<a href="...">` with short descriptive anchor text — "Register", "Health Appraisal form", "Pay balance", "How-to video". Never paste a raw URL as visible text. If an item has more than one link, give each its own short anchor at the end of the bullet, comma-separated.
- If an action has no link in the source email, say where to go in plain words (portal name, office phone) instead.
- Sort by deadline, soonest first. Anything due within 48 hours goes at the top marked **URGENT**. A deadline that has already passed but whose source still says to act goes at the very top, marked **URGENT — overdue**.
- Items with no hard date go last, under a bolded "No hard date" lead-in.
- Routine practices, chores, and recurring calendar events never appear here.
- Leave out anything a calendar or a confirmation email shows is already done (see Step 2d).
- Keep this section tight. An actionable sign-up more than about four weeks out belongs in 📋 FYI, not here. An item that needs lead time to complete (anything requiring a doctor's signature, for instance) can appear earlier than its due date would suggest — say why.

### 📋 For Your Information
Everything else, one or two lines each. Announcements, newsletters, schedule confirmations, general updates. Include a link only where it genuinely adds something (a calendar PDF, a policy document); otherwise keep these link-free.

### 🗓️ Next 10 Days
The final section. **Starts TOMORROW** — today is already covered in the ☀️ Today section at the top, so do not repeat it here. Covers tomorrow through today + 10 days, merging:
1. Family/school events from all six Outlook calendars (Step 2), each attributed to its child where the calendar identifies one.
2. Events from the PlayMetrics soccer feed (Step 2b), attributed to Elle.
3. School-day changes from the BPS district calendar (Step 2c) — no-school days, half days, recesses, conference nights.
4. Religious School Sundays and special notes from the Temple Beth El table (Step 2c-ii), attributed to Ari and Elle.
5. Dated items from new mail (Step 1a) and carried-forward mail (Step 1b) — including deadlines, not just events.

All of it deduplicated per Step 2d.

**Format it as a day-grouped list, NOT a table.** A four-column table is unreadable on a phone — the columns crush to a few characters each and the row wraps into a scrambled block. Instead, for each day that has anything on it:

```
<p><b>Thu, Aug 27</b></p>
<ul>
<li><b>12:00–12:30 pm</b> — JK/K playground meet-and-greet at Quarton <i>(Linda Sackett, Quarton)</i></li>
<li><b>6:00–7:15 pm</b> — Soccer practice, Elle, at Pembroke Park <i>(PlayMetrics + Outlook · Elle)</i></li>
<li><b>Due</b> — GSRP Care Plan + Permission to Administer Medication forms <i>(Lindsay Birckett, BPS GSRP)</i></li>
</ul>
```

List rules:
- One `<p><b>day</b></p>` heading per day, followed by one `<ul>` of that day's items.
- Each item starts with the bolded time ("12:00–12:30 pm", "All day", or "Due" for a deadline), then an em dash, then what it is, which child if known, and where.
- Source goes last, in italics and parentheses. For Outlook calendars name which one: "Outlook · Family", "Outlook · Elle", "Outlook · Lila", or plain "Outlook" for the default calendar. Other sources are "PlayMetrics", "BPS district calendar", "TBE Religious School calendar", or the originating sender. Merged items name all contributing sources.
- No-school days, half days, and Religious School status lead their day's list, above timed events, since they reframe the whole day.
- Strict chronological order. Omit days with nothing on them.
- **Verify every weekday/date pair against the real calendar before writing it.** A wrong weekday is the most damaging error this digest can make.
- Keep this section link-free; the links live in ⚡ Needs Action.
- Resolve any date given without a year to the nearest sensible upcoming date, and say so inline.

Rules:
- Be specific. "Playground meet-and-greet Thu Aug 27, 12:00–12:30pm at Quarton" beats "school event coming up."
- Every item names its original source (e.g. "Linda Sackett, Quarton"). This includes the lunch menu line.
- Do not pad. If there are only two items, the digest is two items.
- No preamble, no sign-off, no "here's your digest" framing.
- Where two sources genuinely conflict on a date, surface the conflict in one short clause rather than silently picking one. Where two events simply overlap in time, note the overlap in one clause on the later item so Jacob sees the clash.

## Step 5 — Send
Use `outlook_send_mail`:
- To: jacob@ivanhoecompanies.com, Rebekah.Shapiro@gmail.com
- Subject: `Family Digest — {Month D, YYYY}` using today's date
- `bodyType: "html"`
- Body: the digest as clean semantic HTML. Start at the first `<h2>` — no `<h1>`, since the subject line already carries the title.

**Mobile formatting requirements — this email is read on a phone:**
- Use `<h2>` for the four section headings, `<p>` for day headings, `<ul>`/`<li>` for everything else. No `<table>` anywhere.
- Keep each bullet to roughly one or two phone lines. If an item needs more, split the extra context into a short trailing sentence rather than one long run-on line.
- Bold the scannable anchor (date, time, or URGENT) at the START of each bullet so the eye can skim the left edge.
- **Links must always be `<a href="...">` with short descriptive text.** A pasted tracking URL destroys mobile line wrapping — these URLs run hundreds of characters. Where no link exists, name the domain in plain text (e.g. "pay at tbebloomfieldhills.shulcloud.com").
- Escape bare ampersands in href values as `&amp;` so long tracking URLs survive intact.
- No nested lists more than one level deep, no multi-sentence parentheticals, no ASCII alignment or padding spaces.
- The connector sanitizes HTML against a narrow allowlist — headings, paragraphs, links, lists, tables, and basic formatting survive; `<style>`, `<span>`, `<img>`, and all inline CSS are stripped. `<a href>` DOES survive. Do not attempt responsive CSS or media queries; they will not survive. Readability has to come from semantic structure and short lines alone.

## Step 6 — File processed mail (ONLY after a successful send)
**Gate: run this only if `outlook_send_mail` returned success.** If the send failed, errored, or you stopped early for any reason, do nothing in this step — leave every message exactly where it is. Mail that was never delivered to Jacob must never be filed away.

**6a — Resolve the Processed folder.** Take `parentFolderId` from any message read in Step 1a, call `read_resource` on `mail:///folders/{parentFolderId}`, and look through `children` for a folder named "Processed". If no such child exists, SKIP the rest of Step 6 entirely and report that the Processed folder is missing so Jacob can create it. Never substitute Deleted Items for messages that have not been filed — that would destroy the carry-forward memory.

**6b — Tag and file the new messages from Step 1a.** Use `outlook_batch_modify_labels`, **max 5 messageIds per call**, so page through them:
- `addCategories`: `Digest-First-{today, YYYY-MM-DD}`. Additionally add `Digest-Hold-{YYYY-MM-DD}` where that date is the LATEST future date anywhere in the message. Omit the Hold category entirely if the message contains no future dates.
- `moveToFolderId`: the Processed folder id from 6a.
- Because the categories differ per message, group messages by identical category set and issue one call per group — that is normally 3-6 calls. If a call returns a 429, honor `retryAfterSeconds` and retry just that call.
- Apply category names directly; they do not need to be pre-created and will simply show uncolored.
- Only file messages that were actually read in Step 1a this run. Never file a message you did not parse.
- If a message's dates live only in an attachment you did not open, set no Hold category and note in the run report that the message will age out on the 7-day undated rule instead of on a real date.

**6c — Purge expired messages out of Processed.** For each message currently in the Processed folder, read its categories. A message is expired when BOTH are true:
- it has no `Digest-Hold-` category, OR its Hold date is before today; AND
- its `Digest-First-` date is 7 or more days before today.

Pass expired message ids to `outlook_batch_delete_messages` (max 50 per call). That is a recoverable soft delete to Deleted Items, not a permanent one — Jacob can restore anything. If nothing qualifies, call nothing and say so.

Leave alone, and mention in the run report, any Processed message with no `Digest-First-` category. Do not guess at its age.

## Run report
Confirm what was done: count of new messages processed and carried-forward messages re-read; how many carried-forward items were still live versus dropped as expired; how many events came from each of the six Outlook calendars versus filtered out as work; whether the PlayMetrics feed and the lunch-menu PDF fetched successfully (and, from the first of each month, the new month's PDF URL if you had to find it via the BPS menus page); how many duplicates were merged; how many bus/SACC items were suppressed; how many links were attached to action items and whether any credential-bearing URL was replaced with plain text; and for Step 6, how many messages were filed into Processed and how many were purged to Deleted Items.

If the send failed, that fact goes in the FIRST LINE of the report, ahead of all statistics. Only push-notify the user (PushNotification) if the run failed or needs Jacob's input (e.g. send failed, lunch-menu source could not be found, a Processed folder is missing); a clean run stays silent.