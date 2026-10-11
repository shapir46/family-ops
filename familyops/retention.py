"""Carry-forward rules for the Outlook Family-Digest/Processed folder (family-digest skill, Steps 1b and 6).

Categories: Digest-First-YYYY-MM-DD (first digest it appeared in), Digest-Hold-YYYY-MM-DD (latest future date in it).
"""
from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Iterable, Optional

UNDATED_DAYS = 7


def _cat_date(cats: Iterable[str], prefix: str) -> Optional[date]:
    for c in cats:
        if m := re.fullmatch(rf"{prefix}-(\d{{4}}-\d{{2}}-\d{{2}})", c.strip()):
            return date.fromisoformat(m.group(1))
    return None


def first_seen(cats: Iterable[str]) -> Optional[date]:
    return _cat_date(cats, "Digest-First")


def hold(cats: Iterable[str]) -> Optional[date]:
    return _cat_date(cats, "Digest-Hold")


def undated_live(cats: Iterable[str], today: date) -> bool:
    """Undated content shows for 7 days from first digest; exactly 7 days old is expired."""
    f = first_seen(cats)
    return f is None or (today - f).days < UNDATED_DAYS


def dated_live(item_date: date, today: date) -> bool:
    return item_date >= today


def expired(cats: Iterable[str], today: date) -> bool:
    """Expiry rule: no live Hold date AND first seen 7+ days ago. Used only to COUNT expired Processed messages for the run report (Step 6c); nothing is ever deleted or moved (Jacob, 2026-10-11)."""
    cats = list(cats)
    f = first_seen(cats)
    if f is None:
        return False
    h = hold(cats)
    return (h is None or h < today) and (today - f).days >= UNDATED_DAYS


def new_categories(today: date, item_dates: Iterable[date]) -> list[str]:
    """Categories for a message filed today: Digest-First, plus Digest-Hold for its latest future date."""
    cats = [f"Digest-First-{today.isoformat()}"]
    future = [d for d in item_dates if d >= today]
    if future:
        cats.append(f"Digest-Hold-{max(future).isoformat()}")
    return cats


def group_for_filing(messages: dict[str, list[str]], batch: int = 5) -> list[tuple[list[str], list[str]]]:
    """{message_id: categories} -> [(ids, categories)] with identical category sets, at most `batch` ids per call."""
    groups: dict[tuple, list[str]] = {}
    for mid, cats in messages.items():
        groups.setdefault(tuple(sorted(cats)), []).append(mid)
    out = []
    for cats, ids in groups.items():
        for i in range(0, len(ids), batch):
            out.append((ids[i:i + batch], list(cats)))
    return out
