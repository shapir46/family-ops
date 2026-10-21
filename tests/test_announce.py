from familyops import announce
from familyops.model import Event


def test_field_trip_today_becomes_an_announcement():
    trip = Event(date="2026-10-22", start="12:15", end="14:15", title="Kindergarten field trip to Bowers School Farm",
                 kids=["Leo"], location="Bowers School Farm", details="Wear the yellow class shirt. Chaperones pay $14.")
    other = Event(date="2026-10-22", start="09:00", title="Soccer practice", kids=["Elle"])
    got = announce.for_day("2026-10-22", [other, trip])
    assert got == [{"kind": "field_trip", "kids": ["Leo"], "colors": ["#16A34A"], "title": trip.title,
                    "when": "12:15–2:15 pm", "where": "Bowers School Farm", "tip": "Wear the yellow class shirt."}]
    assert announce.for_day("2026-10-21", [trip]) is None                       # not today: nothing
    assert announce.for_day("2026-10-22", [Event(date="2026-10-22", title="Field trip", kids=["Someone"])]) is None


def test_time_spans():
    assert announce._span("09:30", "13:00") == "9:30 am–1:00 pm"
    assert announce._span(None, None) == "All day"
