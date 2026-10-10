from familyops.model import Event, merge, weekday_label, fmt_time


def test_merge_same_kid_same_time_across_sources():
    pm = Event(date="2026-10-14", start="18:00", title="Soccer practice", kids=["Elle"],
               location="Pembroke Park", sources=["PlayMetrics"])
    ol = Event(date="2026-10-14", start="18:00", title="Elle Soccer Practice", kids=["Elle"], sources=["Outlook · Elle"])
    out = merge([pm, ol])
    assert len(out) == 1 and out[0].sources == ["PlayMetrics", "Outlook · Elle"] and out[0].location == "Pembroke Park"


def test_no_merge_different_kids_or_times():
    a = Event(date="2026-10-14", start="18:00", title="Practice", kids=["Elle"])
    b = Event(date="2026-10-14", start="18:00", title="Practice", kids=["Ari"])
    c = Event(date="2026-10-14", start="19:00", title="Practice", kids=["Elle"])
    assert len(merge([a, b, c])) == 3
    fam = Event(date="2026-10-14", start="18:00", title="Practice", sources=["Outlook · Family"])
    assert len(merge([a, fam])) == 1  # an unattributed copy of the same title merges into the child's


def test_labels():
    assert weekday_label("2026-10-13") == "Tue, Oct 13"
    assert fmt_time("18:05") == "6:05 pm" and fmt_time("00:30") == "12:30 am" and fmt_time(None) == "All day"
