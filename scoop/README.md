# The Fairfax Daily Scoop — build kit

One-page Letter PDF newspaper. Files (in the family-ops repo): `scoop/` holds build2.py, art.py, render.py, setup.sh, edition.json (sample; copy it and overwrite every field each day) and README.md; the logs are `logs/riddle-log.md` and `logs/content-log.md`. (hedcut.py is RETIRED; ignore it, never import it.)

## DESIGN & CONTENT UPDATES (Jacob, Oct 10, 2026) — override anything below that conflicts
- **Flexible layout.** The number of columns, their widths and where each section sits are flexible. Arrange them to fit the day's content, with readability as the goal.
  - Set `layout` in edition.json (see the field list); without it, the default three-column page is used.
  - Never shrink fonts below the body size to make things fit. Re-arrange or shorten instead.
  - The masthead stays on top and the comic strip at the bottom.
- **Full columns, minimal white space** (Jacob, 2026-10-10). Every column ends close to its bottom, filled with real content: never leave a block of empty space.
  - `render.py` prints `LAYOUT: OK` only when nothing spills past a column and each column's content ends 0–40 px above its bottom. Anything else (`UNDERFILLED` / `OVERFLOW`) must be fixed before printing.
  - To fill a gap, add `extras` (kid-friendly fun facts, "This Week in History", a quote, a weekend activity idea) and place them with `layout`.
  - Fine-tune the last few dozen pixels by lengthening or trimming an extra's text, choosing a longer or shorter extra, or adjusting column widths.
  - **No drawing activity** in any edition (Jacob, 2026-10-10).
  - To fix an overflow, shorten text, move a section to a roomier column or adjust the widths. Never shrink fonts or pad with empty spacing.
  - Every extra must be true, kid-friendly and new: log them in content-log.md and never repeat one.
- **No riddle in any edition.** The Daily Joke stays. `riddle` and `riddle_prev` are gone.
- **Only kids' sports are shaded** (Jacob, 2026-10-10). The kids' team boxes (Spartans Hoop Scoop, MDA Kicks & Giggles, and any future kid team box) use one light green (`.sport` in build2.py). The Detroit Sports Page and Ari's Fantasy Team have no color: the Sports Page is plain column text and the fantasy box is a white bordered box (`.plain`). Never use the green for anything but kids' teams.
- **Word of the Day pops.** It renders as a large accent-colored word in its own bordered box (build2.py `sec_word`). Keep the word short and kid-friendly; the definition and example stay brief.
- **The paper's official icon is an ice cream cone** (Jacob, 2026-10-13). It is original art in art.py (`scoop_icon`: waffle cone, strawberry and chocolate scoops, sprinkles, a cherry) and sits on both sides of the masthead title. Anywhere the paper needs a logo or mark, use this cone; never another icon, and never a third-party logo. No edition.json field.
- **Weather icons** (Jacob, 2026-10-12). The weather box shows a drawn icon of the conditions next to today's temperature and in each forecast day, as well as the text.
  - build2.py picks the icon itself from the wording (art.py `wx_kind`): today's from the first sentence of `wx` (so lead `wx` with today's conditions, e.g. "<b>Sunny.</b> ..."), each day's from its forecast condition. Use the NWS phrases (Sunny, Mostly Sunny, Partly Sunny, Mostly Cloudy, Chance Rain Showers, Rain Likely, Thunderstorms, Snow, Patchy Fog, Breezy) and the icon follows. No edition.json field.
  - Icons are original art in art.py (`weather_icon`; `python art.py --list` names them). An unrecognized phrase gets no icon, never a guessed one.
- **No sources on the page; credits only in the footer** (Jacob, 2026-10-12). No source or credit line appears under any item: not the lunch, the family schedule, stories, news, extras, pictures or the weather (no "(NWS)" in `wx`/`wx2`).
  - Credit sources in `foot`, the small line at the bottom: "Scores: ... · Weather: National Weather Service · News: <outlets>". build2.py adds every picture credit (`head_photo`, `critter`, picture extras) to the footer itself, as the photo licenses require.
  - `head_src` and each news item's source stay in edition.json for the log and the footer, but are not printed.
  - **The footer is one run-on line** (Jacob, 2026-10-13): sources, notes and picture credits run together, separated by " · ", with no line breaks. build2.py turns any `<br>` in `foot` into " · ".
- **School lunch is large and bold** (Jacob, 2026-10-12): the menu prints at 11pt bold (`.lunch` in build2.py), with no source line. The Thursday bagel note stays as a smaller line under it.
- **Featured artwork** (Jacob, 2026-10-14). A family kid's own artwork, shown in a gold gallery frame with a museum-style title card: "Featured Artwork", the title, "by <artist>" and a one-line note describing it.
  - **Queue:** Jacob's artwork goes in `scoop/featured/` (image + an entry in `featured/queue.json`: date, img, title, artist, note). build2.py picks up the entry whose `date` falls in the edition's date(s) by itself and prints `FEATURED: <title> by <artist>`. A Sunday date runs in Saturday's Weekend Edition. Name it in the run report and in content-log.md ("Featured art: <title> by <artist>").
  - **Placement:** section `featured` in `layout`. If the layout leaves it out, build2.py puts it right under the headline story, so a due artwork is never dropped. Re-balance the other sections around it (move the joke or a news item to another column); never shrink or crop the artwork. In a narrow column (about 2.1in) the box stacks the art above its title card.
  - Print the title exactly as Jacob gives it. The artist byline is part of the artwork, not a source credit, so it prints on the page. The art is never AI-altered, redrawn or used anywhere else (comic, extras, prompts), and each piece runs once.
- **Assigned stories** (Jacob, 2026-10-15). A one-time headline story Jacob asks for (for example, something new he saw around town), written ahead of time with his own photo in `scoop/assigned/queue.json` (date, head, sub, story, head_src, photo {img, credit, h}, topic) with the photo in `scoop/assigned/`.
  - build2.py swaps it in as the headline story on its date by itself (a Sunday date runs Saturday) and prints `ASSIGNED STORY: <headline>`. Each runs once; it counts as that edition's local article when it is local.
  - On that day, don't research a headline: use the time for the news items, and an already-found headline story can become a news item. Log it as "Headline: <headline> [topic] (assigned by Jacob, his photo)" and credit "Shapiro family" in `foot`; build2.py adds the photo credit.
  - Write it only from what Jacob says and what the photo shows; never add store hours, addresses or prices that weren't given or visible.
- **Holidays.** If the day is a holiday, name it in the `banner` strip under the masthead (e.g. "Happy Halloween!", "Indigenous Peoples' Day", "Chanukah: 3 Candles").
  - Use `state.almanac[0].holidays`. On the Weekend Edition, also give Sunday's with a "Sun:" prefix, from `almanac[1]`.
- **Shabbat, Fridays only.** The banner says it is Shabbat and gives the sunset time from `state.almanac[0].shabbat.sunset`, e.g. "Shabbat Shalom! Shabbat begins at sunset, 6:49 pm". Never on other days, including the Saturday Weekend Edition.
- **Balanced news, one local story** (Jacob, 2026-10-13). The articles (headline story and `news[0..2]`) are a mix of topics, not mostly science.
  - **One local article in every edition.** Birmingham MI first, else Detroit, else elsewhere in Michigan. Give it the headline when there is a good one. Sources: City of Birmingham, BPS, Patch, Hoodline, Hometown Life, LittleGuide Detroit, Metro Parent, Detroit Free Press, Detroit News, WXYZ, WDIV ClickOnDetroit, MLive, Michigan Radio, the Detroit Zoo, The Henry Ford, the DIA, Cranbrook.
  - **Every article a different topic.** Topics: local community and events; animals and nature; arts, music, books and movies; people and kids doing amazing things; history and anniversaries; food and holidays around the world; fun world news (records, inventions, oddities); science and space.
  - **At most one science or space article per edition.** On Tech Corner days (Wed, Sat), Tech Corner is that one, so there are no other science articles.
  - **At most one article from any one outlet.** Science News Explores and NASA are for the science slot only.
  - Don't lead with the same topic two editions in a row. Tag each headline and news item in content-log.md with its topic, e.g. "[local]", "[animals]", "[arts]", so the balance can be checked.

## COMIC: CHARACTER LIBRARY (Jacob, 2026-10-11) — overrides anything below that conflicts
- **The comic is composed, not hand-drawn.** `art.py` is a library of detailed, original characters on a rig. Every character can take any pose, wear any face and gear and hold a prop.
  - The day's strip goes in edition.json `comic`. Never edit art.py for a daily strip; extend the library only through `/newspaper-design`.
  - `python art.py --list` prints the library. `python art.py --sheet cast.html` draws a model sheet of every character, pose, face, gear item, prop and scene.
- **Cast** (`who`):
  - `bear`: Big Bear, a polar bear.
  - `fox`: Artic, an arctic fox.
  - `mack`: Mackenzie, a scruffy apricot mini-poodle (no topknot) with a lavender collar (Jacob, 2026-10-11).
  - `uni`: Uni, a pastel unicorn.
  - `bob`: Bob, a toy brick guy. Never call him LEGO and never print a brand name or logo.
  - Artic and Big Bear star. The strip is called **"ARTIC, BIG BEAR & FRIENDS"** (Jacob, 2026-10-13); art.py prints it (`COMIC_TITLE`), and edition.json has no title field. Mackenzie, Uni and Bob join as the supporting cast: at least one of them appears in most strips, and never more than two characters share a panel.
- **Library:**
  - poses: stand, wave, point, cheer, shrug, think, run, sit, hold, tada, akimbo, facepalm, dance, scared
  - faces: happy, grin, laugh, surprised, sad, worried, angry, smug, wink, sleepy, love, proud
  - gear: scarf, beanie, earmuffs, cap, bow, party, crown, glasses, shades, cape, bowtie, collar (Mackenzie wears her collar unless it is set to false)
  - held props: balloon, book, mug, cocoa, umbrella, flower, icecream, wand, ball, basketball, pizza, cookie, rod, magnifier, rake, flag, leaf, snowball, pumpkin, fish, trophy, gift
  - props: pumpkin, tree, pine, snowman, leafpile, boot, ball, basketball, kite, hole, bucket, sandcastle, gift, cake, table, campfire, tent, puddle, rock, flowers, bench, sled, bush, snowpile, fish, trophy, stars, hearts, cloud, sun, `sfx` (sound-effect text), plus every held prop
  - scenes (drawn): snow, ice, autumn, hill, beach, night, kitchen, living, classroom, town, backyard, pumpkins, soccer, gym, space, rain, plain
  - painted scenes: see Comic: painted backdrops (`python art.py --list` names them all)
- **New drawings every day** means a combination not in the content log: a different scene (or sky color and `mirror`), poses, faces, gear and props for each panel, not just new words. Match the season and the day when it helps (pumpkins in October, snow in winter).
- **Bubbles:** at most about 22 characters per line and 2 lines. `kind` is `say` (default), `think` or `shout`. A panel can also have a `caption` ("Later...").
  - build2.py prints `COMIC WARNING` when a bubble covers a face or is too wide, or when `comic` is missing. Fix every warning before printing (move the bubble with `x`/`y`, shorten it, or move the cast).
- **Log** the strip in content-log.md as the gag, then the art: scene per panel and each character with pose, face and gear (e.g. "pumpkins: bear hold/happy/green scarf + pumpkin, fox point/surprised").

## COMIC: PAINTED BACKDROPS (Jacob, 2026-10-12)
- **Scenery painted with Grok, characters still drawn.** `scoop/backdrops/` holds picture-book backdrops painted once with xAI's Grok image API (`backdrops.py`), reviewed and committed. A panel uses one by naming it as its `scene` (e.g. `"scene": "farm"`); the original art.py cast, props and bubbles are drawn on top, each character with a soft ground shadow. The cast is never AI-generated.
- **Prefer a painted backdrop** for most panels; the drawn scenes stay available. Pick by season (`python backdrops.py list`).
  - Library: fall: farm, orchard, leafpark, porch, cornmaze · winter: rink, sledhill, cabin, fireplace · spring: garden · summer: lake, campsite, market · any: playground, library, bakery, bedroom, museum, stage, moon, mainstreet, party.
  - `sky` does nothing on a painted backdrop (build2.py warns). Use `mirror` or a different backdrop for variety. Feet go at the backdrop's `ground` (default 108), which is where the cast stands unless a `y` is given.
- **Never repeat**: a painted backdrop is a scene like any other. Change backdrops, mirror, poses, faces, gear and props from logged strips, and log the backdrop name per panel.
- **Credit:** build2.py adds "Comic backgrounds painted with Grok (xAI)" to the footer and changes "comic is original" to "comic characters are original" on its own. Backdrops are library art, not the edition's one AI illustration (AI illustrations rule).
- **Adding backdrops (through `/newspaper-design` only; the daily run never calls xAI for the comic):** `$REPO/.venv/bin/python scoop/backdrops.py make <name> "<scenery>" --season=fall|winter|spring|summer|any [--ground=N]`. The house style (flat colors, ink outlines, scenery only, no text, open ground at the bottom) is added to every prompt.
  - Scenery only: never people, animals, characters, brands, logos, text or real landmarks, and never family facts in a prompt (prompts go to xAI).
  - Look at every new one before committing (Read the file, and draw a test strip): no letters or faces, open ground for the cast, kid-friendly. If it is wrong, run `make` again with different wording or `remove` it.

## COMIC: PAINTED CHARACTER LIBRARY (Jacob, 2026-10-12) — no API calls in the daily run
- **The cast is painted once and reused every day.** `scoop/sprites/` holds Grok-painted sprites of every character in every pose, every expression (head), every accessory and every held and scene prop. `sprites.py` made them from the art.py drawings, so each sprite sits exactly where the rig draws that part.
- **Daily strips are composed exactly as before**, in edition.json `comic`: any cast + pose + face + gear (with color) + held prop + props + scene. build2.py stacks the painted sprites (art.py `painted_figure`, `painted_prop`), so any combination works: a surprised head on a running body with a red beanie and a scarf. **The daily run never calls Grok for the comic.**
  - Gear colors still work: scarf, beanie, earmuffs, cap, bow, party hat, cape, bow tie and collar are recolored by hue (white, fur and ink stay as painted). Held and scene props with a color option are hue-shifted. Painted Bob always wears his red shirt (`shirt` is ignored). `sfx` text and motion marks (wave, speed, notes, shake) stay drawn.
  - A part not in the library is drawn instead and build2.py prints a `COMIC WARNING`. Fix it by adding the part (below), or pick a painted part. `"paint": false` in `comic` prints the whole strip drawn.
- **Credit:** build2.py adds "Comic characters (or art) painted with Grok (xAI) from the original character designs" to the footer and changes "comic is original" to "comic characters are original" by itself. The library is not the edition's one AI illustration (AI illustrations rule).
- **Never repeat** applies to the composition as before (scene, poses, faces, gear, props); log it the same way.
- **Growing the library (through `/newspaper-design` only):** add the drawing to art.py (a new pose, face, gear item, prop or character with a `LOOKS` line in sprites.py), then `$REPO/.venv/bin/python scoop/sprites.py make <filter>` (e.g. `make body`, `make prop/sled`; about 6¢ a part) and check it:
  - `python sprites.py review out.png <filter>` shows drawn and painted side by side: Read it. Each sprite must match its drawing (pose, expression, item, colors), with nothing added, no text, no stray magenta. Redo a bad one with `make <job> --redo`.
  - `python art.py --sheet cast.html` draws the whole painted library (`--drawn` for the rig).
  - Prompts carry only the drawings and the fixed cast descriptions in sprites.py; never family facts.

## MDA KICKS & GIGGLES (Jacob, Oct 10, 2026)
- A box for Elle's soccer team, **MDA U9G Black** (`mda`). Copy it verbatim from `state.mda`, which `familyops/teams.py` computes, and never hand-write it. When `state.mda` is null, the box does not appear.
- **Only two cards: the last game and the next game or tournament** (Jacob, 2026-10-10). Never list more upcoming games.
  - Last game: the score, from `data/results/elle-mda-*.yaml`, which Jacob supplies with `/family-update`. "Elle scored a goal!" appears only when she scored; zero goals is never mentioned. With no result yet: "LAST GAME · SAT OCT 17 / MDA vs Opponent" and "Final score coming soon." (dropped after 8 days).
  - Next: the next game (opponent, kickoff, arrival time, uniform, field) or tournament, whichever comes first.
- Shown only when there was a game since the last paper or the next game/tournament is within 3 days; otherwise hidden.
- **Format: like a pro sports schedule** (Jacob, 2026-10-10). Each entry is a card with four lines:
  - date and time in small caps ("SAT OCT 17 · 12:30 PM"; "FINAL · SUN OCT 11" for results);
  - the matchup "MDA vs Opponent" (results read "MDA 3, Blackhawks 1", winner in bold);
  - the location as field and city;
  - arrival time and uniform.
  Tournaments read "TOURNAMENT · FRI OCT 23–SUN OCT 25 / Kalahari Cup / Sandusky, OH".
- Monday's paper also reports Saturday's game (Saturday's paper prints before Saturday games, and there is no Sunday paper).
- Elle's games still appear in the family schedule as usual. This box adds the details and results.

## SPARTANS HOOP SCOOP (Jacob, Oct 10, 2026)
- The same box for Ari's basketball team, the **Motor City Evolution (MCE) Spartans** (`spartans`). Copy it verbatim from `state.spartans`, which `familyops/teams.py` computes from `data/schedules/ari-mce-basketball-*.yaml`, and never hand-write it. When `state.spartans` is null, the box does not appear.
- Same rules and format as MDA Kicks & Giggles: only the last game and the next game or tournament; shown only when there was a game since the last paper or the next one is within 3 days; pro-schedule cards ("SAT OCT 17 · 9:55 AM / Spartans vs Hoosiers / Berkshire Middle School, Beverly Hills"); finals read "Spartans 24, Tigers 18", winner in bold.
- **Scores are read automatically from MCE's results page**, https://www.motorcityevolution.com/league-results, where the previous weekend's scores are posted (Jacob, 2026-10-10). `familyops/mce.py` reads it every run. A game counts only under Ari's division heading ("College") with the same date and both team names as his schedule (the Rookie League also has a Spartans). Ari's points come from the recap only when it names "Ari Shapiro" with a number. Anything unclear is left out, never guessed.
- Jacob can also send a score or Ari's points (`data/results/ari-spartans-*.yaml`, via `/family-update`); his entry wins over the page. "Ari scored 6 points!" appears only when he scored; zero is never mentioned. With no score yet: "Final score coming soon."
- Playoff dates without a known opponent read "Spartans · Playoffs (if qualified)"; no time is printed while the league says "Times TBD".

## ARI'S FANTASY TEAM (Jacob, 2026-10-12; replaces the Oct 10 rule)
- **Only Monday, Tuesday, Thursday and the Saturday Weekend Edition, during the NFL season.** Never on Wednesday or Friday. Outside the season (ESPN league inactive, or no current matchup) there is no box.
- The box (`ari_fantasy`) is **copied verbatim from `state.ari_fantasy`**, which `familyops/fantasy.py` (`box()`) computes from Ari's ESPN league. When it is null, the box does not appear. Never hand-write it and never guess a score.
- Content:
  - title "Ari's Fantasy Team: <team name>", then record and standing ("4–0, 1st of 10");
  - the current matchup ("Week 5 vs The Jude Crew") with the score ("Score: 206.6–89.8, leading") and the projected score ("Projected: 211.0–98.2");
  - **Monday and Tuesday also give each team's top performer**: the highest-scoring starter on each side (bench and IR don't count), e.g. "Ari's top player: Jahmyr Gibbs, RB, 37.7 pts" / "Their top player: Trevor Lawrence, QB, 21.7 pts".
- **Tuesday reports the week just played**, even after ESPN has moved on to the next week. Once ESPN marks it final it reads "Final: W 206.6–89.8" and the projection is dropped (it equals the score).
- Kept separate from the NFL-wide "Fantasy Football: Top Performers" list (`fantasy`). Ari's box comes first in the sports column. It is a white bordered box (`.plain`), never shaded.

## PHOTO SOURCES (Jacob, 2026-10-12) — for the headline photo, Cutest Critter and pictures in extras
- **Use `photos.py` first.** Run the repo's copy, `$REPO/.venv/bin/python $REPO/scoop/photos.py ...`, not the work-dir copy (it reads the repo's content log to skip pictures already used). It searches two free sources, skips anything already used, downloads the picture and prints the credit:
  - `python photos.py openverse "red panda"`: **Openverse** (openverse.org) real photographs, reusable licenses only (CC0, public domain, CC BY, BY-SA, BY-NC, BY-NC-SA; never "no derivatives", since the page crops).
  - `python photos.py nga "autumn landscape" --kind=painting`: **National Gallery of Art** open-access artworks (public domain, free to use). nga.gov blocks scripts, so the helper reads NGA's open data on GitHub; the first search in a run takes about 25 seconds.
  - `python photos.py get openverse|nga <id> <file.jpg>` downloads one and prints `{"img", "credit", "log"}`. Copy `img` and `credit` into edition.json as given.
- Then Wikimedia Commons, NASA or a zoo press page, as before. If nothing suitable turns up, no picture (New Standing Rule 3).
- **Look at every picture before using it** (Read the downloaded file): it must show what the caption says, be kid-friendly and be sharp at print size. Never use a picture with a watermark, a logo or a recognizable child.
- **Openverse photos are general, not news photos.** A photo of a giraffe can go with a zoo story, but its caption describes what the photo shows; never present it as the event itself.
- **NGA artworks are art, never a photo:** never the Cutest Critter or a headline "photo". Use one as a picture in an extra, e.g. "Art Corner: <title>", with 2–3 kid-friendly sentences about the painting (who painted it, when, something to spot) that are true and taken from NGA's own description.
- **Credit every picture** with the helper's credit line (photographer / source, license; or artist, title, date, National Gallery of Art) in its `credit` field; it prints in the footer, never under the picture.
- **Never repeat a picture:** add the helper's `log` tag (`openverse:<id>` or `nga:<uuid>`) to the day's content-log.md entry. The helper skips any tag already in the log.

## AI ILLUSTRATIONS (Jacob, 2026-10-12)
- **Only for fun, non-news extras:** a weekend activity idea, a fun fact, This Week in History and the like. Never the headline story, news items, Tech Corner, the Cutest Critter, sports, or anything about a real event, place or person: those stay real photo or nothing (New Standing Rule 3).
- **At most one per edition.** Make it with `$REPO/.venv/bin/python $REPO/scoop/illustrate.py "<subject>" <file.jpg>` (xAI's Grok image API; the house kids'-picture-book style is added to every prompt). Copy its `img` and `illus: true` into the extra.
- **The page labels it.** build2.py prints "Illustration" on the picture and credits Grok in the footer by itself. On days with one, `foot` says "Comic is original" instead of "Illustrations and comic are original".
- **Subject:** a scene with animals, objects, nature or kids in general. Never real or famous people, family members, recognizable children, brands, logos, characters from movies, TV, books or games, or text in the picture. **Never put family facts (names, school, schedule) in a prompt**: prompts go to xAI.
- **Look at it before using it** (Read the file): it must match the subject, be kid-appropriate and sharp, with no garbled letters, odd hands or faces. If not, try once more with different wording, then run the extra without a picture.
- **Log** the helper's `log` tag in content-log.md and never repeat a subject.
- If `XAI_API_KEY` is missing or the call fails, run without the picture and say so in the run report.

## PUBLISHING SCHEDULE (Jacob, Oct 10, 2026) — overrides anything below that conflicts
- **Monday–Friday:** the regular daily edition.
- **Saturday:** a **Weekend Edition** that covers Saturday AND Sunday. Set `edition` to "Weekend Edition" and `date` to "Saturday & Sunday, October 17–18, 2026".
  - `sched_title` = "This Weekend"; `sched` lists both days, each item led by its day and time ("<b>Sat 9:30 am</b> — ...").
  - `week_title` = "Next Week"; `week` = Mon–Fri highlights (half days, no-school days, games).
  - Weather: `wx` = Saturday, `wx2` = Saturday night + Sunday; `forecast` = the 4 days from Sunday.
  - **No school lunch anywhere in the Weekend Edition** (Jacob, 2026-10-10): omit `lunch` and `lunch_title`. The weather box then spans the full width.
  - Sports: `yday_title` = "Friday's Scores"; `tonight_title` = "This Weekend in Detroit", with Saturday and Sunday Detroit games and the kids' weekend games; `lions` = a preview of the weekend game.
  - Stories lean toward fun weekend things to do (Birmingham first, then Detroit/Michigan). The Saturday Tech Corner still applies.
- **Sunday:** no newspaper. Do not build, print or log anything. (The digest email still goes out every day.)

## NEW STANDING RULES (Jacob, Oct 8, 2026) — these OVERRIDE anything below that conflicts
1. **Unconfirmed = silent.** If a score, Lions item, tonight's game or high-school result cannot be confirmed in a second source, leave it out completely. NEVER print "not confirmed", "not posted", "no scores confirmed", "no game found" or any placeholder. Set the field to an empty list/string (yday: [], lions: "", tonight: [], hs: []); build2.py skips empty sections and their headings. Print only confirmed facts.
2. **Forecast row = 4 days** (starting tomorrow), not 5. Never print a blank "—" day.
3. **Headline art: real photo or nothing.** Never draw, generate or stipple an illustration for the headline. (AI illustrations are allowed only in fun extras: see AI illustrations.) If a real photograph for the story can be obtained (a freely licensed image fetchable in the shell; see Photo sources), set `head_photo` in edition.json to {"img": "<local path>", "credit": "<photographer / source>"}. If not, omit `head_photo`: the story simply has no photo. Mention it in the run report only.
4. The comic stays original art (ARTIC, BIG BEAR & FRIENDS) with a new gag AND new drawings each day (see Comic: Character Library).
5. In the NEVER REPEAT list below, ignore item 2 (hedcut scene); log "photo: <credit>" or "no photo" instead.

## NEVER REPEAT (standing rule from Jacob, Oct 7, 2026) — applies every day
Nothing may repeat from any earlier edition: not articles/stories, not photos/illustrations, not the comic (text AND drawings), not jokes/words.
1. **Before building**, read `logs/content-log.md` and `logs/riddle-log.md`. Pick a headline story, news items, tech story and critter photo that are not in the logs (a new story on the same topic/event counts as a repeat).
2. (Retired: no headline illustration. See New Standing Rule 3.)
3. **Comic: new drawings every day, not just new text.** In edition.json `comic`, change the scene, props, poses, faces, gear and cast from any logged strip (see Comic: Character Library). A new gag on the same artwork is a repeat. Log the art as described there.
4. **Critter photo**: never reuse a photo or animal already in the log.
5. **After printing**, append today's entry to content-log.md (headline, news items, tech story, headline photo credit or "no photo", comic gag + art description, critter, and the `log` tag of every picture from photos.py) and the joke and word to riddle-log.md (format since 2026-10-10: "YYYY-MM-DD | joke | word"; no riddles).

## Build
1. Make a work dir and copy `scoop/` into it (`cp -r scoop/. <workdir>/`).
2. `sh setup.sh` (installs fonts into ./fonts via npm; installs playwright if missing; Chromium is preinstalled — never run playwright install).
3. Write edition.json (schema below).
4. `FONTDIR=./fonts $REPO/.venv/bin/python build2.py && $REPO/.venv/bin/python render.py newspaper.pdf` ($REPO = the family-ops checkout; `sh $REPO/scripts/bootstrap.sh` creates `.venv`).
5. render.py prints one "content bottom / column bottom" pair per column. Every content value must be <= its column bottom (~830); aim for <= ~800 so nothing is clipped (check the PNG: the word and joke boxes and the last items must be fully visible). If a column overflows, shorten text (never shrink fonts). Run `pdfinfo newspaper.pdf | grep Pages` — must be 1. Look at a PNG (`pdftoppm -r 100 -png`) for clipping.

## edition.json fields
date ("Tuesday, October 6, 2026"), hi (temp number), wx (HTML: high/wind/morning low), wx2 (tonight + tomorrow, italic line), **forecast** (4 entries [day, high, low, short conditions], starting with tomorrow, from the NWS forecast; trust the weekday names, the NWS text page sometimes prints the wrong date next to them; a "—" low is OK for the first day only), lunch (HTML; on Thursdays append the bagel note), sched (list of "<b>time</b> — event" HTML strings, today only), week ("Coming Up", next ~5 days, short), quarton (list of Quarton/school-note strings), yday (list of [label, "Team X, Team Y N"] — previous day's confirmed results only; [] if none), lions (short Lions report, "" if unconfirmed), **fantasy** (optional list of short HTML lines), tonight (list of today's confirmed Detroit games; [] if none; add a kids' game as a bullet when a child has one that evening), hs (Seaholm & Groves, short bullets, confirmed only; [] if none), head/sub/story[3 paragraphs]/head_src (headline story; head_src is not printed: credit the outlet in `foot`), **head_photo** (optional {"img": "<local path to a real photo>", "credit": "...", "h"?: max height in px, default 190}; shown under the subhead, credit in the footer; omit if no real photo), news[0..2] each [headline, text, source] (the source is not printed: credit it in `foot`; news[1] sits center under headline, news[0] right column, news[2] left column), **critter** (optional {"img": "<local path to a real photo file>", "name": "Baby Red Panda", "fact": "one short true fact", "credit": "photographer / source"}; the credit prints in the footer; replaces news[2] in the left column; NEVER a drawing), **word** ([word, part of speech, kid-friendly definition, short example sentence]; a NEW word each day), **extras** (optional list of filler items: {title, text, img?, credit?, illus?, img_h?}; `img` = a local picture from Photo sources, shown under the title (its `credit` prints in the footer), or an AI illustration with `illus: true` (labeled on the page; see AI illustrations), cropped to `img_h` px tall (default 130); no drawing activities; placed in `layout` as `extra:N`, or `extras` for all unplaced), **mda** (optional {title, items[]} copied from state.mda; omit when null), **spartans** (optional {title, items[]} copied from state.spartans; omit when null), **ari_fantasy** (optional {title, items[]} copied verbatim from state.ari_fantasy; omit when null), **banner** (optional list of short strings for the strip under the masthead: holidays; on Fridays only, Shabbat with sunset time), **featured_art** (optional {"img", "title", "artist", "note"?}; normally left out: build2.py fills it from `featured/queue.json` on its date; see Featured artwork; never put it in the sample edition.json, which is copied daily), **layout** (optional: {"columns": [{"width": "1.85in", "sections": [...]}, ...]}; sections: featured, schedule, week, school_notes, left_story, lead, news1, word, joke, ari_fantasy, spartans, mda, sports, news0, extra:N, extras; lead and word must be placed; default = schedule/week/school_notes/left_story | lead/news1/word/joke | ari_fantasy/spartans/mda/sports/news0 at 1.85in / 3.95in / 2.1in), **optional labels**: edition (masthead, default "Daily Edition"), sched_title (default "The Family Schedule"), lunch_title ("Today's School Lunch"), week_title ("Coming Up"), yday_title ("Yesterday's Scores"), tonight_title ("Tonight in Detroit"), joke (with punchline), foot (footer sources line: the only place sources are credited; picture credits are added automatically), **comic** (the day's strip: {"paint"? (false = print the drawn strip instead of the painted library), "panels": [4 × {"scene" (a drawn or painted scene), "sky"? (drawn scenes only), "mirror"?, "caption"?, "cast": [{"who", "x" (0–200), "pose", "face", "gear"? {item: true or a color}, "hold"?, "hold_opt"? (color), "shirt"? (Bob only), "flip"? (default: faces the panel center), "s"? (size)}], "props"? [[name, x, y?, size?, option?]], "say": [{"who", "text", "kind"?, "x"?, "y"?}]}]}; see Comic: Character Library).

## Standing requests from Jacob
- **Sports accuracy.** Use the official or primary source for each league and confirm every score in a second source (CBS Sports, MLB.com, NHL.com, ESPN recap pages via search; ESPN scoreboard is blocked in WebFetch). Never use memory or aggregated summaries. Check winner, loser and final score together. Print only what is confirmed; otherwise say nothing (see New Standing Rule 1). Same for Lions, tonight's games and Seaholm/Groves.
- Overall font size is 7.8pt body in build2.py. Keep text short enough to fit; do not shrink fonts.
- 4-day forecast row sits under the weather line.
- Word of the Day (with definition and example) sits above the joke and stands out (see Design & Content Updates).
- **Thursday bagel day.** On Thursdays, add to the lunch box: "Bagel Day! Bagels are delivered to students in their classrooms every Thursday morning." Applies on school days only.
- **Fantasy football top performers** (`fantasy` field; omit on other days). Only the day after football games: Monday list 5–6 players; Tuesday and Friday list about 3. Standard (PPR) scoring from an official source, each player's team and stat line confirmed in a second source; print only what is confirmed. One short line each, e.g. "<b>Josh Allen</b>, QB BUF, 34.2 pts". When present, build2.py drops the right-column news[0] story to make room.
- **Cool kids' technology story, Wednesdays and Saturdays.** Make news[1] a kid-focused tech story (robots, space tech, AI explained simply, gadgets, coding, engineering), headline starting "Tech Corner:". Sources: Science News Explores, NASA, Wired, Popular Science, Smithsonian Magazine, TIME for Kids. ~60–80 words, own words, source credited in the footer, no repeats.
- **"Cutest Critter" PHOTOGRAPH, Tuesdays and Fridays.** Real photograph, NOT a drawing. A freely licensed photo (Openverse via `photos.py` first, then Wikimedia Commons, NASA, a zoo press page; see Photo sources). If none can be obtained, omit `critter` and say so in the run report. Caption = animal name + one short true fact + credit. ~150px tall.

## Rules (user-approved layout)
- Masthead "The Fairfax Daily Scoop" (Grenze Gotisch); columns are flexible (see Design & Content Updates); the comic strip stays at the bottom ("ARTIC, BIG BEAR & FRIENDS", composed by edition.json `comic` from the painted character library on Grok-painted backdrops; see Comic: painted character library and Comic: painted backdrops).
- Stories: only fun, kid-friendly, on a balanced mix of topics with one local (Birmingham MI, else Detroit/Michigan) article in every edition (see Balanced news, one local story). Headline story ~3 short paragraphs, with a real photo only if one can be obtained (see New Standing Rule 3).
- No third-party characters. The comic is original; NEW 4-panel gag AND new artwork each day in edition.json `comic` (keep text short so bubbles fit).
- Kids' sports appear in the family schedule, plus as a game under "Tonight in Detroit" when that evening. Elle's MDA soccer and Ari's Spartans basketball also have their own boxes (MDA Kicks & Giggles, Spartans Hoop Scoop; above).
- Daily joke: new each day, kid-friendly, never repeat riddle-log.md. No riddle (Jacob, 2026-10-10). After building, append today's joke and word to riddle-log.md.
