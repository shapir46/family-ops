# dashboard/: live family view (not built yet; plan in docs/architecture-v2.md)

Change it through `/dashboard-design`.

- **Data contract:** render from `state/YYYY-MM-DD.json` only, the same record the email and newspaper use. Need something new? Add the field in `familyops/` with a test. Never compute or hard-code family facts in the page.
- **Design tokens:** kid colors and initials from `data/family.yaml`.
- **Hosting:** Jacob's Mac mini (the machine behind print.shapbox.com), behind a login for Jacob and Rebekah.
- **Modes:** phone first (390 px wide); later a wall/family-device mode with large type, auto-refresh and no buttons.
- **Done checkmarks:** stored on the Mac mini; the next daily run reads them so finished items drop out of Needs Action.
