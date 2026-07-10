from dataclasses import asdict

from oversight.clinical.renal import RenalDoseResult, adjust_dose, cockcroft_gault
from oversight.clinical.safety import check_contraindications, check_interactions


def run_deterministic_tool(candidate_agent: str, patient: dict, allergies: list[str],
                           current_meds: list[str], cross_react: bool = True) -> dict:
    """The single deterministic-tool entry point (Section 4.3 / Section 5). Pure function; no model.
    Populates the `deterministic_tool_result` block of a recommendation (Section 8)."""
    renal = _renal(candidate_agent, patient)
    return {
        "renal_dose_adjustment": asdict(renal),
        "interactions": check_interactions(candidate_agent, current_meds),
        "contraindications": check_contraindications(candidate_agent, allergies, cross_react=cross_react),
    }


def _renal(candidate_agent: str, patient: dict) -> RenalDoseResult:
    required = ("age", "weight_kg", "serum_creatinine", "is_female")
    if not all(k in patient for k in required):
        return RenalDoseResult(agent=candidate_agent, crcl=None, crcl_band=None, dose=None,
                               adjusted=False, note="Insufficient renal inputs; clinician review required.")
    crcl = cockcroft_gault(age=patient["age"], weight_kg=patient["weight_kg"],
                           serum_creatinine=patient["serum_creatinine"], is_female=patient["is_female"])
    return adjust_dose(candidate_agent, crcl)
