from modules.live_search import _domain_allowed


def test_domain_spoofing_rejection():
    allowlist = ["who.int", "wsava.org"]
    assert _domain_allowed("who.int", allowlist)
    assert _domain_allowed("sub.who.int", allowlist)
    assert not _domain_allowed("who.int.evil.com", allowlist)
    assert not _domain_allowed("wsava.org.evil.com", allowlist)
