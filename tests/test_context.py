from oversight.orchestrator.context import ClinicalContext, ContextBuilder


class FakeFhir:
    def __init__(self, resources):
        self._r = resources

    def read(self, rt, rid):
        return self._r[f"{rt}/{rid}"]

    def search(self, rt, params=None):
        return [v for k, v in self._r.items() if k.startswith(rt + "/")]


def _resources():
    return {
        "Patient/clean-1": {"resourceType": "Patient", "id": "clean-1", "gender": "female", "birthDate": "1972-03-11"},
        "MedicationRequest/mr-1": {"resourceType": "MedicationRequest", "id": "mr-1", "status": "active",
            "medicationCodeableConcept": {"text": "piperacillin-tazobactam"}, "subject": {"reference": "Patient/clean-1"}},
        "AllergyIntolerance/a-1": {"resourceType": "AllergyIntolerance", "id": "a-1",
            "code": {"text": "cefazolin"}, "patient": {"reference": "Patient/clean-1"}},
        "Observation/o-cr": {"resourceType": "Observation", "id": "o-cr",
            "code": {"coding": [{"system": "http://loinc.org", "code": "2160-0"}]},
            "valueQuantity": {"value": 0.9, "unit": "mg/dL"}, "subject": {"reference": "Patient/clean-1"}},
        "Observation/o-wt": {"resourceType": "Observation", "id": "o-wt",
            "code": {"coding": [{"system": "http://loinc.org", "code": "29463-7"}]},
            "valueQuantity": {"value": 68, "unit": "kg"}, "subject": {"reference": "Patient/clean-1"}},
        "Observation/o-susc": {"resourceType": "Observation", "id": "o-susc",
            "code": {"coding": [{"system": "http://loinc.org", "code": "18864-9", "display": "Cefazolin [Susceptibility]"}]},
            "valueCodeableConcept": {"text": "Susceptible"}, "subject": {"reference": "Patient/clean-1"}},
        "DiagnosticReport/dr-1": {"resourceType": "DiagnosticReport", "id": "dr-1",
            "conclusion": "MSSA susceptible to cefazolin.", "subject": {"reference": "Patient/clean-1"}},
    }


def test_builds_context():
    ctx = ContextBuilder(FakeFhir(_resources())).build("clean-1", "enc-clean-1")
    assert isinstance(ctx, ClinicalContext)
    assert ctx.patient_reference == "Patient/clean-1"
    assert ctx.is_female is True
    assert ctx.weight_kg == 68
    assert ctx.serum_creatinine == 0.9
    assert ctx.age and ctx.age > 40
    assert any("cefazolin" in a for a in ctx.allergies)
    assert any(s["agent"] == "cefazolin" and s["interpretation"].lower().startswith("suscept")
               for s in ctx.susceptibilities)
    assert ctx.current_regimen[0]["fhir_reference"].startswith("MedicationRequest/")
