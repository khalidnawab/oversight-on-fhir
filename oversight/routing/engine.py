from oversight.routing.rules import evaluate_high_risk


def decide_routing(ctx, candidate_agent: str, tool_result: dict,
                   confidence_score: float, threshold: float,
                   severe_crcl: float = 30.0, neutropenia_cutoff: float = 0.5) -> dict:
    """Combine the two independent escalation triggers (Section 9). Either forces escalate.
    Returns the `routing` block for the recommendation schema."""
    fired = evaluate_high_risk(ctx, candidate_agent, tool_result,
                               severe_crcl=severe_crcl, neutropenia_cutoff=neutropenia_cutoff)
    below = confidence_score < threshold
    decision = "escalate" if (fired or below) else "surface"
    return {"decision": decision, "triggered_high_risk_rules": fired, "below_confidence_threshold": below}
