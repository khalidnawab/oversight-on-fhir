from oversight.oversight import resources as R
from oversight.oversight import taxonomy as t

TS = "2026-07-10T12:00:00Z"
REC = {"patient_reference": "Patient/clean-1", "encounter_reference": "Encounter/enc-clean-1",
       "routing": {"decision": "surface"}, "disclosure_text": "AI generated.",
       "candidacy": {"recommended_action": "narrow", "recommended_agent": "cefazolin"}}


def test_device_carries_model_identity():
    d = R.build_device(model="claude-opus-4-8", version="0.1.0", backend="frontier")
    assert d["resourceType"] == "Device" and d["id"]
    assert any(v["value"] == "0.1.0" for v in d["version"])


def test_guidance_response_embeds_recommendation():
    gr = R.build_guidance_response(REC, device_id="ai-1", timestamp=TS, gr_id="gr-1")
    assert gr["resourceType"] == "GuidanceResponse"
    assert gr["status"] in ("success", "data-required")
    assert gr["subject"]["reference"] == "Patient/clean-1"
    assert gr["performer"]["reference"] == "Device/ai-1"
    contained = gr["contained"][0]
    assert contained["resourceType"] == "Parameters"


def test_ai_provenance_targets_guidance_and_attributes_device():
    p = R.build_ai_provenance(target_ref="GuidanceResponse/gr-1", device_id="ai-1", timestamp=TS, prov_id="pr-1")
    assert p["resourceType"] == "Provenance"
    assert p["target"][0]["reference"] == "GuidanceResponse/gr-1"
    assert p["agent"][0]["who"]["reference"] == "Device/ai-1"


def test_oversight_event_encodes_disposition_reason_and_target():
    ae = R.build_oversight_event(guidance_ref="GuidanceResponse/gr-1", practitioner_ref="Practitioner/dr-1",
                                 disposition="reject", reason_code="data-vintage", note="Newer culture back.",
                                 timestamp=TS, ae_id="ae-1")
    assert ae["resourceType"] == "AuditEvent"
    assert ae["type"]["code"] == "oversight-decision"
    assert any(st["code"] == "reject" for st in ae["subtype"])
    assert ae["agent"][0]["who"]["reference"] == "Practitioner/dr-1"
    assert ae["entity"][0]["what"]["reference"] == "GuidanceResponse/gr-1"
    ext = ae["extension"][0]
    assert ext["url"] == t.REASON_EXT_URL
    assert ext["valueCodeableConcept"]["coding"][0]["code"] == "data-vintage"


def test_escalation_event_is_distinct_type():
    ae = R.build_escalation_event(guidance_ref="GuidanceResponse/gr-1", triggered_rules=["allergy_to_candidate"],
                                  timestamp=TS, ae_id="ae-2")
    assert ae["type"]["code"] == "escalation"
    assert any(st["code"] == "allergy_to_candidate" for st in ae["subtype"])
