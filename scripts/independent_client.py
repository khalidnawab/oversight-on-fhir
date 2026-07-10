"""Independent read-only FHIR client (Section 10.5 / acceptance criterion 6).

Given ONLY a FHIR base URL (and optional bearer token), this reconstructs the full oversight
story for a recommendation — who decided what, when, over which AI output, and why — using
nothing but standard FHIR REST. It imports NO project code: this is the proof that oversight
events are genuine, independently-retrievable resources, not internal logs.

Usage:
    uv run python scripts/independent_client.py <GuidanceResponse-id> [--base URL] [--token TOKEN]
"""
import argparse
import json
import sys

import httpx


def _get(client: httpx.Client, path: str) -> dict:
    r = client.get(path)
    r.raise_for_status()
    return r.json()


def reconstruct(base_url: str, guidance_id: str, token: str = "") -> dict:
    headers = {"Accept": "application/fhir+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with httpx.Client(base_url=base_url.rstrip("/"), headers=headers, timeout=30) as client:
        gr = _get(client, f"/GuidanceResponse/{guidance_id}")
        gref = f"GuidanceResponse/{guidance_id}"

        prov_bundle = _get(client, f"/Provenance?target={gref}")
        audit_bundle = _get(client, f"/AuditEvent?entity={gref}")

    # AI authorship (who/what produced the recommendation)
    ai_device = None
    for e in prov_bundle.get("entry", []):
        for agent in e["resource"].get("agent", []):
            who = agent.get("who", {}).get("reference")
            if who and who.startswith("Device/"):
                ai_device = who

    # Human dispositions + escalations over this recommendation
    dispositions, escalations = [], []
    for e in audit_bundle.get("entry", []):
        ae = e["resource"]
        etype = ae.get("type", {}).get("code")
        if etype == "oversight-decision":
            reason = None
            for ext in ae.get("extension", []):
                if ext.get("url", "").endswith("oversight-reason-ext"):
                    reason = ext["valueCodeableConcept"]["coding"][0]["code"]
            note = None
            for ent in ae.get("entity", []):
                for d in ent.get("detail", []):
                    if d.get("type") == "reason-note":
                        note = d.get("valueString")
            dispositions.append({
                "who": ae.get("agent", [{}])[0].get("who", {}).get("reference"),
                "disposition": ae.get("subtype", [{}])[0].get("code"),
                "reason": reason, "note": note, "when": ae.get("recorded"),
            })
        elif etype == "escalation":
            escalations.append({
                "triggered_rules": [st.get("code") for st in ae.get("subtype", [])],
                "when": ae.get("recorded"),
            })

    return {
        "guidance_response": gref,
        "recommendation_status": gr.get("status"),
        "patient": gr.get("subject", {}).get("reference"),
        "produced_at": gr.get("occurrenceDateTime"),
        "produced_by_ai": ai_device or gr.get("performer", {}).get("reference"),
        "dispositions": dispositions,
        "escalations": escalations,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("guidance_id")
    ap.add_argument("--base", default="http://localhost:8080/fhir")
    ap.add_argument("--token", default="")
    args = ap.parse_args()
    story = reconstruct(args.base, args.guidance_id, args.token)
    print(json.dumps(story, indent=2))
    print("\n--- Reconstructed oversight story ---")
    print(f"AI output:   {story['guidance_response']} (status={story['recommendation_status']})")
    print(f"For patient: {story['patient']}")
    print(f"Produced by: {story['produced_by_ai']} at {story['produced_at']}")
    for d in story["dispositions"]:
        print(f"Decision:    {d['who']} chose '{d['disposition']}' at {d['when']}"
              + (f" — reason: {d['reason']}" if d['reason'] else "")
              + (f" ('{d['note']}')" if d['note'] else ""))
    for e in story["escalations"]:
        print(f"Escalation:  triggered by {e['triggered_rules']} at {e['when']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
