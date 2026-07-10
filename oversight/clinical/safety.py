import json
from pathlib import Path

_DATA = json.loads((Path(__file__).parent / "data" / "contraindications.json").read_text(encoding="utf-8"))
_CEPHALOSPORINS = set(_DATA["cross_reactivity"]["cephalosporins"])
_PCN_TRIGGERS = set(_DATA["cross_reactivity"]["penicillin_triggers"])


def check_contraindications(candidate_agent: str, allergies: list[str], cross_react: bool = False) -> list[dict]:
    """Deterministic contraindication check. `allergies` are substances the patient reacts to."""
    agent = candidate_agent.strip().lower()
    allergy_set = {a.strip().lower() for a in allergies}
    out: list[dict] = []
    if agent in allergy_set:
        out.append({"type": "allergy", "agent": agent, "severity": "absolute",
                    "note": f"Documented allergy to {agent}; do not administer."})
    if cross_react and agent in _CEPHALOSPORINS and (allergy_set & _PCN_TRIGGERS):
        out.append({"type": "cross_reactivity", "agent": agent, "severity": "caution",
                    "note": "Penicillin allergy with a cephalosporin candidate; assess cross-reactivity."})
    return out


def check_interactions(candidate_agent: str, current_meds: list[str]) -> list[dict]:
    agent = candidate_agent.strip().lower()
    meds = {m.strip().lower() for m in current_meds}
    table = _DATA["interactions"].get(agent, [])
    return [row for row in table if row["with"].lower() in meds]
