from oversight.clinical.tool import run_deterministic_tool
from oversight.orchestrator.prompt import build_prompt
from oversight.routing.confidence import self_consistency_score
from oversight.routing.engine import decide_routing
from oversight.schema.validate import load_model_schema, validate_recommendation

_DEFAULT_DISCLOSURE = "AI-generated stewardship suggestion — not an order; requires clinician review."


class Orchestrator:
    """Runs the Section 3 loop. Calls the backend through the seam; contains no dosing arithmetic
    and no FHIR wire code (Section 5)."""

    def __init__(self, backend, threshold: float = 0.7, n_samples: int = 3,
                 severe_crcl: float = 30.0, neutropenia_cutoff: float = 0.5,
                 disclosure_text: str = _DEFAULT_DISCLOSURE):
        self._backend = backend
        self._threshold = threshold
        self._n = n_samples
        self._severe_crcl = severe_crcl
        self._neutropenia_cutoff = neutropenia_cutoff
        self._disclosure = disclosure_text

    def run_with_context(self, ctx, knowledge_passages: list) -> dict:
        schema = load_model_schema()
        prompt = build_prompt(ctx, knowledge_passages)
        result = self._backend.generate(prompt, schema, n_samples=self._n)
        rec = result.recommendation

        # Confidence from self-consistency over samples (Section 9.2).
        score, method, rationale = self_consistency_score(result.samples or [rec])
        rec["confidence"] = {"score": round(score, 3), "method": method, "rationale": rationale}

        candidate_agent = rec.get("candidacy", {}).get("recommended_agent")

        # Deterministic tool owns all dosing/interaction/contraindication computation (Section 4.3).
        if candidate_agent:
            tool_result = run_deterministic_tool(
                candidate_agent=candidate_agent, patient=ctx.patient_dict(),
                allergies=ctx.allergies, current_meds=[m["medication"] for m in ctx.current_regimen])
            rec["deterministic_tool_result"] = tool_result
        else:
            tool_result = {"renal_dose_adjustment": {}, "interactions": [], "contraindications": []}
            rec["deterministic_tool_result"] = tool_result

        # Routing: either trigger escalates (Section 9).
        rec["routing"] = decide_routing(ctx, candidate_agent or "", tool_result,
                                        confidence_score=score, threshold=self._threshold,
                                        severe_crcl=self._severe_crcl, neutropenia_cutoff=self._neutropenia_cutoff)

        # Disclosure is code-owned and kept short/consistent — never the model's (often verbose) text.
        rec["disclosure_text"] = self._disclosure

        validate_recommendation(rec)
        return rec
