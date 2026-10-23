"""No-login link to a day's newspaper on the Mac mini print relay (Jacob, 2026-10-12).

The relay serves GET /paper/YYYY-MM-DD?sig=<first 32 hex of HMAC-SHA256(PAPER_LINK_KEY, "YYYY-MM-DD")>, so the
digest can carry the link before the paper exists (the relay shows a "not ready yet" page until it is printed).
PAPER_LINK_KEY comes from the cloud environment only: never print, log or commit it. The link itself is fine to email.
Without the key, fall back to the private GitHub archive link.
"""
from __future__ import annotations

import hashlib
import hmac
import os
from datetime import date

RELAY = "https://print.shapbox.com/paper/{d}?sig={sig}"
GITHUB = "https://github.com/shapir46/family-ops/blob/main/editions/{d}.pdf"


def sig(key: str, d: date) -> str:
    return hmac.new(key.encode(), d.isoformat().encode(), hashlib.sha256).hexdigest()[:32]


def link(d: date, key: str | None = None) -> str:
    key = key if key is not None else os.environ.get("PAPER_LINK_KEY", "")
    if not key:
        return GITHUB.format(d=d.isoformat())
    return RELAY.format(d=d.isoformat(), sig=sig(key, d))
