"""CDS Hooks mapping (Section 5 / Section 12). The recommendation maps to a CDS Hooks card;
the accept/edit/reject actions map to the card's suggestion/override semantics feeding the same
oversight capture path. This module provides the discovery document and the card mapping so the
standards-native surface is complete (FHIR + SMART + CDS Hooks)."""

SERVICE_ID = "deescalation-oversight"


def discovery_document() -> dict:
    return {
        "services": [
            {
                "hook": "patient-view",
                "title": "Antibiotic de-escalation oversight",
                "description": "Surfaces an agentic de-escalation recommendation with AI disclosure and "
                               "an accept/edit/reject oversight control.",
                "id": SERVICE_ID,
            }
        ]
    }


def recommendation_to_card(rec: dict, guidance_ref: str) -> dict:
    """Map a de-escalation recommendation to a CDS Hooks card."""
    candidacy = rec.get("candidacy", {})
    action = candidacy.get("recommended_action")
    agent = candidacy.get("recommended_agent")
    escalated = rec.get("routing", {}).get("decision") == "escalate"

    if escalated:
        summary = "Escalated to human review (de-escalation)"
        indicator = "warning"
        detail = ("This case was routed to a human by a deterministic high-risk rule: "
                  + ", ".join(rec["routing"].get("triggered_high_risk_rules", [])) + ".")
    elif action == "narrow" and agent:
        summary = f"Consider de-escalation to {agent}"
        indicator = "info"
        detail = "\n".join(f"- {r['assertion']}" for r in rec.get("rationale", []))
    else:
        summary = "Insufficient information to recommend de-escalation"
        indicator = "info"
        detail = "The agent could not confirm a de-escalation opportunity from available data."

    card = {
        "summary": summary,
        "indicator": indicator,
        "detail": f"{detail}\n\n_{rec.get('disclosure_text', '')}_",
        "source": {"label": "Oversight-on-FHIR", "topic": {"text": "AI-generated, requires oversight"}},
        "links": [{"label": "Review and disposition", "url": f"/patient-from-guidance/{guidance_ref}", "type": "absolute"}],
    }
    # Suggestions carry the disposition semantics; selecting one is the accept path in an EHR.
    if not escalated and action == "narrow" and agent:
        card["suggestions"] = [{"label": f"Accept: narrow to {agent}", "uuid": guidance_ref}]
        card["selectionBehavior"] = "at-most-one"
    return card
