from oversight.orchestrator.context import ClinicalContext
from oversight.routing.engine import decide_routing


def _ctx(**kw):
    base = dict(patient_reference="Patient/x", encounter_reference="Encounter/y")
    base.update(kw)
    return ClinicalContext(**base)


def test_high_risk_forces_escalate_even_with_high_confidence():
    ctx = _ctx(allergies=["cefazolin"])
    r = decide_routing(ctx, candidate_agent="cefazolin",
                       tool_result={"contraindications": [{"type": "allergy"}], "interactions": []},
                       confidence_score=0.99, threshold=0.7)
    assert r["decision"] == "escalate"
    assert "allergy_to_candidate" in r["triggered_high_risk_rules"]
    assert r["below_confidence_threshold"] is False


def test_low_confidence_forces_escalate():
    ctx = _ctx()
    r = decide_routing(ctx, candidate_agent="cefazolin",
                       tool_result={"contraindications": [], "interactions": []},
                       confidence_score=0.4, threshold=0.7)
    assert r["decision"] == "escalate"
    assert r["below_confidence_threshold"] is True


def test_clean_high_confidence_surfaces():
    ctx = _ctx(susceptibilities=[{"agent": "cefazolin", "interpretation": "Susceptible", "fhir_reference": "Observation/o"}])
    r = decide_routing(ctx, candidate_agent="cefazolin",
                       tool_result={"contraindications": [], "interactions": []},
                       confidence_score=0.95, threshold=0.7)
    assert r["decision"] == "surface"
    assert r["triggered_high_risk_rules"] == []
