BASE_CANONICAL = "https://oversight-on-fhir.org/fhir"
REASON_CS_URL = f"{BASE_CANONICAL}/CodeSystem/oversight-reason"
REASON_VS_URL = f"{BASE_CANONICAL}/ValueSet/oversight-reason-vs"
DISPOSITION_CS_URL = f"{BASE_CANONICAL}/CodeSystem/oversight-disposition"
DISPOSITION_VS_URL = f"{BASE_CANONICAL}/ValueSet/oversight-disposition-vs"
EVENT_TYPE_CS_URL = f"{BASE_CANONICAL}/CodeSystem/oversight-event-type"
HIGH_RISK_CS_URL = f"{BASE_CANONICAL}/CodeSystem/high-risk-rule"
REASON_EXT_URL = f"{BASE_CANONICAL}/StructureDefinition/oversight-reason-ext"

REASON_CODES = [
    {"code": "clinical-disagreement", "display": "Clinician disagrees with the clinical judgment"},
    {"code": "missing-information", "display": "The agent lacked information the clinician has"},
    {"code": "patient-specific-factor", "display": "A patient-specific consideration the agent did not weigh"},
    {"code": "data-vintage", "display": "The clinician has newer data than the agent did"},
]
DISPOSITION_CODES = [
    {"code": "accept", "display": "Accept"},
    {"code": "edit", "display": "Edit"},
    {"code": "reject", "display": "Reject"},
]
EVENT_TYPE_CODES = [
    {"code": "oversight-decision", "display": "Human oversight decision over agentic AI output"},
    {"code": "escalation", "display": "Escalation of an agentic AI recommendation to a human"},
]

_REASONS = {c["code"] for c in REASON_CODES}
_DISPOSITIONS = {c["code"] for c in DISPOSITION_CODES}


def is_valid_reason(code: str) -> bool:
    return code in _REASONS


def is_valid_disposition(code: str) -> bool:
    return code in _DISPOSITIONS
