import copy

import httpx
import pytest

from oversight.config import Settings
from oversight.fhir.client import FhirClient
from oversight.orchestrator.context import ContextBuilder
from oversight.orchestrator.loop import Orchestrator
from oversight.schema.validate import validate_recommendation
from tests.test_orchestrator import CLEAN_REC, FakeBackend


def _hapi_up(base):
    try:
        return httpx.get(f"{base}/metadata", timeout=3).status_code == 200
    except Exception:
        return False


settings = Settings()
pytestmark = pytest.mark.skipif(not _hapi_up(settings.fhir_base_url), reason="HAPI not running")


def test_clean_fixture_end_to_end():
    client = FhirClient.from_settings(settings)
    ctx = ContextBuilder(client).build("clean-1", "enc-clean-1")
    assert ctx.weight_kg is not None  # fixture has body weight
    orch = Orchestrator(backend=FakeBackend(CLEAN_REC), threshold=0.7, n_samples=3)
    rec = orch.run_with_context(ctx, knowledge_passages=[])
    validate_recommendation(rec)
    assert rec["routing"]["decision"] == "surface"


def test_high_risk_fixture_escalates_end_to_end():
    client = FhirClient.from_settings(settings)
    ctx = ContextBuilder(client).build("hr-1", "enc-hr-1")
    # The fixture's escalation trigger is renal: CrCl ~19 mL/min via Cockcroft-Gault,
    # computed deterministically from data the model's prompt never includes.
    assert ctx.serum_creatinine is not None and ctx.serum_creatinine > 3.0
    rec_src = copy.deepcopy(CLEAN_REC)
    rec_src["patient_reference"] = "Patient/hr-1"
    rec_src["encounter_reference"] = "Encounter/enc-hr-1"
    orch = Orchestrator(backend=FakeBackend(rec_src), threshold=0.7, n_samples=3)
    rec = orch.run_with_context(ctx, knowledge_passages=[])
    assert rec["routing"]["decision"] == "escalate"
    assert "severe_renal_impairment" in rec["routing"]["triggered_high_risk_rules"]
