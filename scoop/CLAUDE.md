# scoop/: the Fairfax Daily Scoop (newspaper)

Change it through `/newspaper-design`. **`README.md` is the rule book**: standing rules, never-repeat rules and the `edition.json` field list. It overrides the daily-scoop skill.

- `build2.py`: page layout and CSS, rendered from `edition.json`
- `art.py`: the comic character library (Artic, Big Bear, Mackenzie, Uni, Bob: poses, faces, gear, props, drawn and painted scenes). Daily strips are data in `edition.json` `comic`; `python art.py --sheet cast.html` draws the model sheet
- `render.py`: HTML to a one-page Letter PDF, plus the overflow check
- `photos.py`: finds and downloads free pictures (Openverse photos, National Gallery of Art open-access art) with their credit lines (README: Photo sources)
- `illustrate.py`: one AI illustration (xAI Grok) for a fun extra, labeled on the page (README: AI illustrations)
- `backdrops.py`, `backdrops/`: painted comic backdrops (xAI Grok), made once and committed (README: Comic: painted backdrops)
- `sprites.py`, `sprites/`: the painted character library (every pose, face, gear item and prop, painted once by Grok); the daily comic stacks these, no API call (README: Comic: painted character library)
- `setup.sh`: fonts into `./fonts`
- `edition.json`: a sample edition (schema and style example only)
- `hedcut.py`: retired, never used

Family content (schedule, lunch, school notes) comes from `state/*.json`. Never hard-code family facts here. Kid colors and initials come from `data/family.yaml`. Logs of past editions are in `logs/`.
