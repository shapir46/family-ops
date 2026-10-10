# The Fairfax Daily Scoop — build kit

One-page Letter PDF newspaper. Files (in the family-ops repo): `scoop/` holds build2.py, art.py, render.py, setup.sh, edition.json (sample; copy it and overwrite every field each day) and README.md; the logs are `logs/riddle-log.md` and `logs/content-log.md`. (hedcut.py is RETIRED; ignore it, never import it.)

## PUBLISHING SCHEDULE (Jacob, Oct 10, 2026) — overrides anything below that conflicts
- **Monday–Friday:** the regular daily edition.
- **Saturday:** a **Weekend Edition** that covers Saturday AND Sunday. Set `edition` to "Weekend Edition" and `date` to "Saturday & Sunday, October 17–18, 2026".
  - `sched_title` = "This Weekend"; `sched` lists both days, each item led by its day and time ("<b>Sat 9:30 am</b> — ...").
  - `week_title` = "Next Week"; `week` = Mon–Fri highlights (half days, no-school days, games).
  - Weather: `wx` = Saturday, `wx2` = Saturday night + Sunday; `forecast` = the 4 days from Sunday.
  - `lunch_title` = "Monday's School Lunch"; `lunch` = "No school this weekend. Monday: <Monday's entrée>" (Monday's cell from the lunch menu, if school is on).
  - Sports: `yday_title` = "Friday's Scores"; `tonight_title` = "This Weekend in Detroit", with Saturday and Sunday Detroit games and the kids' weekend games; `lions` = a preview of the weekend game.
  - Stories lean toward fun weekend things to do (Birmingham first, then Detroit/Michigan). The Saturday Tech Corner still applies.
- **Sunday:** no newspaper. Do not build, print or log anything. (The digest email still goes out every day.)
- Riddles: `riddle_prev` uses the label of the day the last logged riddle ran ("<b>Saturday:</b> ..." on Monday).

## NEW STANDING RULES (Jacob, Oct 8, 2026) — these OVERRIDE anything below that conflicts
1. **Unconfirmed = silent.** If a score, Lions item, tonight's game or high-school result cannot be confirmed in a second source, leave it out completely. NEVER print "not confirmed", "not posted", "no scores confirmed", "no game found" or any placeholder. Set the field to an empty list/string (yday: [], lions: "", tonight: [], hs: []); build2.py skips empty sections and their headings. Print only confirmed facts.
2. **Forecast row = 4 days** (starting tomorrow), not 5. Never print a blank "—" day.
3. **Headline art: real photo or nothing.** Never draw, generate or stipple an illustration for the headline. If a real photograph for the story can be obtained (a freely licensed image fetchable in the shell), set `head_photo` in edition.json to {"img": "<local path>", "credit": "<photographer / source>"}. If not, omit `head_photo`: the story simply has no photo. Mention it in the run report only.
4. The comic stays original art (ARTIC & BIG BEAR) with a new gag AND new drawings each day.
5. In the NEVER REPEAT list below, ignore item 2 (hedcut scene); log "photo: <credit>" or "no photo" instead.

## NEVER REPEAT (standing rule from Jacob, Oct 7, 2026) — applies every day
Nothing may repeat from any earlier edition: not articles/stories, not photos/illustrations, not the comic (text AND drawings), not riddles/jokes/words.
1. **Before building**, read `logs/content-log.md` and `logs/riddle-log.md`. Pick a headline story, news items, tech story and critter photo that are not in the logs (a new story on the same topic/event counts as a repeat).
2. (Retired: no headline illustration. See New Standing Rule 3.)
3. **Comic: new drawings every day, not just new text.** In art.py comic(), change the setting, props, poses, backgrounds and panel colors of Artic (arctic fox) and Big Bear (polar bear), e.g. new scenery, new objects, different poses/expressions, different scarf/hat/gear. A new gag on the same artwork is a repeat. Log a one-line description of the art.
4. **Critter photo**: never reuse a photo or animal already in the log.
5. **After printing**, append today's entry to content-log.md (headline, news items, tech story, headline photo credit or "no photo", comic gag + art description, critter) and riddle-log.md.

## Build
1. Make a work dir and copy `scoop/` into it (`cp -r scoop/. <workdir>/`).
2. `sh setup.sh` (installs fonts into ./fonts via npm; installs playwright if missing; Chromium is preinstalled — never run playwright install).
3. Write edition.json (schema below).
4. `FONTDIR=./fonts $REPO/.venv/bin/python build2.py && $REPO/.venv/bin/python render.py newspaper.pdf` ($REPO = the family-ops checkout; `sh $REPO/scripts/bootstrap.sh` creates `.venv`).
5. render.py prints one "content bottom / column bottom" pair per column. Every content value must be <= its column bottom (~830); aim for <= ~800 so nothing is clipped (check the PNG: the riddle/joke box and the last items must be fully visible). If a column overflows, shorten text (never shrink fonts). Run `pdfinfo newspaper.pdf | grep Pages` — must be 1. Look at a PNG (`pdftoppm -r 100 -png`) for clipping.

## edition.json fields
date ("Tuesday, October 6, 2026"), hi (temp number), wx (HTML: high/wind/morning low), wx2 (tonight + tomorrow, italic line), **forecast** (4 entries [day, high, low, short conditions], starting with tomorrow, from the NWS forecast; trust the weekday names, the NWS text page sometimes prints the wrong date next to them; a "—" low is OK for the first day only), lunch (HTML; on Thursdays append the bagel note), sched (list of "<b>time</b> — event" HTML strings, today only), sched_note (source note), week ("Coming Up", next ~5 days, short), quarton (list of Quarton/school-note strings), yday (list of [label, "Team X, Team Y N"] — previous day's confirmed results only; [] if none), lions (short Lions report, "" if unconfirmed), **fantasy** (optional list of short HTML lines), tonight (list of today's confirmed Detroit games; [] if none; add a kids' game as a bullet when a child has one that evening), hs (Seaholm & Groves, short bullets, confirmed only; [] if none), head/sub/story[3 paragraphs]/head_src (headline story), **head_photo** (optional {"img": "<local path to a real photo>", "credit": "..."}; shown under the subhead; omit if no real photo), news[0..2] each [headline, text, source] (news[1] sits center under headline, news[0] right column, news[2] left column), **critter** (optional {"img": "<local path to a real photo file>", "name": "Baby Red Panda", "fact": "one short true fact", "credit": "photographer / source"}; replaces news[2] in the left column; NEVER a drawing), **word** ([word, part of speech, kid-friendly definition, short example sentence]; a NEW word each day), riddle (today's riddle, NO answer), riddle_prev ("<b>Yesterday:</b> <riddle> <i>Answer!</i>"; on Monday "<b>Saturday:</b> ..."), **optional labels**: edition (masthead, default "Daily Edition"), sched_title (default "The Family Schedule"), lunch_title ("Today's School Lunch"), week_title ("Coming Up"), yday_title ("Yesterday's Scores"), tonight_title ("Tonight in Detroit"), joke (with punchline), foot (footer sources line).

## Standing requests from Jacob
- **Sports accuracy.** Use the official or primary source for each league and confirm every score in a second source (CBS Sports, MLB.com, NHL.com, ESPN recap pages via search; ESPN scoreboard is blocked in WebFetch). Never use memory or aggregated summaries. Check winner, loser and final score together. Print only what is confirmed; otherwise say nothing (see New Standing Rule 1). Same for Lions, tonight's games and Seaholm/Groves.
- Overall font size is 7.8pt body in build2.py. Keep text short enough to fit; do not shrink fonts.
- 4-day forecast row sits under the weather line.
- Word of the Day (with definition and example) sits above the riddle and joke.
- **Thursday bagel day.** On Thursdays, add to the lunch box: "Bagel Day! Bagels are delivered to students in their classrooms every Thursday morning." Applies on school days only.
- **Fantasy football top performers** (`fantasy` field; omit on other days). Only the day after football games: Monday list 5–6 players; Tuesday and Friday list about 3. Standard (PPR) scoring from an official source, each player's team and stat line confirmed in a second source; print only what is confirmed. One short line each, e.g. "<b>Josh Allen</b>, QB BUF, 34.2 pts". When present, build2.py drops the right-column news[0] story to make room.
- **Cool kids' technology story, Wednesdays and Saturdays.** Make news[1] a kid-focused tech story (robots, space tech, AI explained simply, gadgets, coding, engineering), headline starting "Tech Corner:". Sources: Science News Explores, NASA, Wired, Popular Science, Smithsonian Magazine, TIME for Kids. ~60–80 words, own words, source line, no repeats.
- **"Cutest Critter" PHOTOGRAPH, Tuesdays and Fridays.** Real photograph, NOT a drawing. A freely licensed photo (Wikimedia Commons, NASA, a zoo press page). If none can be obtained, omit `critter` and say so in the run report. Caption = animal name + one short true fact + credit. ~150px tall.

## Rules (user-approved layout)
- Masthead "The Fairfax Daily Scoop" (Grenze Gotisch); keep the three different-width columns and the comic strip at the bottom ("ARTIC & BIG BEAR": Artic = arctic fox, Big Bear = polar bear; art.py comic()).
- Stories: only fun, kid-friendly. Prefer Birmingham MI, else Detroit/Michigan, else anywhere. Headline story ~3 short paragraphs, with a real photo only if one can be obtained (see New Standing Rule 3).
- No third-party characters. The comic is original; NEW 4-panel gag AND new artwork each day in art.py comic() (keep text short so bubbles fit).
- Kids' sports appear only in the family schedule, plus as a game under "Tonight in Detroit" when that evening.
- Daily riddle + joke: new each day, kid-friendly, never repeat riddle-log.md. Yesterday's answer goes in riddle_prev. After building, append today's riddle, answer and word to riddle-log.md.
