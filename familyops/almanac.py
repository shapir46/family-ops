"""Holidays and Shabbat sunset for the newspaper banner (and the dashboard).

- US holidays and well-known kid-friendly days: computed from their date rules (no network).
- Jewish holidays: Hebcal API, fetched once per year and cached in cache/jewish-holidays-YYYY.json.
- Sunset: NOAA solar equations for Birmingham, MI (no network); cross-checked against Hebcal in tests.
"""
from __future__ import annotations

import json
import math
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import requests

from . import ROOT, TZ

LAT, LON = 42.5467, -83.2113          # Birmingham, MI
CACHE = ROOT / "cache"
# Modern Israeli observances too obscure for a kids' paper.
SKIP = {"Yom HaAliyah", "Yom HaAliyah School Observance", "Sigd", "Family Day", "Yitzhak Rabin Memorial Day",
        "Ben-Gurion Day", "Herzl Day", "Jabotinsky Day", "Hebrew Language Day", "Chag HaBanot"}
ZMANIM = "https://www.hebcal.com/zmanim?cfg=json&latitude={lat}&longitude={lon}&tzid=America/Detroit&date={d}"
HEBCAL = ("https://www.hebcal.com/hebcal?v=1&cfg=json&maj=on&min=on&mod=on&nx=off&ss=off&mf=off&c=off"
          "&s=off&i=off&geo=none&year={year}")


def _nth_weekday(year, month, weekday, n):
    """n-th weekday (0=Mon) of a month; n=-1 means the last."""
    if n > 0:
        d = date(year, month, 1)
        d += timedelta(days=(weekday - d.weekday()) % 7)
        return d + timedelta(weeks=n - 1)
    nxt = date(year + (month == 12), month % 12 + 1, 1)
    d = nxt - timedelta(days=1)
    return d - timedelta(days=(d.weekday() - weekday) % 7)


def us_holidays(year: int) -> dict[date, str]:
    MON, THU, SUN = 0, 3, 6
    h = {
        date(year, 1, 1): "New Year's Day",
        _nth_weekday(year, 1, MON, 3): "Martin Luther King Jr. Day",
        date(year, 2, 2): "Groundhog Day",
        date(year, 2, 14): "Valentine's Day",
        _nth_weekday(year, 2, MON, 3): "Presidents' Day",
        date(year, 3, 17): "St. Patrick's Day",
        date(year, 4, 22): "Earth Day",
        _nth_weekday(year, 5, SUN, 2): "Mother's Day",
        _nth_weekday(year, 5, MON, -1): "Memorial Day",
        _nth_weekday(year, 6, SUN, 3): "Father's Day",
        date(year, 6, 19): "Juneteenth",
        date(year, 7, 4): "Independence Day",
        _nth_weekday(year, 9, MON, 1): "Labor Day",
        _nth_weekday(year, 10, MON, 2): "Indigenous Peoples' Day",
        date(year, 10, 31): "Halloween",
        date(year, 11, 11): "Veterans Day",
        _nth_weekday(year, 11, THU, 4): "Thanksgiving",
        date(year, 12, 24): "Christmas Eve",
        date(year, 12, 25): "Christmas",
        date(year, 12, 31): "New Year's Eve",
    }
    return h


def jewish_holidays(year: int, fetch=True) -> dict[date, list[str]]:
    path = CACHE / f"jewish-holidays-{year}.json"
    if path.exists():
        items = json.loads(path.read_text())
    elif fetch:
        r = requests.get(HEBCAL.format(year=year), timeout=30)
        r.raise_for_status()
        items = [{"date": i["date"][:10], "title": i["title"]}
                 for i in r.json()["items"] if i.get("category") == "holiday" and i["title"] not in SKIP]
        CACHE.mkdir(exist_ok=True)
        path.write_text(json.dumps(items, indent=1, ensure_ascii=False))
    else:
        return {}
    out: dict[date, list[str]] = {}
    for i in items:
        out.setdefault(date.fromisoformat(i["date"]), []).append(i["title"])
    return out


def sunset(d: date, lat=LAT, lon=LON) -> datetime:
    """Local sunset (America/Detroit) by the NOAA solar position equations, accurate to about a minute."""
    n = d.timetuple().tm_yday
    gamma = 2 * math.pi / 365 * (n - 1 + 0.5)
    eqtime = 229.18 * (0.000075 + 0.001868 * math.cos(gamma) - 0.032077 * math.sin(gamma)
                       - 0.014615 * math.cos(2 * gamma) - 0.040849 * math.sin(2 * gamma))
    decl = (0.006918 - 0.399912 * math.cos(gamma) + 0.070257 * math.sin(gamma) - 0.006758 * math.cos(2 * gamma)
            + 0.000907 * math.sin(2 * gamma) - 0.002697 * math.cos(3 * gamma) + 0.00148 * math.sin(3 * gamma))
    zenith = math.radians(90.833)
    phi = math.radians(lat)
    ha = math.degrees(math.acos(math.cos(zenith) / (math.cos(phi) * math.cos(decl)) - math.tan(phi) * math.tan(decl)))
    minutes_utc = 720 - 4 * (lon - ha) - eqtime
    utc = datetime(d.year, d.month, d.day, tzinfo=ZoneInfo("UTC")) + timedelta(minutes=minutes_utc)
    return utc.astimezone(ZoneInfo(TZ))


def sunset_best(d: date, fetch=True) -> datetime:
    """Hebcal's sunset when reachable (the reference Jewish calendars use), else the NOAA calculation."""
    if fetch:
        try:
            r = requests.get(ZMANIM.format(lat=LAT, lon=LON, d=d.isoformat()), timeout=20)
            r.raise_for_status()
            return datetime.fromisoformat(r.json()["times"]["sunset"]).astimezone(ZoneInfo(TZ))
        except Exception:  # noqa: BLE001
            pass
    return sunset(d)


def fmt(t: datetime) -> str:
    return f"{t.hour % 12 or 12}:{t:%M} {'am' if t.hour < 12 else 'pm'}"


def day(d: date, fetch=True) -> dict:
    """{'holidays': [...], 'shabbat': {'sunset': '6:52 pm'} on Fridays only}."""
    names = []
    if d in us_holidays(d.year):
        names.append(us_holidays(d.year)[d])
    try:
        names += jewish_holidays(d.year, fetch=fetch).get(d, [])
    except Exception:  # noqa: BLE001 - a missing Jewish calendar never blocks the paper
        pass
    out = {"date": d.isoformat(), "holidays": names, "shabbat": None}
    if d.weekday() == 4:
        out["shabbat"] = {"sunset": fmt(sunset_best(d, fetch)), "source": "Hebcal" if fetch else "computed"}
    return out
