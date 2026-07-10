from collections import Counter


def self_consistency_score(samples: list[dict]) -> tuple[float, str, str]:
    """Fraction of samples agreeing with the modal (action, agent) pair (Section 9.2)."""
    if not samples:
        return 0.0, "self_consistency", "no samples"
    keys = [(s.get("candidacy", {}).get("recommended_action"),
             s.get("candidacy", {}).get("recommended_agent")) for s in samples]
    counts = Counter(keys)
    modal, n = counts.most_common(1)[0]
    score = n / len(samples)
    rationale = f"{n}/{len(samples)} samples agree on action={modal[0]}, agent={modal[1]}"
    return score, "self_consistency", rationale
