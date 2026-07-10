from dataclasses import dataclass
from typing import Callable

from oversight.clinical.renal import cockcroft_gault


@dataclass(frozen=True)
class HighRiskRule:
    id: str
    description: str
    predicate: Callable  # (ctx, candidate_agent, tool_result, params) -> bool


def _allergy(ctx, agent, tool, p):
    return (any(c.get("type") == "allergy" for c in tool.get("contraindications", []))
            or agent.lower() in {a.lower() for a in ctx.allergies})


def _not_susceptible(ctx, agent, tool, p):
    for s in ctx.susceptibilities:
        if s["agent"].lower() == agent.lower() and not s["interpretation"].lower().startswith("suscept"):
            return True
    return False


def _severe_renal(ctx, agent, tool, p):
    if None in (ctx.age, ctx.weight_kg, ctx.serum_creatinine, ctx.is_female):
        return False
    crcl = cockcroft_gault(age=ctx.age, weight_kg=ctx.weight_kg,
                           serum_creatinine=ctx.serum_creatinine, is_female=ctx.is_female)
    return crcl < p["severe_crcl"]


def _neutropenia(ctx, agent, tool, p):
    return ctx.anc is not None and ctx.anc < p["neutropenia_cutoff"]


RULES: list[HighRiskRule] = [
    HighRiskRule("allergy_to_candidate", "Documented allergy to the candidate narrower agent.", _allergy),
    HighRiskRule("isolate_not_susceptible", "Isolate not susceptible to the proposed narrower agent.", _not_susceptible),
    HighRiskRule("severe_renal_impairment", "Severe renal impairment altering dosing.", _severe_renal),
    HighRiskRule("neutropenia", "Neutropenia or other immunocompromise.", _neutropenia),
]


def evaluate_high_risk(ctx, candidate_agent: str, tool_result: dict,
                       severe_crcl: float = 30.0, neutropenia_cutoff: float = 0.5) -> list[str]:
    """Return the ids of all high-risk rules that fire (Section 9.1). Deterministic; no model."""
    agent = candidate_agent or ""
    params = {"severe_crcl": severe_crcl, "neutropenia_cutoff": neutropenia_cutoff}
    return [r.id for r in RULES if r.predicate(ctx, agent, tool_result, params)]
