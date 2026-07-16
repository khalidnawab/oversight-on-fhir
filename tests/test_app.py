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


def test_cds_hooks_page_renders(monkeypatch):
    c = _client(monkeypatch)
    r = c.get("/cds-hooks")
    assert r.status_code == 200
    assert "CDS Hooks integration" in r.text
    assert "Consider de-escalation to cefazolin" in r.text  # example info card
    assert "Escalated to human review" in r.text or "warning" in r.text  # example warning card


@pytest.mark.skipif(not _hapi_up(), reason="HAPI not running")
def test_api_assessment_returns_action(monkeypatch):
    c = _client(monkeypatch)
    r = c.get("/api/assessment/clean-1/enc-clean-1")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["action"] in ("narrow", "continue", "stop", "switch-iv-to-po", "broaden",
                              "insufficient_information", "escalate")


@pytest.mark.skipif(not _hapi_up(), reason="HAPI not running")
def test_clean_patient_view_surfaces(monkeypatch):
    c = _client(monkeypatch)
    r = c.get("/patient/clean-1/enc-clean-1")
    assert r.status_code == 200
    assert "cefazolin" in r.text
    assert "Escalated to human review" not in r.text
    # chart tabs and EHR data present
    assert "panel-orders" in r.text and "panel-labs" in r.text
    assert "MedicationRequest" in r.text  # orders tab
    assert "Creatinine" in r.text          # labs tab


@pytest.mark.skipif(not _hapi_up(), reason="HAPI not running")
def test_high_risk_patient_view_escalates(monkeypatch):
    c = _client(monkeypatch)
    r = c.get("/patient/hr-1/enc-hr-1")
    assert r.status_code == 200
    assert "Escalated" in r.text
    assert "severe_renal_impairment" in r.text


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
                                        "reason_code": "data-vintage", "note": "Newer culture.",
                                        "pid": "clean-1", "eid": "enc-clean-1"},
                  follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == "/"  # back to the census
    dash = c.get("/dashboard")
    assert dash.status_code == 200
    assert "oversight decisions" in dash.text.lower()


@pytest.mark.skipif(not _hapi_up(), reason="HAPI not running")
def test_reviewed_flow_moves_patient_off_census(monkeypatch):
    import re
    c = _client(monkeypatch)
    # fresh reset so census/reviewed state is clean
    c.post("/reset", follow_redirects=False)
    view = c.get("/patient/hr-1/enc-hr-1")
    gref = re.search(r"GuidanceResponse/gr-[0-9a-f]+", view.text).group(0)
    # before deciding, hr-1 (Okafor) is on the census
    assert "Okafor" in c.get("/").text
    c.post("/disposition", data={"guidance_ref": gref, "disposition": "accept",
                                 "pid": "hr-1", "eid": "enc-hr-1"}, follow_redirects=False)
    # after deciding, hr-1 is off the census and on the reviewed page
    assert "Okafor" not in c.get("/").text
    reviewed = c.get("/reviewed").text
    assert "Okafor" in reviewed and "accepted" in reviewed


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


def test_reset_blocks_cross_origin_post(monkeypatch):
    c = _client(monkeypatch)
    resp = c.post("/reset", headers={"origin": "http://evil.example", "host": "testserver"},
                  follow_redirects=False)
    assert resp.status_code == 403


def test_reset_404_when_disabled(monkeypatch):
    monkeypatch.setenv("OVERSIGHT_BACKEND", "demo")
    monkeypatch.setenv("OVERSIGHT_ENABLE_RESET", "false")
    from oversight.app.main import create_app
    from oversight.config import Settings
    c = TestClient(create_app(Settings()))
    assert c.post("/reset", follow_redirects=False).status_code == 404


@pytest.mark.skipif(not _hapi_up(), reason="HAPI not running")
def test_cds_service_returns_card(monkeypatch):
    c = _client(monkeypatch)
    r = c.post(f"/cds-services/deescalation-oversight",
               json={"hook": "patient-view", "context": {"patientId": "clean-1", "encounterId": "enc-clean-1"}})
    assert r.status_code == 200
    cards = r.json()["cards"]
    assert cards and "summary" in cards[0]


def test_fhir_log_endpoint_incremental(monkeypatch):
    from oversight.fhir.log import activity_log
    c = _client(monkeypatch)
    activity_log.clear()
    start = activity_log.latest
    activity_log.append("GET", "Patient/p1", 200)
    activity_log.append("POST", "GuidanceResponse", 201, resource_id="GuidanceResponse/gr-1")
    body = c.get(f"/api/fhir-log?since={start}").json()
    assert [e["target"] for e in body["entries"]] == ["Patient/p1", "GuidanceResponse"]
    assert body["latest"] == start + 2
    # cursor past the end -> empty increment
    assert c.get(f"/api/fhir-log?since={start + 2}").json()["entries"] == []


@pytest.mark.skipif(not _hapi_up(), reason="HAPI not running")
def test_reset_clears_fhir_log(monkeypatch):
    from oversight.fhir.log import activity_log
    c = _client(monkeypatch)
    c.get("/")  # census scan generates FHIR reads
    assert c.get("/api/fhir-log?since=0").json()["entries"]
    c.post("/reset", follow_redirects=False)
    assert c.get("/api/fhir-log?since=0").json()["entries"] == []


def test_raw_viewer_rejects_non_allowlisted_type_without_fhir_call(monkeypatch):
    from oversight.fhir.log import activity_log
    c = _client(monkeypatch)
    before = activity_log.latest
    assert c.get("/fhir/Binary/abc/raw").status_code == 404
    assert activity_log.latest == before  # allowlist rejected it before any FHIR request


def test_raw_viewer_rejects_malformed_rid_without_fhir_call(monkeypatch):
    from oversight.fhir.log import activity_log
    c = _client(monkeypatch)
    before = activity_log.latest
    assert c.get("/fhir/Patient/clean-1%3F_format=xml/raw").status_code == 404
    assert activity_log.latest == before


@pytest.mark.skipif(not _hapi_up(), reason="HAPI not running")
def test_raw_viewer_renders_allowlisted_resource(monkeypatch):
    c = _client(monkeypatch)
    r = c.get("/fhir/Patient/clean-1/raw")
    assert r.status_code == 200
    assert "resourceType" in r.text and "Patient/clean-1" in r.text


@pytest.mark.skipif(not _hapi_up(), reason="HAPI not running")
def test_raw_viewer_404_on_missing_resource(monkeypatch):
    c = _client(monkeypatch)
    assert c.get("/fhir/Patient/does-not-exist-xyz/raw").status_code == 404


def test_fhir_activity_panel_on_every_page(monkeypatch):
    c = _client(monkeypatch)
    text = c.get("/cds-hooks").text
    assert 'id="fhir-log"' in text            # panel present in base template
    assert "writes only" in text              # filter control
    assert "/static/fhir-log.js" in text      # poller wired up


@pytest.mark.skipif(not _hapi_up(), reason="HAPI not running")
def test_dashboard_query_appears_in_fhir_log(monkeypatch):
    from oversight.fhir.log import activity_log
    c = _client(monkeypatch)
    activity_log.clear()
    start = activity_log.latest
    c.get("/dashboard")
    targets = [e["target"] for e in activity_log.since(start)]
    assert any(t.startswith("AuditEvent?_count=") for t in targets)
