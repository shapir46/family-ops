"""Weather for Birmingham, MI from the NWS API (api.weather.gov), not the HTML text page."""
from __future__ import annotations

import re
from datetime import date, datetime

import requests

FORECAST = "https://api.weather.gov/gridpoints/DTX/59,42/forecast"  # 42.5237,-83.2303 (Birmingham, MI)
UA = {"User-Agent": "family-ops (Shapiro family digest)", "Accept": "application/geo+json"}


def icon(short: str) -> str:
    """Icon key for renderers: storm | snow | rain | fog | cloud | partly | sun | wind."""
    s = short.lower()
    for key, words in [("storm", ["thunder", "t-storm"]), ("snow", ["snow", "flurr", "sleet", "ice"]),
                       ("rain", ["rain", "shower", "drizzle"]), ("fog", ["fog", "haze", "smoke"]),
                       ("partly", ["partly", "mostly sunny", "mostly clear"]),
                       ("cloud", ["cloud", "overcast"]), ("wind", ["wind", "breezy", "blustery"]),
                       ("sun", ["sunny", "clear"])]:
        if any(w in s for w in words):
            return key
    return "cloud"


def summarize(periods: list[dict], today: date) -> dict:
    """Today's high and line, tonight's low, and a 4-day row starting tomorrow (README rule 2)."""
    by_day: dict[date, dict] = {}
    for p in periods:
        d = datetime.fromisoformat(p["startTime"]).date()
        slot = by_day.setdefault(d, {})
        slot["day" if p["isDaytime"] else "night"] = p
    t = by_day.get(today, {})
    day, night = t.get("day"), t.get("night")
    out = {
        "hi": day["temperature"] if day else None,
        "today": day["shortForecast"] if day else (night["shortForecast"] if night else None),
        "today_detail": day["detailedForecast"] if day else None,
        "tonight_low": night["temperature"] if night else None,
        "tonight": night["shortForecast"] if night else None,
        "icon": icon((day or night or {}).get("shortForecast", "")),
        "forecast": [],
    }
    for d in sorted(k for k in by_day if k > today)[:4]:
        dd, nn = by_day[d].get("day"), by_day[d].get("night")
        if not dd:
            continue
        out["forecast"].append({"date": d.isoformat(), "day": f"{d:%a}", "hi": dd["temperature"],
                                "lo": nn["temperature"] if nn else None, "short": _short(dd["shortForecast"]),
                                "icon": icon(dd["shortForecast"])})
    return out


def _short(s: str) -> str:
    s = re.sub(r"\bthen\b.*", "", s).strip()
    return s if len(s) <= 22 else s.split(" and ")[0][:22]


def get(today: date) -> dict:
    r = requests.get(FORECAST, headers=UA, timeout=30)
    r.raise_for_status()
    p = r.json()["properties"]
    out = summarize(p["periods"], today)
    out.update({"source": "National Weather Service", "updated": p.get("updateTime")})
    return out
