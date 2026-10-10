# data/: the family's single source of truth

Everything the digest, newspaper and dashboard know about the family lives here, and nowhere else. Change it through `/family-update`.

| File | Holds |
|---|---|
| `family.yaml` | Kids (grade, school, teacher, color, initial, which district audiences apply), congregation, Sunday School kids. Colors and initials are the shared design tokens for every output. |
| `family.md` | Rules that need words: child attribution, the bus/SACC exclusion, what to drop |
| `calendars/*.yaml` | Year calendars as data (`date`, optional `end`, `kind`, `audience`/`kids`, `label`). Prose originals (e.g. `bps-calendar-2026-27.md`) are kept only while a routine still reads prose. |
| `schedules/*.yaml` | Activity and league schedules (`kids`, `location`, `events[]`). The `.md` twin, where present, is the human-readable copy; keep both in sync. |
| `lunch-menus.yaml` | One BPS lunch PDF URL per month (added automatically) |

## Conventions
- Every fact carries who confirmed it and when: `(Jacob, 2026-10-10)` or the source document's name.
- Dates are ISO (`2026-10-18`). Times are 24-hour (`"09:30"`). Kids are written exactly `Ari`, `Elle`, `Leo`, `Lila`.
- Removing something removes its file and every rule that mentions it (history stays in `docs/`).
- `./fo test` checks the calendars against their sources and checks weekday/date pairs. It must pass before you push.
