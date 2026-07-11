from oversight.oversight.service import OversightService


class FakeFhir:
    def __init__(self):
        self.created = []
        self.updated = []

    def update(self, resource):
        self.updated.append(resource)
        return {**resource}

    def create(self, resource):
        self.created.append(resource)
        return {**resource, "id": resource.get("id", "server-assigned")}


SURFACE_REC = {"patient_reference": "Patient/clean-1", "encounter_reference": "Encounter/enc-clean-1",
               "routing": {"decision": "surface", "triggered_high_risk_rules": []},
               "disclosure_text": "AI generated."}
ESCALATE_REC = {"patient_reference": "Patient/hr-1", "encounter_reference": "Encounter/enc-hr-1",
                "routing": {"decision": "escalate", "triggered_high_risk_rules": ["allergy_to_candidate"]},
                "disclosure_text": "AI generated."}


def _svc(fake):
    return OversightService(fake, model="claude-opus-4-8", version="0.1.0", backend="frontier")


def test_persist_writes_device_guidance_and_provenance():
    fake = FakeFhir()
    refs = _svc(fake).persist_recommendation(SURFACE_REC)
    updated_types = [r["resourceType"] for r in fake.updated]
    created_types = [r["resourceType"] for r in fake.created]
    assert "Device" in updated_types
    assert "GuidanceResponse" in updated_types
    assert "Provenance" in created_types
    assert refs["guidance_response"].startswith("GuidanceResponse/")


def test_persist_escalation_writes_escalation_event():
    fake = FakeFhir()
    refs = _svc(fake).persist_recommendation(ESCALATE_REC)
    escalations = [r for r in fake.created if r["resourceType"] == "AuditEvent" and r["type"]["code"] == "escalation"]
    assert escalations
    assert "escalation_event" in refs


class FakeFhirWithStore:
    def __init__(self, store):
        self.store = store  # {resourceType: [ids]}
        self.deleted = []

    def search(self, rt, params=None):
        ids = self.store.get(rt, [])
        return [{"resourceType": rt, "id": i} for i in ids]

    def delete(self, rt, rid):
        self.store[rt] = [i for i in self.store.get(rt, []) if i != rid]
        self.deleted.append(f"{rt}/{rid}")
        return {}


def test_reset_deletes_recorded_resources_only():
    store = {"AuditEvent": ["ae1", "ae2"], "Provenance": ["p1"], "GuidanceResponse": ["gr1"],
             "Patient": ["clean-1"], "Observation": ["o1"]}
    fake = FakeFhirWithStore(store)
    svc = OversightService(fake, model="m", version="0.1.0", backend="demo")
    counts = svc.reset_recorded()
    assert counts == {"AuditEvent": 2, "Provenance": 1, "GuidanceResponse": 1}
    # patient data untouched
    assert store["Patient"] == ["clean-1"]
    assert store["Observation"] == ["o1"]
    # referrers deleted before the guidance response
    assert fake.deleted.index("Provenance/p1") < fake.deleted.index("GuidanceResponse/gr1")


def test_capture_disposition_writes_audit_event():
    fake = FakeFhir()
    _svc(fake).capture_disposition("GuidanceResponse/gr-1", "Practitioner/dr-alice",
                                   disposition="reject", reason_code="data-vintage", note="Newer culture back.")
    aes = [r for r in fake.created if r["resourceType"] == "AuditEvent"]
    assert aes and aes[0]["type"]["code"] == "oversight-decision"
    assert any(st["code"] == "reject" for st in aes[0]["subtype"])
