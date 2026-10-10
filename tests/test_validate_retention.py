from datetime import date

from familyops import retention as R
from familyops import validate as V

TODAY = date(2026, 10, 10)


def test_weekday_pairs():
    assert V.weekday_pairs("Tue, Oct 13 and Sun, Oct 11", TODAY) == []
    assert V.weekday_pairs("Wed, Oct 13", TODAY) == ["weekday mismatch: 'Wed, Oct 13' (Wed Oct 13) is really Tue, Oct 13"]
    assert V.weekday_pairs("Fri, Jan 1", date(2026, 12, 20)) == []  # resolves to 2027


def test_weekday_ranges():
    for ok in ["Fri–Sun, Oct 23–25", "Fri-Sun, Oct 23-25", "Mon–Wed, Dec 28–30", "Sat, Oct 24–Sun, Oct 25",
               "Wed-Thu, Sep 2-3"]:
        assert V.weekday_pairs(ok, TODAY) == [], ok
    assert V.weekday_pairs("Fri–Sat, Oct 23–25", TODAY)  # end weekday wrong (Oct 25 is a Sunday)
    assert V.weekday_pairs("Thu–Sun, Oct 23–25", TODAY)  # start weekday wrong


def test_bus_sacc_but_bike_bus_ok():
    assert V.excluded_topics("Join the Bike Bus Friday") == []
    assert len(V.excluded_topics("No busses for JK/K; SACC registration open")) == 2


def test_credentials_and_env_secret(monkeypatch):
    assert V.secrets('<a href="https://x.shulcloud.com/payment.php?login_link=eyJ">Pay</a>')
    assert V.secrets('<a href="https://classdojo.com/x?ctt=abc">Open</a>')
    assert V.secrets("<a href=\"https://www.constantcontact.com/tn.jsp?x=1\">Register</a>") == []
    monkeypatch.setenv("RELAY_TOKEN", "abcdef1234567890")
    assert V.secrets("oops abcdef1234567890") == ["RELAY_TOKEN value appears in the output"]


def test_email_html_rules():
    good = '<h2>☀️ Today</h2><ul><li><b>9:30 am</b> — <a href="https://a.b/c?x=1&amp;y=2">Register</a></li></ul>'
    assert V.email_html(good) == []
    bad = '<h1>x</h1><table></table><a href="https://a.b/?x=1&y=2">https://a.b/?x=1</a>'
    probs = V.email_html(bad)
    assert any("h1" in p and "table" in p for p in probs)
    assert any("raw URL" in p for p in probs) and any("unescaped &" in p for p in probs)


def test_recipients():
    assert V.recipients(["jacob@ivanhoecompanies.com"], shadow=True) == []
    assert V.recipients(["jacob@ivanhoecompanies.com", "Rebekah.Shapiro@gmail.com"], shadow=True)
    assert V.recipients(["Jacob@ivanhoecompanies.com", "Rebekah.Shapiro@gmail.com"], shadow=False) == []


def test_retention_rules():
    cats = ["Digest-First-2026-10-03"]
    assert not R.undated_live(cats, TODAY)            # exactly 7 days: expired
    assert R.undated_live(["Digest-First-2026-10-04"], TODAY)
    assert R.expired(cats, TODAY)
    assert not R.expired(cats + ["Digest-Hold-2026-10-12"], TODAY)  # live hold keeps it
    assert R.expired(cats + ["Digest-Hold-2026-10-09"], TODAY)
    assert not R.expired(["Something-else"], TODAY)  # no Digest-First: never purge
    assert R.new_categories(TODAY, [date(2026, 10, 1), date(2026, 10, 20), date(2026, 10, 12)]) == \
        ["Digest-First-2026-10-10", "Digest-Hold-2026-10-20"]
    assert R.new_categories(TODAY, []) == ["Digest-First-2026-10-10"]


def test_group_for_filing_batches_of_five():
    msgs = {f"m{i}": ["Digest-First-2026-10-10"] for i in range(7)} | {"x": ["Digest-First-2026-10-10", "Digest-Hold-2026-10-20"]}
    groups = R.group_for_filing(msgs)
    assert sorted(len(ids) for ids, _ in groups) == [1, 2, 5]
