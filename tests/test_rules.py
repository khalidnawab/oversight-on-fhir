from oversight.orchestrator.context import ClinicalContext
from oversight.routing.rules import RULES, evaluate_high_risk


def _ctx(**kw):
    base = dict(patient_reference="Patient/x", encounter_reference="Encounter/y")
    base.update(kw)
    return ClinicalContext(**base)


def test_allergy_to_candidate_triggers():
    ctx = _ctx(allergies=["cefazolin"])
    fired = evaluate_high_risk(ctx, candidate_agent="cefazolin",
                               tool_result={"contraindications": [{"type": "allergy"}], "interactions": []})
    assert "allergy_to_candidate" in fired


def test_not_susceptible_triggers():
    ctx = _ctx(susceptibilities=[{"agent": "cefazolin", "interpretation": "Resistant", "fhir_reference": "Observation/o"}])
    fired = evaluate_high_risk(ctx, candidate_agent="cefazolin", tool_result={"contraindications": [], "interactions": []})
    assert "isolate_not_susceptible" in fired


def test_severe_renal_triggers():
    ctx = _ctx(serum_creatinine=4.0, weight_kg=70, age=70, is_female=False)  # low CrCl
    fired = evaluate_high_risk(ctx, candidate_agent="cefazolin",
                               tool_result={"contraindications": [], "interactions": []}, severe_crcl=30)
    assert "severe_renal_impairment" in fired


def test_neutropenia_triggers():
    ctx = _ctx(anc=0.4)
    fired = evaluate_high_risk(ctx, candidate_agent="cefazolin",
                               tool_result={"contraindications": [], "interactions": []}, neutropenia_cutoff=0.5)
    assert "neutropenia" in fired


def test_clean_context_fires_nothing():
    ctx = _ctx(allergies=[],
               susceptibilities=[{"agent": "cefazolin", "interpretation": "Susceptible", "fhir_reference": "Observation/o"}],
               serum_creatinine=0.9, weight_kg=68, age=54, is_female=True, anc=4.0)
    fired = evaluate_high_risk(ctx, candidate_agent="cefazolin", tool_result={"contraindications": [], "interactions": []})
    assert fired == []


def test_rules_are_inspectable():
    # Each rule exposes an id + human description so the taxonomy is reviewable (Section 9.1).
    assert all(r.id and r.description for r in RULES)
