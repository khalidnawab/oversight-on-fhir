import datetime as _dt

from oversight.orchestrator.census import CensusScanner

NOW = _dt.datetime(2026, 7, 10, 12, 0, 0, tzinfo=_dt.timezone.utc)


def _h(hours):
    return (NOW - _dt.timedelta(hours=hours)).isoformat().replace("+00:00", "Z")


class FakeFhir:
    def __init__(self, resources):
        self._r = resources

    def search(self, rt, params=None):
        out = [v for k, v in self._r.items() if k.startswith(rt + "/")]
        if params and "patient" in params:
            pid = params["patient"]
            out = [r for r in out if _subject_ref(r) == pid]
        return out


def _subject_ref(r):
    for key in ("subject", "patient"):
        if key in r:
            return r[key].get("reference")
    return None


def _unit():
    return {
        # eligible: broad-spectrum 90h, susceptibilities resulted
        "Patient/webb": {"resourceType": "Patient", "id": "webb", "name": [{"given": ["Marcus"], "family": "Webb"}]},
        "Encounter/enc-webb": {"resourceType": "Encounter", "id": "enc-webb", "status": "in-progress",
            "subject": {"reference": "Patient/webb"}, "location": [{"location": {"display": "Ward 5B · Bed 12"}}]},
        "MedicationRequest/mr-webb": {"resourceType": "MedicationRequest", "id": "mr-webb", "status": "active",
            "medicationCodeableConcept": {"text": "piperacillin-tazobactam"}, "subject": {"reference": "Patient/webb"},
            "authoredOn": _h(90)},
        "Observation/susc-webb": {"resourceType": "Observation", "id": "susc-webb",
            "code": {"coding": [{"display": "Ceftriaxone [Susceptibility]"}]}, "valueCodeableConcept": {"text": "Susceptible"},
            "subject": {"reference": "Patient/webb"}},
        "DiagnosticReport/dr-webb": {"resourceType": "DiagnosticReport", "id": "dr-webb",
            "conclusion": "E. coli, ceftriaxone-susceptible", "subject": {"reference": "Patient/webb"}},
        # monitoring: only 20h of therapy
        "Patient/becker": {"resourceType": "Patient", "id": "becker", "name": [{"given": ["Tom"], "family": "Becker"}]},
        "Encounter/enc-becker": {"resourceType": "Encounter", "id": "enc-becker", "status": "in-progress",
            "subject": {"reference": "Patient/becker"}, "location": [{"location": {"display": "Ward 6A · Bed 3"}}]},
        "MedicationRequest/mr-becker": {"resourceType": "MedicationRequest", "id": "mr-becker", "status": "active",
            "medicationCodeableConcept": {"text": "piperacillin-tazobactam"}, "subject": {"reference": "Patient/becker"},
            "authoredOn": _h(20)},
        # insufficient: 96h broad-spectrum but no susceptibilities
        "Patient/anand": {"resourceType": "Patient", "id": "anand", "name": [{"given": ["Priya"], "family": "Anand"}]},
        "Encounter/enc-anand": {"resourceType": "Encounter", "id": "enc-anand", "status": "in-progress",
            "subject": {"reference": "Patient/anand"}, "location": [{"location": {"display": "Ward 5B · Bed 14"}}]},
        "MedicationRequest/mr-anand": {"resourceType": "MedicationRequest", "id": "mr-anand", "status": "active",
            "medicationCodeableConcept": {"text": "piperacillin-tazobactam"}, "subject": {"reference": "Patient/anand"},
            "authoredOn": _h(96)},
        "DiagnosticReport/dr-anand": {"resourceType": "DiagnosticReport", "id": "dr-anand",
            "conclusion": "No growth to date", "subject": {"reference": "Patient/anand"}},
        # not eligible: on narrow cefazolin only
        "Patient/marchetti": {"resourceType": "Patient", "id": "marchetti", "name": [{"given": ["Sofia"], "family": "Marchetti"}]},
        "Encounter/enc-marchetti": {"resourceType": "Encounter", "id": "enc-marchetti", "status": "in-progress",
            "subject": {"reference": "Patient/marchetti"}, "location": [{"location": {"display": "Ward 6A · Bed 7"}}]},
        "MedicationRequest/mr-marchetti": {"resourceType": "MedicationRequest", "id": "mr-marchetti", "status": "active",
            "medicationCodeableConcept": {"text": "cefazolin"}, "subject": {"reference": "Patient/marchetti"},
            "authoredOn": _h(40)},
    }


def _by_id(entries):
    return {e.patient_id: e for e in entries}


def test_scan_classifies_each_category():
    entries = CensusScanner(FakeFhir(_unit())).scan(now=NOW)
    by = _by_id(entries)
    assert by["webb"].eligibility == "eligible"
    assert by["becker"].eligibility == "monitoring"
    assert by["anand"].eligibility == "insufficient"
    assert by["marchetti"].eligibility == "not_eligible"


def test_eligible_sorted_first():
    entries = CensusScanner(FakeFhir(_unit())).scan(now=NOW)
    assert entries[0].eligibility == "eligible"


def test_day_of_therapy_computed():
    by = _by_id(CensusScanner(FakeFhir(_unit())).scan(now=NOW))
    assert by["webb"].day_of_therapy == 4  # 90h -> day 4
    assert by["webb"].location == "Ward 5B · Bed 12"


def test_location_and_regimen_present():
    by = _by_id(CensusScanner(FakeFhir(_unit())).scan(now=NOW))
    assert by["webb"].regimen[0]["broad_spectrum"] is True
    assert by["marchetti"].regimen[0]["broad_spectrum"] is False


def test_window_is_configurable():
    # With a 12h window, Becker (20h) becomes eligible-track rather than monitoring.
    by = _by_id(CensusScanner(FakeFhir(_unit()), deescalation_hours=12).scan(now=NOW))
    assert by["becker"].eligibility in ("eligible", "insufficient")
