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


def test_capture_disposition_writes_audit_event():
    fake = FakeFhir()
    _svc(fake).capture_disposition("GuidanceResponse/gr-1", "Practitioner/dr-alice",
                                   disposition="reject", reason_code="data-vintage", note="Newer culture back.")
    aes = [r for r in fake.created if r["resourceType"] == "AuditEvent"]
    assert aes and aes[0]["type"]["code"] == "oversight-decision"
    assert any(st["code"] == "reject" for st in aes[0]["subtype"])
