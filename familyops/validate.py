"""Checks that run before anything leaves the house. Each returns a list of problems; empty = OK."""
from __future__ import annotations

import os
import re
from datetime import date
from html.parser import HTMLParser

JACOB = "jacob@ivanhoecompanies.com"
REBEKAH = "rebekah.shapiro@gmail.com"

MONTHS = {m: i for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct",
                                      "Nov", "Dec"], 1)}
_PAIR = re.compile(r"\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,?\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(\d{1,2})\b")

# Bus and SACC content never applies (data/family.md). "Bike Bus" is a bike ride and stays.
_BUS = re.compile(r"\b(school bus|bus route|busing|bussing|busses|buses|stopfinder|no bus)\b", re.I)
_SACC = re.compile(r"\b(SACC|kids club|school age child care|drop-in care)\b", re.I)

# URLs that carry a credential must never be re-sent (family-digest skill, Extract links).
_CRED_URL = re.compile(r"login_link=|[?&]ctt=|[?&](token|auth|session|jwt|pwd|password|reset)=|calendar\.playmetrics\.com|"
                       r"passcode", re.I)

ALLOWED_TAGS = {"h2", "h3", "p", "ul", "ol", "li", "a", "b", "strong", "i", "em", "br"}


def weekday_pairs(text: str, today: date) -> list[str]:
    """Every 'Tue, Oct 13' must be a real weekday/date in the year nearest `today`."""
    probs = []
    for m in _PAIR.finditer(text):
        wd, mon, day = m.group(1), MONTHS[m.group(2)], int(m.group(3))
        cands = []
        for y in (today.year - 1, today.year, today.year + 1):
            try:
                cands.append(date(y, mon, day))
            except ValueError:
                pass
        if not cands:
            probs.append(f"impossible date: {m.group(0)}")
            continue
        d = min(cands, key=lambda c: abs((c - today).days))
        if f"{d:%a}" != wd:
            probs.append(f"weekday mismatch: '{m.group(0)}' is really {d:%a}, {d:%b} {d.day}")
    return probs


def excluded_topics(text: str) -> list[str]:
    plain = re.sub(r"bike bus", "", text, flags=re.I)
    return [f"bus/SACC content: '{m.group(0)}'" for rx in (_BUS, _SACC) for m in rx.finditer(plain)]


def secrets(text: str) -> list[str]:
    probs = [f"credential-bearing URL or passcode: '{m.group(0)}'" for m in _CRED_URL.finditer(text)]
    for var in ("RELAY_TOKEN", "PLAYMETRICS_ICS_URL"):
        v = os.environ.get(var)
        if v and len(v) > 8 and v in text:
            probs.append(f"{var} value appears in the output")
    return probs


class _Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags, self.problems, self._a = [], [], None

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        if tag == "a":
            self._a = dict(attrs).get("href", "")
            if not self._a:
                self.problems.append("link without href")

    def handle_endtag(self, tag):
        if tag == "a":
            self._a = None

    def handle_data(self, data):
        if self._a is not None and re.match(r"\s*https?://", data):
            self.problems.append(f"raw URL as link text: {data.strip()[:60]}")


def email_html(html: str) -> list[str]:
    p = _Tags()
    p.feed(html)
    probs = list(p.problems)
    bad = sorted(set(p.tags) - ALLOWED_TAGS)
    if bad:
        probs.append(f"tags the Outlook connector strips or the phone layout forbids: {', '.join(bad)}")
    for href in re.findall(r'href="([^"]*)"', html):
        if re.search(r"&(?!amp;|#\d+;|[a-z]+;)", href):
            probs.append(f"unescaped & in href: {href[:60]}")
    return probs


def recipients(to: list[str], shadow: bool) -> list[str]:
    got = {a.strip().lower() for a in to}
    if shadow:
        return [] if got == {JACOB} else [f"shadow mode must send to {JACOB} only, got {sorted(got)}"]
    want = {JACOB, REBEKAH}
    return [] if got == want else [f"live recipients must be {sorted(want)}, got {sorted(got)}"]


def outgoing(html: str, to: list[str], today: date, shadow: bool) -> list[str]:
    """Everything that must hold before the digest email is sent."""
    text = re.sub(r"<[^>]+>", " ", html)
    return (recipients(to, shadow) + email_html(html) + weekday_pairs(text, today) + excluded_topics(text)
            + secrets(html))
