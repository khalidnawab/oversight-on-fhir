import json
import os

import pytest

from oversight.inference.frontier import FrontierAPIBackend
from oversight.schema.validate import load_schema, validate_recommendation


class _FakeContentBlock:
    def __init__(self, obj):
        self.type = "text"
        self.text = json.dumps(obj)


class _FakeMessage:
    def __init__(self, obj):
        self.content = [_FakeContentBlock(obj)]


class _FakeMessages:
    def __init__(self, obj):
        self._obj = obj
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return _FakeMessage(self._obj)


class _FakeClient:
    def __init__(self, obj):
        self.messages = _FakeMessages(obj)


VALID_MIN = {
    "schema_version": "0.1.0",
    "patient_reference": "Patient/x", "encounter_reference": "Encounter/y",
    "stewardship_assessment": "Narrow to cefazolin.",
    "candidacy": {"is_deescalation_candidate": "yes",
                  "current_regimen": [{"medication": "pip-tazo", "fhir_reference": "MedicationRequest/m1"}],
                  "recommended_action": "narrow", "recommended_agent": "cefazolin", "recommended_dose": None},
    "rationale": [{"assertion": "a", "evidence": [{"type": "fhir_resource", "fhir_reference": "DiagnosticReport/d1",
                   "document_reference": None, "text_span": None, "knowledge_source_id": None}]}],
    "deterministic_tool_result": None,
    "confidence": {"score": 0.9, "method": "self_consistency", "rationale": "r"},
    "routing": {"decision": "surface", "triggered_high_risk_rules": [], "below_confidence_threshold": False},
    "disclosure_text": "AI generated.",
}


def test_generate_returns_validated_recommendation():
    backend = FrontierAPIBackend(model="claude-opus-4-8", client=_FakeClient(VALID_MIN))
    result = backend.generate(prompt="reason about patient", schema=load_schema())
    validate_recommendation(result.recommendation)
    assert result.recommendation["candidacy"]["recommended_agent"] == "cefazolin"
    assert backend.name == "frontier:claude-opus-4-8"


def test_n_samples_collects_multiple():
    backend = FrontierAPIBackend(model="claude-opus-4-8", client=_FakeClient(VALID_MIN))
    result = backend.generate(prompt="p", schema=load_schema(), n_samples=3)
    assert len(result.samples) == 3


@pytest.mark.skipif(not os.getenv("OVERSIGHT_RUN_LIVE_TESTS"),
                    reason="live API test; set OVERSIGHT_RUN_LIVE_TESTS=1 to run")
def test_live_smoke():
    from oversight.schema.validate import load_model_schema
    backend = FrontierAPIBackend(model="claude-opus-4-8")
    prompt = ("Produce a de-escalation recommendation for Patient/x Encounter/y currently on "
              "MedicationRequest/m1 piperacillin-tazobactam, isolate MSSA susceptible to cefazolin "
              "per DiagnosticReport/d1. Narrow to cefazolin. Leave recommended_dose null.")
    result = backend.generate(prompt=prompt, schema=load_model_schema())
    # Raw model output: code-owned fields are null; the clinical content is present and evidence-linked.
    assert result.recommendation["candidacy"]["recommended_action"] in (
        "narrow", "continue", "stop", "switch-iv-to-po", "broaden", "insufficient_information", "escalate")
    assert result.recommendation["rationale"] and result.recommendation["rationale"][0]["evidence"]
