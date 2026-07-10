from oversight.app import cds_hooks


def test_discovery_document_lists_service():
    doc = cds_hooks.discovery_document()
    assert doc["services"][0]["id"] == cds_hooks.SERVICE_ID
    assert doc["services"][0]["hook"] == "patient-view"


def test_surface_recommendation_becomes_info_card_with_suggestion():
    rec = {"candidacy": {"recommended_action": "narrow", "recommended_agent": "cefazolin"},
           "rationale": [{"assertion": "MSSA susceptible.", "evidence": []}],
           "routing": {"decision": "surface", "triggered_high_risk_rules": []},
           "disclosure_text": "AI generated."}
    card = cds_hooks.recommendation_to_card(rec, "GuidanceResponse/gr-1")
    assert card["indicator"] == "info"
    assert "cefazolin" in card["summary"]
    assert card["suggestions"][0]["uuid"] == "GuidanceResponse/gr-1"


def test_escalated_recommendation_becomes_warning_card_without_suggestion():
    rec = {"candidacy": {"recommended_action": "narrow", "recommended_agent": "cefazolin"},
           "rationale": [], "routing": {"decision": "escalate", "triggered_high_risk_rules": ["allergy_to_candidate"]},
           "disclosure_text": "AI generated."}
    card = cds_hooks.recommendation_to_card(rec, "GuidanceResponse/gr-2")
    assert card["indicator"] == "warning"
    assert "allergy_to_candidate" in card["detail"]
    assert "suggestions" not in card
