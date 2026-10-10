"""ICS feeds: parse, expand recurrences into a date window, normalize to America/Detroit."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from dateutil.rrule import rrulestr

from . import TZ

LOCAL = ZoneInfo(TZ)


@dataclass
class IcsEvent:
    uid: str
    summary: str
    start: datetime | date          # aware datetime in America/Detroit, or a date for all-day
    end: Optional[datetime | date]
    location: str
    description: str
    status: str

    @property
    def all_day(self) -> bool:
        return not isinstance(self.start, datetime)

    @property
    def day(self) -> date:
        return self.start if self.all_day else self.start.date()


def _unfold(text: str) -> list[str]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"\n[ \t]", "", text).split("\n")


def _unescape(v: str) -> str:
    out, i = [], 0
    while i < len(v):
        if v[i] == "\\" and i + 1 < len(v):
            out.append({"n": "\n", "N": "\n"}.get(v[i + 1], v[i + 1]))
            i += 2
        else:
            out.append(v[i])
            i += 1
    return "".join(out)


def _parse_dt(params: dict, value: str) -> datetime | date:
    value = value.strip()
    if params.get("VALUE") == "DATE" or re.fullmatch(r"\d{8}", value):
        return datetime.strptime(value[:8], "%Y%m%d").date()
    if value.endswith("Z"):
        return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=ZoneInfo("UTC")).astimezone(LOCAL)
    dt = datetime.strptime(value, "%Y%m%dT%H%M%S")
    return dt.replace(tzinfo=ZoneInfo(params.get("TZID", TZ))).astimezone(LOCAL)


def _props(block: list[str]):
    for line in block:
        if ":" not in line:
            continue
        head, value = line.split(":", 1)
        name, *ps = head.split(";")
        params = dict(p.split("=", 1) for p in ps if "=" in p)
        yield name.upper(), params, value


def parse(text: str) -> list[dict]:
    """Raw VEVENTs (VTIMEZONE blocks, which carry their own RRULEs, are ignored)."""
    events, cur, depth_other = [], None, 0
    for line in _unfold(text):
        if line == "BEGIN:VEVENT":
            cur = []
        elif line == "END:VEVENT" and cur is not None:
            events.append(cur)
            cur = None
        elif cur is not None:
            cur.append(line)
    out = []
    for block in events:
        ev = {"EXDATE": [], "RDATE": []}
        for name, params, value in _props(block):
            if name in ("DTSTART", "DTEND", "RECURRENCE-ID"):
                ev[name] = _parse_dt(params, value)
            elif name in ("EXDATE", "RDATE"):
                ev[name] += [_parse_dt(params, v) for v in value.split(",")]
            elif name in ("SUMMARY", "DESCRIPTION", "LOCATION"):
                ev[name] = _unescape(value)
            else:
                ev.setdefault(name, value)
        out.append(ev)
    return out


def expand(raw: list[dict], start: date, end: date) -> list[IcsEvent]:
    """Occurrences with a start day in [start, end]; cancelled events and EXDATEs removed;
    RECURRENCE-ID overrides replace the occurrence they modify."""
    overrides = {(e["UID"], e["RECURRENCE-ID"]): e for e in raw if "RECURRENCE-ID" in e}
    out = []
    for e in raw:
        if "RECURRENCE-ID" in e or "DTSTART" not in e:
            continue
        s0, e0 = e["DTSTART"], e.get("DTEND")
        dur = (e0 - s0) if e0 is not None else None
        if "RRULE" in e:
            all_day = not isinstance(s0, datetime)
            anchor = datetime.combine(s0, time()) if all_day else s0.replace(tzinfo=None)
            rule = rrulestr(e["RRULE"], dtstart=anchor)
            lo = datetime.combine(start, time()) - timedelta(days=1)
            hi = datetime.combine(end, time.max)
            starts = []
            for occ in rule.between(lo, hi, inc=True):
                starts.append(occ.date() if all_day else occ.replace(tzinfo=s0.tzinfo))
            starts += [r for r in e["RDATE"]]
        else:
            starts = [s0]
        exdates = {x if not isinstance(x, datetime) else x.replace(second=0) for x in e["EXDATE"]}
        for st in starts:
            key = st if not isinstance(st, datetime) else st.replace(second=0)
            if key in exdates:
                continue
            src = overrides.get((e.get("UID"), st), e)
            st2 = src.get("DTSTART", st) if src is not e else st
            occ = IcsEvent(
                uid=e.get("UID", ""), summary=src.get("SUMMARY", ""),
                start=st2, end=(st2 + dur) if dur is not None else src.get("DTEND"),
                location=src.get("LOCATION", ""), description=src.get("DESCRIPTION", ""),
                status=src.get("STATUS", "CONFIRMED").upper(),
            )
            if occ.status == "CANCELLED" or not (start <= occ.day <= end):
                continue
            out.append(occ)
    return sorted(out, key=lambda o: (o.day, "" if o.all_day else o.start.strftime("%H:%M")))
