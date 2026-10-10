---
name: daily-digest-system
description: Personal daily digest system for family and business updates
sources: [backfill]
aliases: [daily digest]
---
- [stated] Family digest architecture: Proton Mail auto-forwards family sender emails to digest@shapfam.com (M365 shared mailbox); Claude Cowork scheduled task reads via M365 MCP, summarizes by child, saves dated markdown to OneDrive-synced folder, emails digest to Proton address
- [stated] Slack chosen as delivery channel for the business digest (daily financial/news/market aggregation)
- [stated] Integrates Office 365 + ProtonMail
- [stated] Weekly Metro Detroit residential development brief (scheduled task, Tuesdays; reads Outlook News-Digest folder, files to News-Processed): wants it emailed to jacob@ivanhoecompanies.com each run, not just delivered in chat
- [stated] Setting up a daily printed newspaper (PDF) sent via his own print relay at print.jacobshapiro.net (curl POST with bearer token) to the printer on his Mac mini; also has a UniFi drive on that computer