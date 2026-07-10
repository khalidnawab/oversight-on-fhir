import copy

from oversight.inference.base import InferenceResult
from oversight.orchestrator.context import ClinicalContext
from oversight.orchestrator.loop import Orchestrator
from oversight.schema.validate import validate_recommendation

CLEAN_REC = {
    "schema_version": "0.1.0", "patient_reference": "Patient/clean-1", "encounter_reference": "Encounter/enc-clean-1",
    "candidacy": {"is_deescalation_candidate": "yes",
        "current_regimen": [{"medication": "piperacillin-tazobactam", "fhir_reference": "MedicationRequest/mr-clean-1"}],
        "recommended_action": "narrow", "recommended_agent": "cefazolin", "recommended_dose": None},
    "rationale": [{"assertion": "MSSA susceptible to cefazolin.",
        "evidence": [{"type": "fhir_resource", "fhir_reference": "DiagnosticReport/dr-clean-1",
                      "document_reference": None, "text_span": None, "knowledge_source_id": None}]}],
    "deterministic_tool_result": None,
    "confidence": {"score": 0.0, "method": "placeholder", "rationale": ""},
    "routing": {"decision": "surface", "triggered_high_risk_rules": [], "below_confidence_threshold": False},
    "disclosure_text": "AI generated.",
}


class FakeBackend:
    name = "fake"

    def __init__(self, rec):
        self._rec = rec

    def generate(self, prompt, schema, n_samples=1):
        return InferenceResult(recommendation=copy.deepcopy(self._rec),
                               samples=[copy.deepcopy(self._rec) for _ in range(n_samples)],
                               raw_meta={"backend": "fake"})


def _clean_ctx():
    return ClinicalContext(patient_reference="Patient/clean-1", encounter_reference="Encounter/enc-clean-1",
        age=54, weight_kg=68, serum_creatinine=0.9, is_female=True,
        current_regimen=[{"medication": "piperacillin-tazobactam", "fhir_reference": "MedicationRequest/mr-clean-1"}],
        allergies=[], susceptibilities=[{"agent": "cefazolin", "interpretation": "Susceptible", "fhir_reference": "Observation/o"}])


def _high_risk_ctx():
    c = _clean_ctx()
    c.allergies = ["cefazolin"]
    return c


def test_clean_surfaces_and_is_schema_valid():
    orch = Orchestrator(backend=FakeBackend(CLEAN_REC), threshold=0.7, n_samples=3)
    rec = orch.run_with_context(_clean_ctx(), knowledge_passages=[])
    validate_recommendation(rec)
    assert rec["routing"]["decision"] == "surface"
    assert rec["confidence"]["method"] == "self_consistency"
    assert rec["confidence"]["score"] == 1.0
    # deterministic tool result injected, not model-authored
    assert rec["deterministic_tool_result"]["renal_dose_adjustment"]["dose"] is not None
    assert rec["candidacy"]["recommended_dose"] is None


def test_high_risk_escalates_via_rule():
    orch = Orchestrator(backend=FakeBackend(CLEAN_REC), threshold=0.7, n_samples=3)
    rec = orch.run_with_context(_high_risk_ctx(), knowledge_passages=[])
    validate_recommendation(rec)
    assert rec["routing"]["decision"] == "escalate"
    assert "allergy_to_candidate" in rec["routing"]["triggered_high_risk_rules"]
    assert rec["deterministic_tool_result"]["contraindications"][0]["type"] == "allergy"
