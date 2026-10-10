---
name: outlook-operating-instructions
description: Working rules and gotchas for organizing Jacob's Outlook inbox via the M365 connector — read before any category, rule, or move operation
sources: [backfill]
aliases: [inbox-organization, m365-connector-notes]
---

- [stated] Tag emails by property/deal using Outlook categories, not folders — the M365 connector supports categories and inbox rules only; folders must be created manually by Jacob
- [stated] Route CRE deal-blast senders to Deals-Inbound (weekly batch review); news/newsletter sources to News-Digest
- [stated] To get a folder ID: have Jacob manually drag one email into the target folder, search via `outlook_email_search`, then extract `parentFolderId` via `read_resource` — never use folder names as move targets; always use the raw folder ID
- [stated] Always use the raw `id` field from message metadata when referencing messages — never the percent-encoded `webLink` field, which causes silent move failures
- [stated] Historical sweeps: after each batch move, re-query with `folderName + sender` to confirm the remaining count before fetching the next batch; re-querying avoids double-move errors since moved messages drop out of results
- [stated] Use `senderContains` on domain (not `fromAddresses`) for inbox rules on broker platforms that send from many local parts on the same domain; always include `stopProcessingRules: True`
- [stated] If category or rule creation silently fails: grant admin consent for `MailboxSettings.ReadWrite` on both "M365 MCP Server for Claude" and "M365 MCP Client for Claude" in Entra Enterprise Applications, then disconnect and reconnect the M365 connector in Claude settings to refresh the token