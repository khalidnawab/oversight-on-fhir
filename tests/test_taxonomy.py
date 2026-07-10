from oversight.oversight import taxonomy as t


def test_reason_codes_present():
    codes = {c["code"] for c in t.REASON_CODES}
    assert {"clinical-disagreement", "missing-information", "patient-specific-factor", "data-vintage"} <= codes


def test_disposition_codes_present():
    assert {c["code"] for c in t.DISPOSITION_CODES} == {"accept", "edit", "reject"}


def test_canonical_urls_are_stable():
    assert t.REASON_CS_URL.endswith("/oversight-reason")
    assert t.DISPOSITION_CS_URL.endswith("/oversight-disposition")
    assert t.is_valid_reason("data-vintage")
    assert not t.is_valid_reason("nonsense")
