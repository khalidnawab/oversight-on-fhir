from oversight.inference.base import InferenceBackend
from oversight.inference.scripted import ScriptedDemoBackend
from oversight.orchestrator.context import ClinicalContext
from oversight.orchestrator.prompt import build_prompt
from oversight.schema.validate import load_schema, validate_recommendation


def _prompt(ctx):
    return build_prompt(ctx, knowledge_passages=[])


def _ctx(pid, susceptibilities, regimen_ref="MedicationRequest/mr-1"):
    return ClinicalContext(
        patient_reference=f"Patient/{pid}", encounter_reference=f"Encounter/enc-{pid}",
        current_regimen=[{"medication": "piperacillin-tazobactam", "fhir_reference": regimen_ref}],
        susceptibilities=susceptibilities,
        culture_conclusions=[{"text": "positive", "fhir_reference": f"DiagnosticReport/dr-{pid}"}])


def test_is_a_backend():
    assert isinstance(ScriptedDemoBackend(), InferenceBackend)


def test_narrows_to_susceptible_target():
    ctx = _ctx("mssa", [{"agent": "cefazolin", "interpretation": "Susceptible", "fhir_reference": "Observation/o"}])
    r = ScriptedDemoBackend().generate(_prompt(ctx), load_schema(), n_samples=3)
    validate_recommendation(r.recommendation)
    assert r.recommendation["patient_reference"] == "Patient/mssa"
    assert r.recommendation["candidacy"]["recommended_agent"] == "cefazolin"
    assert len(r.samples) == 3


def test_prefers_ceftriaxone_when_only_it_is_susceptible():
    ctx = _ctx("ecoli", [{"agent": "ceftriaxone", "interpretation": "Susceptible", "fhir_reference": "Observation/o"}])
    r = ScriptedDemoBackend().generate(_prompt(ctx), load_schema())
    assert r.recommendation["candidacy"]["recommended_agent"] == "ceftriaxone"


def test_continue_when_no_narrow_target_susceptible():
    ctx = _ctx("pseudo", [{"agent": "cefepime", "interpretation": "Susceptible", "fhir_reference": "Observation/o"}])
    r = ScriptedDemoBackend().generate(_prompt(ctx), load_schema())
    validate_recommendation(r.recommendation)
    assert r.recommendation["candidacy"]["recommended_action"] == "continue"


def test_insufficient_when_no_susceptibilities():
    ctx = _ctx("pending", [])
    r = ScriptedDemoBackend().generate(_prompt(ctx), load_schema())
    validate_recommendation(r.recommendation)
    assert r.recommendation["candidacy"]["recommended_action"] == "insufficient_information"
