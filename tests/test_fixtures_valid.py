import json
from pathlib import Path

import pytest

FIX = Path(__file__).parent.parent / "fixtures"


@pytest.mark.parametrize("name", ["clean_candidate.json", "high_risk.json"])
def test_fixture_is_transaction_bundle(name):
    bundle = json.loads((FIX / name).read_text(encoding="utf-8"))
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "transaction"
    assert len(bundle["entry"]) >= 5
    for e in bundle["entry"]:
        assert "resource" in e and "request" in e
        assert e["request"]["method"] in ("PUT", "POST")


def test_clean_has_susceptibility_and_no_allergy():
    bundle = json.loads((FIX / "clean_candidate.json").read_text(encoding="utf-8"))
    types = [e["resource"]["resourceType"] for e in bundle["entry"]]
    assert "DiagnosticReport" in types
    assert "AllergyIntolerance" not in types


def test_high_risk_has_cefazolin_allergy():
    bundle = json.loads((FIX / "high_risk.json").read_text(encoding="utf-8"))
    allergies = [e["resource"] for e in bundle["entry"] if e["resource"]["resourceType"] == "AllergyIntolerance"]
    assert allergies, "high_risk fixture must contain an AllergyIntolerance"
    assert "cefazolin" in json.dumps(allergies[0]).lower()
