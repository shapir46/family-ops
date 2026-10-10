from datetime import date

from familyops import almanac


def test_us_holiday_rules():
    h = almanac.us_holidays(2026)
    assert h[date(2026, 10, 12)] == "Indigenous Peoples' Day"   # 2nd Monday of October
    assert h[date(2026, 11, 26)] == "Thanksgiving"               # 4th Thursday
    assert h[date(2026, 5, 25)] == "Memorial Day"                # last Monday of May
    assert h[date(2026, 9, 7)] == "Labor Day"                    # matches the BPS calendar
    assert h[date(2026, 10, 31)] == "Halloween"


def test_sunset_within_two_minutes_of_hebcal_reference():
    # Hebcal zmanim for Birmingham, MI (checked 2026-10-10): 18:49, 17:01, 19:44, 21:13
    for d, ref in [(date(2026, 10, 16), (18, 49)), (date(2026, 12, 18), (17, 1)), (date(2027, 3, 19), (19, 44)),
                   (date(2027, 6, 18), (21, 13))]:
        t = almanac.sunset(d)
        assert abs((t.hour * 60 + t.minute) - (ref[0] * 60 + ref[1])) <= 2, d


def test_shabbat_only_on_friday_and_offline_ok():
    fri = almanac.day(date(2026, 10, 16), fetch=False)
    assert fri["shabbat"]["sunset"].endswith("pm")
    assert almanac.day(date(2026, 10, 17), fetch=False)["shabbat"] is None
    assert almanac.day(date(2026, 10, 12), fetch=False)["holidays"] == ["Indigenous Peoples' Day"]
