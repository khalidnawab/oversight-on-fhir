import json

SYSTEM_INSTRUCTIONS = (
    "You are a clinical decision-support agent proposing antibiotic de-escalation for suspected sepsis. "
    "You are advisory only: never write orders. Produce ONLY schema-valid JSON. Every rationale item MUST "
    "cite evidence by fhir_reference (e.g. DiagnosticReport/dr-1) or knowledge_source_id from the provided "
    "knowledge passages. Leave candidacy.recommended_dose null — dosing is computed by a deterministic tool, "
    "not by you. If susceptibilities needed to narrow are absent, set recommended_action to "
    "'insufficient_information'."
)


def build_prompt(context, knowledge_passages: list) -> str:
    ctx = {
        "patient_reference": context.patient_reference,
        "encounter_reference": context.encounter_reference,
        "current_regimen": context.current_regimen,
        "allergies": context.allergies,
        "susceptibilities": context.susceptibilities,
        "culture_conclusions": context.culture_conclusions,
    }
    kp = [{"knowledge_source_id": p.passage_id, "source": p.source, "text": p.text} for p in knowledge_passages]
    return (
        f"{SYSTEM_INSTRUCTIONS}\n\n"
        f"CLINICAL CONTEXT (from FHIR):\n{json.dumps(ctx, indent=2)}\n\n"
        f"KNOWLEDGE PASSAGES (cite by knowledge_source_id):\n{json.dumps(kp, indent=2)}\n\n"
        f"Produce the de-escalation recommendation now."
    )
