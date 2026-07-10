from oversight.routing.confidence import self_consistency_score


def _sample(action, agent):
    return {"candidacy": {"recommended_action": action, "recommended_agent": agent}}


def test_full_agreement_is_high():
    samples = [_sample("narrow", "cefazolin")] * 3
    score, method, rationale = self_consistency_score(samples)
    assert score == 1.0
    assert method == "self_consistency"


def test_split_lowers_score():
    samples = [_sample("narrow", "cefazolin"), _sample("narrow", "cefazolin"), _sample("continue", None)]
    score, _, _ = self_consistency_score(samples)
    assert abs(score - 2 / 3) < 1e-9


def test_single_sample_defaults_to_one():
    score, _, _ = self_consistency_score([_sample("narrow", "cefazolin")])
    assert score == 1.0
