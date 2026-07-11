"""Oversight dashboard aggregation (Section 11). Reads ONLY via FHIR REST — this is what proves
the oversight events are genuine resources, not internal logs."""
import httpx

from oversight.fhir.log import activity_log
from oversight.oversight import taxonomy as t


def aggregate_oversight(fhir_base_url: str, bearer_token: str = "", count: int = 500) -> dict:
    headers = {"Accept": "application/fhir+json"}
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    with httpx.Client(base_url=fhir_base_url.rstrip("/"), headers=headers, timeout=30) as client:
        resp = client.get(f"/AuditEvent?_count={count}")
        bundle = resp.json()
    try:  # surface this read in the activity panel; it bypasses FhirClient by design
        activity_log.append("GET", f"AuditEvent?_count={count}", resp.status_code)
    except Exception:
        pass

    dispositions = {c["code"]: 0 for c in t.DISPOSITION_CODES}
    reasons = {c["code"]: 0 for c in t.REASON_CODES}
    escalations = 0
    total_decisions = 0

    for entry in bundle.get("entry", []):
        ae = entry.get("resource", {})
        etype = ae.get("type", {})
        if etype.get("system") != t.EVENT_TYPE_CS_URL:
            continue
        if etype.get("code") == "escalation":
            escalations += 1
            continue
        if etype.get("code") == "oversight-decision":
            total_decisions += 1
            for st in ae.get("subtype", []):
                if st.get("code") in dispositions:
                    dispositions[st["code"]] += 1
            for ext in ae.get("extension", []):
                if ext.get("url") == t.REASON_EXT_URL:
                    code = ext["valueCodeableConcept"]["coding"][0]["code"]
                    if code in reasons:
                        reasons[code] += 1

    overrides = dispositions["edit"] + dispositions["reject"]
    override_rate = (overrides / total_decisions) if total_decisions else 0.0
    return {
        "total_decisions": total_decisions,
        "dispositions": dispositions,
        "override_rate": round(override_rate, 3),
        "reasons": reasons,
        "data_vintage_overrides": reasons["data-vintage"],
        "escalations": escalations,
    }
