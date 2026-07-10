from oversight.clinical.safety import check_contraindications, check_interactions


def test_allergy_to_candidate_is_contraindication():
    result = check_contraindications(candidate_agent="cefazolin", allergies=["cefazolin"])
    assert any(c["type"] == "allergy" for c in result)
    assert result[0]["severity"] == "absolute"


def test_no_allergy_no_contraindication():
    assert check_contraindications(candidate_agent="cefazolin", allergies=["penicillin"]) == []


def test_beta_lactam_cross_reactivity_flagged():
    # documented penicillin allergy + cephalosporin candidate => cross-reactivity caution
    result = check_contraindications(candidate_agent="cefazolin", allergies=["penicillin"], cross_react=True)
    assert any(c["type"] == "cross_reactivity" for c in result)


def test_interaction_table_hit():
    result = check_interactions(candidate_agent="ceftriaxone", current_meds=["calcium gluconate"])
    assert any(i["with"] == "calcium gluconate" for i in result)


def test_interaction_no_hit():
    assert check_interactions(candidate_agent="cefazolin", current_meds=["acetaminophen"]) == []
