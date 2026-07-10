from oversight.clinical.renal import RenalDoseResult, adjust_dose, cockcroft_gault


def test_cockcroft_gault_female_factor():
    # 60yo, 70kg, SCr 1.0: male CrCl = (80*70)/(72*1.0)=77.8; female *0.85
    male = cockcroft_gault(age=60, weight_kg=70, serum_creatinine=1.0, is_female=False)
    female = cockcroft_gault(age=60, weight_kg=70, serum_creatinine=1.0, is_female=True)
    assert round(male, 1) == 77.8
    assert round(female, 1) == round(male * 0.85, 1)


def test_adjust_dose_normal_function():
    r = adjust_dose("cefazolin", crcl=90)
    assert isinstance(r, RenalDoseResult)
    assert r.adjusted is False
    assert "q8h" in r.dose


def test_adjust_dose_severe_impairment_flags_adjustment():
    r = adjust_dose("cefazolin", crcl=20)
    assert r.adjusted is True
    assert r.crcl_band == "10-34"


def test_unknown_agent_returns_no_recommendation():
    r = adjust_dose("madeup-cillin", crcl=90)
    assert r.dose is None
    assert r.note is not None
