import json

from oversight.oversight import taxonomy as t


def build_device(model: str, version: str, backend: str, device_id: str = "oversight-ai") -> dict:
    """Device representing the AI system (model identity, version, backend) for AI-authorship
    attribution (Section 10.3 / Section 14 Device metadata)."""
    return {
        "resourceType": "Device", "id": device_id, "status": "active",
        "identifier": [{"system": f"{t.BASE_CANONICAL}/device", "value": f"{model}:{version}:{backend}"}],
        "deviceName": [{"name": f"Oversight-on-FHIR agent ({model})", "type": "model-name"}],
        "version": [{"value": version}],
        "property": [
            {"type": {"text": "backend"}, "valueCode": {"text": backend}},
            {"type": {"text": "model"}, "valueCode": {"text": model}},
        ],
    }


def build_guidance_response(rec: dict, device_id: str, timestamp: str, gr_id: str) -> dict:
    """The recommendation persisted as a retrievable FHIR resource (Section 10.3). The full
    structured recommendation is carried in a contained Parameters resource."""
    status = "success" if rec.get("routing", {}).get("decision") == "surface" else "data-required"
    params = {"resourceType": "Parameters", "id": "rec",
              "parameter": [{"name": "recommendation", "valueString": json.dumps(rec)}]}
    return {
        "resourceType": "GuidanceResponse", "id": gr_id,
        "contained": [params],
        "moduleUri": f"{t.BASE_CANONICAL}/module/deescalation",
        "status": status,
        "subject": {"reference": rec["patient_reference"]},
        "encounter": {"reference": rec["encounter_reference"]},
        "occurrenceDateTime": timestamp,
        "performer": {"reference": f"Device/{device_id}"},
        "outputParameters": {"reference": "#rec"},
        "note": [{"text": rec.get("disclosure_text", "")}],
    }


def build_ai_provenance(target_ref: str, device_id: str, timestamp: str, prov_id: str) -> dict:
    """Attributes AI authorship of the recommendation to the Device, machine-generated (Section 10.3)."""
    return {
        "resourceType": "Provenance", "id": prov_id,
        "target": [{"reference": target_ref}],
        "recorded": timestamp,
        "activity": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-DataOperation",
                                 "code": "CREATE", "display": "create"}], "text": "machine-generated"},
        "agent": [{"type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/provenance-participant-type",
                                        "code": "author"}]},
                   "who": {"reference": f"Device/{device_id}"}}],
    }


def _reason_ext(reason_code: str) -> dict:
    return {"url": t.REASON_EXT_URL,
            "valueCodeableConcept": {"coding": [{"system": t.REASON_CS_URL, "code": reason_code}]}}


def build_oversight_event(guidance_ref: str, practitioner_ref: str, disposition: str,
                          reason_code: str | None, note: str | None, timestamp: str, ae_id: str) -> dict:
    """The novel object: the human oversight decision as a profiled AuditEvent (Section 10.3)."""
    ae = {
        "resourceType": "AuditEvent", "id": ae_id,
        "type": {"system": t.EVENT_TYPE_CS_URL, "code": "oversight-decision"},
        "subtype": [{"system": t.DISPOSITION_CS_URL, "code": disposition}],
        "action": "R",
        "recorded": timestamp,
        "outcome": "0",
        "agent": [{"who": {"reference": practitioner_ref}, "requestor": True}],
        "source": {"observer": {"display": "Oversight-on-FHIR"}},
        "entity": [{"what": {"reference": guidance_ref},
                    "detail": ([{"type": "reason-note", "valueString": note}] if note else [])}],
    }
    if reason_code:
        ae["extension"] = [_reason_ext(reason_code)]
    return ae


def build_escalation_event(guidance_ref: str, triggered_rules: list[str], timestamp: str, ae_id: str) -> dict:
    """Escalations recorded as oversight events with a distinct type so escalation frequency is
    queryable alongside overrides (Section 10.3)."""
    subtype = [{"system": t.HIGH_RISK_CS_URL, "code": r} for r in triggered_rules]
    if not subtype:
        subtype = [{"system": t.EVENT_TYPE_CS_URL, "code": "escalation"}]
    return {
        "resourceType": "AuditEvent", "id": ae_id,
        "type": {"system": t.EVENT_TYPE_CS_URL, "code": "escalation"},
        "subtype": subtype,
        "action": "E", "recorded": timestamp, "outcome": "0",
        "agent": [{"who": {"display": "Oversight-on-FHIR routing engine"}, "requestor": False}],
        "source": {"observer": {"display": "Oversight-on-FHIR"}},
        "entity": [{"what": {"reference": guidance_ref}}],
    }
