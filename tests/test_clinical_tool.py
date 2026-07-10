from oversight.clinical.tool import run_deterministic_tool


def test_facade_assembles_full_result():
    result = run_deterministic_tool(
        candidate_agent="cefazolin",
        patient={"age": 60, "weight_kg": 70, "serum_creatinine": 1.0, "is_female": False},
        allergies=["cefazolin"],
        current_meds=["piperacillin-tazobactam"],
    )
    assert "renal_dose_adjustment" in result
    assert "interactions" in result
    assert "contraindications" in result
    assert result["renal_dose_adjustment"]["crcl"] is not None
    assert result["contraindications"][0]["type"] == "allergy"


def test_facade_handles_missing_renal_inputs():
    result = run_deterministic_tool(candidate_agent="cefazolin", patient={}, allergies=[], current_meds=[])
    assert result["renal_dose_adjustment"]["dose"] is None or result["renal_dose_adjustment"]["note"] is not None
