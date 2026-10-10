---
name: dashboard-design
description: Build or change the family dashboard (the live view for Jacob and Rebekah, and later the wall/family device). Use for any dashboard layout, sections, interactions or device-mode request. Works in dashboard/ only and reads the shared family data; it never edits family facts.
---

# Dashboard design

Scope: `dashboard/` only. Read `dashboard/CLAUDE.md` first. The dashboard renders the day's `state/*.json` (built by `./fo collect` plus the digest run), so its data is identical to the email's and the newspaper's. To change facts, use `/family-update`.

## Steps
1. **Restate the request** in one line.
2. **Change only `dashboard/`.** Kid colors and initials come from `data/family.yaml`. Reuse them; never invent new ones.
3. **Preview:**
   - Render the page against the latest `state/*.json`, or a sample if none exists.
   - Take a screenshot with Playwright (Chromium at `/opt/pw-browsers/chromium`) at phone width (390 px). For wall mode, also take one at tablet landscape (1180 px).
   - Send the screenshots to Jacob.
4. **Fields:** if the dashboard needs a field that `state.json` lacks, add it in `familyops/` (with a test) rather than computing facts in the page.
5. Commit and push to `main`. Deploying to the Mac mini is Jacob's step until a deploy script exists; say so in the reply.
