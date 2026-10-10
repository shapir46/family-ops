# How to give inputs (for Jacob)

Everything runs from one private repo, `shapir46/family-ops`. You talk to it by starting a **Claude Code session** on that repo: in the Claude app, open Code, start a new session and pick **family-ops**. Begin your message with one of four commands. The command tells Claude which part of the project to touch, so it loads only that part. That keeps sessions small and cheap, and every change lands in the same place.

## The four commands

| Start with | Use it for | Examples |
|---|---|---|
| **`/family-update`** | Facts, schedules, calendars, corrections, "include/drop this" rules | "Elle's soccer moved to Tuesdays." "Here's Temple Israel's calendar" (attach the PDF or a photo). "Leo started swim on Thursdays 5pm at Lifetime." "The digest said Ari for flag football, it's Elle." |
| **`/newspaper-design`** | How the Scoop looks or what kind of content it carries | "Bigger weather graphic." "Add a Halloween countdown box." "Drop high-school volleyball." "Make the comic three panels." |
| **`/digest-format`** | How the daily email reads or is organized | "Put Needs Action first." "Shorter FYI section." |
| **`/dashboard-design`** | The live dashboard and, later, the family wall device | "Add a week view." "Wall mode: bigger clock." |

Family data is entered once and shared everywhere. Tell `/family-update` that Ari has a new practice, and it appears in the email, the newspaper and the dashboard. You never repeat it per output. Design commands never change facts, and `/family-update` never changes design, so the two can't drift apart.

## Tips that keep it efficient
- **One session per topic.** Start a fresh session for each batch of changes rather than one endless chat. Long sessions re-read everything and cost more.
- **Batch your updates.** Five changes in one message is one pass; five messages is five passes.
- **Send the document, don't retype it.** Attach the PDF, screenshot or photo of a calendar. Claude extracts every date, checks each weekday, and asks only about anything unclear.
- **Corrections are the most useful input.** "The digest got X wrong" becomes a rule, so it doesn't happen again.
- **You'll get a short confirmation:** what changed, where it lives, and "takes effect tomorrow morning". For design changes you'll see a preview image first.

## What you never need to do
- Edit routine prompts. The daily routine just says "run the digest per the repo", so all changes go through the commands above.
- Put passwords or private links in chat. Tokens and private feed links go in the environment settings at claude.ai/code (cloud button → Default → gear).

## The daily run
The Claude Code routine **Family digest** runs at about 6:30 AM ET. It emails the digest to you and Rebekah, files the mail and prints the Scoop. Your inputs through the four commands above take effect on its next run. The old Cowork routine was retired on Oct 10, 2026: it is turned off, not deleted.
