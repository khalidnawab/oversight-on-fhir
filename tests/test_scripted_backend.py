from oversight.inference.base import InferenceBackend
from oversight.inference.scripted import ScriptedDemoBackend
from oversight.schema.validate import load_schema, validate_recommendation


def test_is_a_backend():
    assert isinstance(ScriptedDemoBackend(), InferenceBackend)


def test_clean_patient_proposal():
    b = ScriptedDemoBackend()
    r = b.generate("... Patient/clean-1 Encounter/enc-clean-1 ...", load_schema(), n_samples=3)
    validate_recommendation(r.recommendation)
    assert r.recommendation["patient_reference"] == "Patient/clean-1"
    assert r.recommendation["candidacy"]["recommended_agent"] == "cefazolin"
    assert len(r.samples) == 3
    # evidence points at this patient's diagnostic report
    assert r.recommendation["rationale"][0]["evidence"][0]["fhir_reference"] == "DiagnosticReport/dr-clean-1"


def test_high_risk_patient_proposal_references_hr():
    r = ScriptedDemoBackend().generate("Patient/hr-1 Encounter/enc-hr-1", load_schema())
    assert r.recommendation["patient_reference"] == "Patient/hr-1"
    assert r.recommendation["candidacy"]["current_regimen"][0]["fhir_reference"] == "MedicationRequest/mr-hr-1"


def test_unknown_patient_is_insufficient():
    r = ScriptedDemoBackend().generate("no patient here", load_schema())
    validate_recommendation(r.recommendation)
    assert r.recommendation["candidacy"]["recommended_action"] == "insufficient_information"
