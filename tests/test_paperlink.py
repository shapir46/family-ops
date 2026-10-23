from datetime import date

from familyops import paperlink


def test_signed_link_is_deterministic_and_hides_key():
    d = date(2026, 10, 12)
    a = paperlink.link(d, key="k" * 64)
    assert a == paperlink.link(d, key="k" * 64)
    assert a.startswith("https://print.shapbox.com/paper/2026-10-12?sig=") and len(a.split("sig=")[1]) == 32
    assert "k" * 8 not in a
    assert paperlink.link(date(2026, 10, 13), key="k" * 64) != a


def test_falls_back_to_github_without_key(monkeypatch):
    monkeypatch.delenv("PAPER_LINK_KEY", raising=False)
    assert paperlink.link(date(2026, 10, 12)) == "https://github.com/shapir46/family-ops/blob/main/editions/2026-10-12.pdf"
