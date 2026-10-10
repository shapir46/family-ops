---
name: digest-format
description: Change the layout, wording, section order or tone of the daily Family Digest email (not its facts). Use when Jacob says the email should look, read or be organized differently.
---

# Digest email format

Scope: the formatting rules of the family-digest skill: Step 4 (sections) and Step 5 (mobile HTML). To change what the digest knows or drops (facts, kids, schedules, include/exclude rules), use `/family-update` instead.

## Steps
1. **Restate the request** as one rule.
2. **Edit only** Step 4 / Step 5 of `.claude/skills/family-digest/SKILL.md`. Read the file fully before writing, change it with an exact string replacement, and never truncate it.
3. **Check the result:**
   - Write a short sample digest in the new format to the scratchpad.
   - Run `./fo check-email --html <file> --to jacob@ivanhoecompanies.com --shadow`. It must say OK.
   - Show Jacob the sample.
4. **Run `./fo test`.** It includes a guard that every digest step is still present. Then commit and push.
