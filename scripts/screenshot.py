"""Seed a few oversight decisions for a realistic dashboard, then screenshot the three screens."""
import copy
from pathlib import Path

from playwright.sync_api import sync_playwright

from oversight.config import Settings
from oversight.fhir.client import FhirClient
from oversight.oversight.service import OversightService

OUT = Path(__file__).parent.parent / "screenshots"
OUT.mkdir(exist_ok=True)

_REC = {"schema_version": "0.1.0", "patient_reference": "Patient/clean-1", "encounter_reference": "Encounter/enc-clean-1",
        "candidacy": {"is_deescalation_candidate": "yes",
            "current_regimen": [{"medication": "piperacillin-tazobactam", "fhir_reference": "MedicationRequest/mr-clean-1"}],
            "recommended_action": "narrow", "recommended_agent": "cefazolin", "recommended_dose": None},
        "rationale": [{"assertion": "MSSA susceptible to cefazolin.",
            "evidence": [{"type": "fhir_resource", "fhir_reference": "DiagnosticReport/dr-clean-1",
                          "document_reference": None, "text_span": None, "knowledge_source_id": None}]}],
        "deterministic_tool_result": None,
        "confidence": {"score": 1.0, "method": "self_consistency", "rationale": "3/3"},
        "routing": {"decision": "surface", "triggered_high_risk_rules": [], "below_confidence_threshold": False},
        "disclosure_text": "AI generated."}

SEED = [("accept", None), ("accept", None), ("accept", None),
        ("reject", "data-vintage"), ("reject", "data-vintage"),
        ("edit", "clinical-disagreement"), ("reject", "missing-information"),
        ("edit", "patient-specific-factor")]


def seed():
    s = Settings()
    svc = OversightService(FhirClient.from_settings(s), model="claude-opus-4-8", version="0.1.0", backend="demo")
    for disp, reason in SEED:
        refs = svc.persist_recommendation(copy.deepcopy(_REC))
        svc.capture_disposition(refs["guidance_response"], "Practitioner/dr-alice",
                                disposition=disp, reason_code=reason, note=("note" if reason else None))
    print(f"seeded {len(SEED)} dispositions")


def shoot():
    pages = {"census": "http://127.0.0.1:8000/", "patient": "http://127.0.0.1:8000/patient/u-cole/enc-u-cole",
             "dashboard": "http://127.0.0.1:8000/dashboard"}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=2)
        for name, url in pages.items():
            page.goto(url)
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(700)
            page.screenshot(path=str(OUT / f"{name}.png"), full_page=True)
            print(f"shot {name}")
        browser.close()


if __name__ == "__main__":
    seed()
    shoot()
