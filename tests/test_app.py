import httpx
import pytest
from fastapi.testclient import TestClient

from oversight.app.main import create_app
from oversight.config import Settings


def _client(monkeypatch):
    monkeypatch.setenv("OVERSIGHT_BACKEND", "demo")
    return TestClient(create_app(Settings()))


def _hapi_up():
    try:
        return httpx.get("http://localhost:8080/fhir/metadata", timeout=3).status_code == 200
    except Exception:
        return False


@pytest.mark.skipif(not _hapi_up(), reason="HAPI not running")
def test_census_home_renders(monkeypatch):
    c = _client(monkeypatch)
    r = c.get("/")
    assert r.status_code == 200
    assert "census" in r.text.lower()
    assert "Eligible for review" in r.text
    # at least one known patient surname from the unit
    assert "Rivera" in r.text or "Webb" in r.text


def test_cds_discovery(monkeypatch):
    c = _client(monkeypatch)
    r = c.get("/cds-services")
    assert r.status_code == 200
    assert r.json()["services"][0]["hook"] == "patient-view"


@pytest.mark.skipif(not _hapi_up(), reason="HAPI not running")
def test_clean_patient_view_surfaces(monkeypatch):
    c = _client(monkeypatch)
    r = c.get("/patient/clean-1/enc-clean-1")
    assert r.status_code == 200
    assert "cefazolin" in r.text
    assert "Escalated to human review" not in r.text


@pytest.mark.skipif(not _hapi_up(), reason="HAPI not running")
def test_high_risk_patient_view_escalates(monkeypatch):
    c = _client(monkeypatch)
    r = c.get("/patient/hr-1/enc-hr-1")
    assert r.status_code == 200
    assert "Escalated" in r.text
    assert "allergy_to_candidate" in r.text


@pytest.mark.skipif(not _hapi_up(), reason="HAPI not running")
def test_disposition_then_dashboard(monkeypatch):
    c = _client(monkeypatch)
    # produce + persist a recommendation to get a guidance ref
    view = c.get("/patient/clean-1/enc-clean-1")
    # extract the persisted guidance ref from the rendered page
    import re
    m = re.search(r"GuidanceResponse/gr-[0-9a-f]+", view.text)
    assert m
    gref = m.group(0)
    resp = c.post("/disposition", data={"guidance_ref": gref, "disposition": "reject",
                                        "reason_code": "data-vintage", "note": "Newer culture."},
                  follow_redirects=False)
    assert resp.status_code == 303
    dash = c.get("/dashboard")
    assert dash.status_code == 200
    assert "oversight decisions" in dash.text.lower()


@pytest.mark.skipif(not _hapi_up(), reason="HAPI not running")
def test_reset_clears_recorded_data(monkeypatch):
    import re
    c = _client(monkeypatch)
    # record a decision so there is something to clear
    view = c.get("/patient/clean-1/enc-clean-1")
    gref = re.search(r"GuidanceResponse/gr-[0-9a-f]+", view.text).group(0)
    c.post("/disposition", data={"guidance_ref": gref, "disposition": "reject",
                                 "reason_code": "data-vintage", "note": "x"}, follow_redirects=False)
    resp = c.post("/reset", follow_redirects=False)
    assert resp.status_code == 303
    dash = c.get("/dashboard")
    # after reset the decisions KPI is zero
    assert re.search(r"Oversight decisions</div>\s*<div class=\"value\">0<", dash.text)


@pytest.mark.skipif(not _hapi_up(), reason="HAPI not running")
def test_cds_service_returns_card(monkeypatch):
    c = _client(monkeypatch)
    r = c.post(f"/cds-services/deescalation-oversight",
               json={"hook": "patient-view", "context": {"patientId": "clean-1", "encounterId": "enc-clean-1"}})
    assert r.status_code == 200
    cards = r.json()["cards"]
    assert cards and "summary" in cards[0]
