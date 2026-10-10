---
name: overview
description: Purpose, portfolio scope, current build state, and what's next for Jacob's Outlook productivity system
sources: [backfill, cowork]
aliases: [outlook-productivity-system, m365-outlook-system]
---

- [stated] Jacob is a real estate operator and investor working across multiple residential properties
- [stated] Portfolio: Greens Lake, Windsor Woods, Warren Village, Townes at Trail, and The Grove (a Pulte development deal)
- [stated] Building a comprehensive productivity system using Claude Cowork integrated with Microsoft 365 Outlook to streamline email triage, response drafting, daily digests, and project tracking across his portfolio
- [stated] Jacob is a Microsoft Entra admin for his tenant, which matters when write permissions need to be granted for the M365 connector

## Current state

- [stated] Phase 1 of the Outlook productivity system is complete
- [stated] Property categories created in Outlook for tagging emails by property/deal: Greens Lake (blue), Windsor Woods (teal), Warren Village (purple), Townes at Trail (orange), The Grove (green)
- [stated] Categories are used rather than folders because the M365 connector supports categories and inbox rules but cannot create folders directly
- [stated] Folders created manually by Jacob: Deals-Inbound (CRE deal blasts, for weekly batch review), News-Digest (newsletters, for daily digest), Voicemail (Ruby Receptionist + Qualitech notifications)
- [stated] Inbox rules established to auto-route future mail
- [stated] Historical deal blasts, Ruby voicemails, and Qualitech voicemails swept into their respective folders

## On the horizon

- [stated] Phases 2–6 of the Claude Cowork productivity system: email response drafting, daily digest generation, and property/deal project tracking
- [stated] Ongoing inbox maintenance as new senders and deal sources emerge
- A daily scheduled task now scans the main Inbox each evening for unanswered correspondence (excluding Deals-Inbound/News-Digest/Voicemail and automated mail) and drafts replies in Outlook Drafts for Jacob to review and send himself; it then sends Jacob a summary (for=code)

## Tools & resources

- [stated] Claude Cowork with the Microsoft 365 Outlook connector (read, category creation, inbox rule creation; folder creation is not supported — folders must be created manually by Jacob)
- [stated] Microsoft Entra — Jacob is admin; `MailboxSettings.ReadWrite` scope required for write operations
- [stated] Ruby Receptionist (call logs via noreply@ruby.com) and Qualitech (voicemails via voicemail@qualitech.net)
- [stated] CRE platforms: GP-LP Match (gplpmatch.com), RCM1, Northmarq, Crexi, Kiser Group
- [stated] News sources: Crain's Detroit, CoStar, Axios, Oakland Press, Free Press, Multifamily Insiders