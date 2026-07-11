from oversight.orchestrator.chart import build_chart


class FakeFhir:
    def __init__(self, resources):
        self._r = resources

    def search(self, rt, params=None):
        out = [v for k, v in self._r.items() if k.startswith(rt + "/")]
        if params and "patient" in params:
            out = [r for r in out if (r.get("subject", r.get("patient", {})).get("reference")) == params["patient"]]
        return out


def _resources():
    return {
        "MedicationRequest/mr1": {"resourceType": "MedicationRequest", "id": "mr1", "status": "active",
            "medicationCodeableConcept": {"text": "piperacillin-tazobactam"}, "subject": {"reference": "Patient/p1"},
            "authoredOn": "2026-07-06T09:00:00Z"},
        "MedicationAdministration/ma1": {"resourceType": "MedicationAdministration", "id": "ma1",
            "medicationCodeableConcept": {"text": "piperacillin-tazobactam"}, "subject": {"reference": "Patient/p1"},
            "effectiveDateTime": "2026-07-08T08:00:00Z"},
        "Observation/cr": {"resourceType": "Observation", "id": "cr",
            "code": {"coding": [{"system": "http://loinc.org", "code": "2160-0", "display": "Creatinine"}]},
            "valueQuantity": {"value": 4.2, "unit": "mg/dL"}, "subject": {"reference": "Patient/p1"}},
        "Observation/susc": {"resourceType": "Observation", "id": "susc",
            "code": {"coding": [{"system": "http://loinc.org", "code": "18864-9", "display": "Cefazolin [Susceptibility]"}]},
            "valueCodeableConcept": {"text": "Susceptible"}, "subject": {"reference": "Patient/p1"}},
        "DiagnosticReport/dr": {"resourceType": "DiagnosticReport", "id": "dr", "status": "final",
            "code": {"coding": [{"display": "Blood culture"}]}, "conclusion": "MSSA susceptible to cefazolin.",
            "subject": {"reference": "Patient/p1"}, "issued": "2026-07-08T06:00:00Z"},
        "AllergyIntolerance/a": {"resourceType": "AllergyIntolerance", "id": "a", "criticality": "high",
            "code": {"text": "cefazolin"}, "patient": {"reference": "Patient/p1"},
            "reaction": [{"manifestation": [{"text": "anaphylaxis"}]}]},
    }


def test_chart_orders_labs_cultures():
    cv = build_chart(FakeFhir(_resources()), "p1")
    assert cv.orders and cv.orders[0]["antibiotic"] is True
    assert cv.administrations and cv.administrations[0]["name"] == "piperacillin-tazobactam"
    creat = next(l for l in cv.labs if l["name"] == "Creatinine")
    assert creat["value"] == 4.2 and creat["flag"] == "high"
    assert cv.cultures and "MSSA" in cv.cultures[0]["conclusion"]
    assert any(s["agent"] == "cefazolin" for s in cv.cultures[0]["susceptibilities"])
    assert cv.allergies and cv.allergies[0]["substance"] == "cefazolin"
