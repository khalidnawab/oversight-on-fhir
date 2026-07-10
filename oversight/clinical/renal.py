import json
from dataclasses import dataclass
from pathlib import Path

_DOSING = json.loads((Path(__file__).parent / "data" / "renal_dosing.json").read_text(encoding="utf-8"))


@dataclass
class RenalDoseResult:
    agent: str
    crcl: float | None
    crcl_band: str | None
    dose: str | None
    adjusted: bool
    note: str | None = None


def cockcroft_gault(age: int, weight_kg: float, serum_creatinine: float, is_female: bool) -> float:
    """Deterministic creatinine clearance (mL/min). All dosing math lives here, never in the LLM."""
    if serum_creatinine <= 0:
        raise ValueError("serum_creatinine must be > 0")
    crcl = ((140 - age) * weight_kg) / (72 * serum_creatinine)
    if is_female:
        crcl *= 0.85
    return crcl


def adjust_dose(agent: str, crcl: float) -> RenalDoseResult:
    agent_key = agent.strip().lower()
    spec = _DOSING.get(agent_key)
    if spec is None:
        return RenalDoseResult(agent=agent, crcl=crcl, crcl_band=None, dose=None, adjusted=False,
                               note=f"No renal dosing table for {agent!r}; clinician review required.")
    for band in spec["bands"]:
        if band["min"] <= crcl <= band["max"]:
            return RenalDoseResult(agent=agent, crcl=crcl, crcl_band=band["label"],
                                   dose=band["dose"], adjusted=band["adjusted"])
    return RenalDoseResult(agent=agent, crcl=crcl, crcl_band=None, dose=spec["normal_dose"], adjusted=False)
