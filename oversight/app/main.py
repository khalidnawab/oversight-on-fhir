import datetime as _dt
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from oversight.app import cds_hooks
from oversight.app.dashboard import aggregate_oversight
from oversight.config import Settings
from oversight.errors import FhirError
from oversight.fhir.client import FhirClient
from oversight.fhir.log import activity_log
from oversight.inference.factory import get_backend
from oversight.oversight import taxonomy as t
from oversight.oversight.service import OversightService
from oversight.orchestrator.census import CensusScanner
from oversight.orchestrator.chart import build_chart
from oversight.orchestrator.context import ContextBuilder
from oversight.orchestrator.loop import Orchestrator
from oversight.rag.retriever import Retriever

_TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
_STATIC = Path(__file__).parent / "static"
# (pid, eid, backend) -> (rec, guidance_ref). The census and the patient view share this, so an
# assessment is computed + persisted once and clicking "Review" is instant afterwards.
_REC_CACHE: dict = {}
# (pid, eid, backend) -> {disposition, reason, note, guidance_ref, when, patient_name, location}.
# Patients whose decision has been recorded; they move off the pending census into "Reviewed".
_REVIEWED: dict = {}
# Single sample keeps each assessment one fast model call and avoids nested thread pools inside
# FastAPI's worker threads. (Self-consistency with n>1 is available in the backend/CLI, but the
# interactive app favors responsiveness; the safety-critical escalations are rule-based, not
# confidence-based.)
_N_SAMPLES = 1


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    app = FastAPI(title="Oversight-on-FHIR")
    app.mount("/static", StaticFiles(directory=str(_STATIC)), name="static")

    def _svc() -> OversightService:
        return OversightService(FhirClient.from_settings(settings), model=settings.model,
                                version="0.1.0", backend=settings.backend)

    def ctx(**kw) -> dict:
        return {"backend": settings.backend, "enable_reset": settings.enable_reset, **kw}

    def _assess(pid: str, eid: str):
        """Compute (once) the agent's recommendation for a patient, persist it, and cache it.
        Shared by the census worklist and the patient detail view so Review is instant after scan."""
        key = (pid, eid, settings.backend)
        if key in _REC_CACHE:
            return _REC_CACHE[key]
        cc = ContextBuilder(FhirClient.from_settings(settings)).build(pid, eid)
        passages = Retriever().retrieve(
            f"de-escalation stop duration IV to PO {', '.join(cc.allergies)}", k=3)
        orch = Orchestrator(get_backend(settings), threshold=settings.confidence_threshold, n_samples=_N_SAMPLES)
        rec = orch.run_with_context(cc, knowledge_passages=passages)
        guidance_ref = _svc().persist_recommendation(rec)["guidance_response"]
        _REC_CACHE[key] = (rec, guidance_ref)
        return rec, guidance_ref

    def _is_reviewed(e) -> bool:
        return (e.patient_id, e.encounter_id, settings.backend) in _REVIEWED

    @app.get("/", response_class=HTMLResponse)
    def census(request: Request):
        # Deterministic triage only — renders instantly. Per-patient agent assessments load lazily
        # via /api/assessment so the worklist never blocks on the model. Reviewed patients drop off.
        all_entries = CensusScanner(FhirClient.from_settings(settings)).scan()
        entries = [e for e in all_entries if not _is_reviewed(e)]
        counts = {k: sum(1 for e in entries if e.eligibility == k)
                  for k in ("eligible", "insufficient", "monitoring", "not_eligible")}
        scanned_at = _dt.datetime.now().strftime("%H:%M")
        return _TEMPLATES.TemplateResponse(request, "census.html",
            ctx(entries=entries, counts=counts, scanned_at=scanned_at, reviewed_count=len(_REVIEWED)))

    @app.get("/reviewed", response_class=HTMLResponse)
    def reviewed(request: Request):
        items = sorted(_REVIEWED.values(), key=lambda r: r.get("when", ""), reverse=True)
        return _TEMPLATES.TemplateResponse(request, "reviewed.html",
            ctx(items=items, reviewed_count=len(_REVIEWED)))

    @app.get("/api/assessment/{pid}/{eid}")
    def api_assessment(pid: str, eid: str):
        """Lazy per-patient agent assessment for the census (populates + caches the recommendation)."""
        try:
            rec, _ = _assess(pid, eid)
        except Exception:
            return JSONResponse({"ok": False})
        return JSONResponse({"ok": True,
                             "action": rec["candidacy"]["recommended_action"],
                             "agent": rec["candidacy"]["recommended_agent"],
                             "escalate": rec["routing"]["decision"] == "escalate",
                             "rules": rec["routing"]["triggered_high_risk_rules"]})

    @app.get("/api/fhir-log")
    def api_fhir_log(since: int = 0):
        """Increments of the FHIR activity ring buffer for the live panel (polled ~1s)."""
        entries, latest = activity_log.snapshot(since)
        return JSONResponse({"entries": entries, "latest": latest})

    @app.get("/patient/{pid}/{eid}", response_class=HTMLResponse)
    def patient(request: Request, pid: str, eid: str):
        client = FhirClient.from_settings(settings)
        entry = CensusScanner(client).classify(pid)
        chart = build_chart(client, pid)
        rec, guidance_ref = _assess(pid, eid)
        return _TEMPLATES.TemplateResponse(request, "clinician.html", ctx(
            rec=rec, guidance_ref=guidance_ref, reasons=t.REASON_CODES, pid=pid, eid=eid, chart=chart,
            patient_name=(entry.patient_name if entry else pid),
            location=(entry.location if entry else ""),
            day_of_therapy=(entry.day_of_therapy if entry else 0)))

    @app.post("/disposition")
    def disposition(guidance_ref: str = Form(...), disposition: str = Form(...),
                    reason_code: str = Form(""), note: str = Form(""),
                    pid: str = Form(""), eid: str = Form("")):
        try:
            _svc().capture_disposition(guidance_ref, "Practitioner/dr-alice", disposition=disposition,
                                       reason_code=(reason_code or None), note=(note or None))
        except FhirError:
            # The recommendation this decision refers to is no longer on the server (e.g. it was
            # cleared by "Reset test data" while this page was open). Ask for a fresh review.
            return HTMLResponse(
                "<p style='font-family:system-ui;max-width:640px;margin:3rem auto'>"
                "This recommendation is no longer current — it was likely cleared by a reset while "
                "this page was open. <a href='/'>Return to the census</a> and re-open the patient to "
                "record a decision on a fresh recommendation.</p>", status_code=409)
        # Move the patient off the pending census into the Reviewed section.
        if pid and eid:
            entry = CensusScanner(FhirClient.from_settings(settings)).classify(pid)
            _REVIEWED[(pid, eid, settings.backend)] = {
                "pid": pid, "eid": eid, "disposition": disposition,
                "reason": reason_code or None, "note": note or None, "guidance_ref": guidance_ref,
                "when": _dt.datetime.now().strftime("%H:%M"),
                "patient_name": entry.patient_name if entry else pid,
                "location": entry.location if entry else "",
            }
        return RedirectResponse(url="/", status_code=303)

    @app.post("/reset")
    def reset(request: Request):
        # Test-only affordance; return 404 when disabled so it isn't exposed in a non-demo build.
        if not settings.enable_reset:
            raise HTTPException(status_code=404)
        # CSRF defense without session infra: reject cross-origin POSTs. A browser always sends
        # Origin on a cross-site form POST; same-origin form posts and CLI tools (no Origin) pass.
        origin = request.headers.get("origin")
        if origin is not None and urlparse(origin).netloc != request.headers.get("host", ""):
            raise HTTPException(status_code=403, detail="cross-origin reset blocked")
        _svc().reset_recorded()
        _REC_CACHE.clear()
        _REVIEWED.clear()
        activity_log.clear()  # after reset_recorded(): its DELETE traffic is wiped too
        return RedirectResponse(url=request.headers.get("referer") or "/", status_code=303)

    @app.get("/dashboard", response_class=HTMLResponse)
    def dashboard(request: Request):
        stats = aggregate_oversight(settings.fhir_base_url, settings.fhir_bearer_token)
        return _TEMPLATES.TemplateResponse(request, "dashboard.html", ctx(stats=stats))

    @app.get("/cds-services")
    def cds_discovery():
        return JSONResponse(cds_hooks.discovery_document())

    @app.get("/cds-hooks", response_class=HTMLResponse)
    def cds_hooks_page(request: Request):
        import json as _json
        disclosure = "AI-generated stewardship suggestion — not an order; requires clinician review."
        narrow_rec = {"candidacy": {"recommended_action": "narrow", "recommended_agent": "cefazolin"},
                      "rationale": [{"assertion": "Blood culture grew MSSA susceptible to cefazolin.", "evidence": []},
                                    {"assertion": "Antibiogram names cefazolin the preferred narrow agent for MSSA.", "evidence": []}],
                      "routing": {"decision": "surface", "triggered_high_risk_rules": []},
                      "disclosure_text": disclosure}
        escalate_rec = {"candidacy": {"recommended_action": "narrow", "recommended_agent": "cefazolin"},
                        "rationale": [], "routing": {"decision": "escalate", "triggered_high_risk_rules": ["allergy_to_candidate"]},
                        "disclosure_text": disclosure}
        cards = [cds_hooks.recommendation_to_card(narrow_rec, "GuidanceResponse/gr-example"),
                 cds_hooks.recommendation_to_card(escalate_rec, "GuidanceResponse/gr-example-2")]
        return _TEMPLATES.TemplateResponse(request, "cds_hooks.html", ctx(
            discovery=_json.dumps(cds_hooks.discovery_document(), indent=2), cards=cards,
            service_id=cds_hooks.SERVICE_ID))

    @app.post("/cds-services/" + cds_hooks.SERVICE_ID)
    def cds_service(payload: dict):
        c = payload.get("context", {})
        pid = (c.get("patientId") or "clean-1").replace("Patient/", "")
        eid = c.get("encounterId", "enc-clean-1").replace("Encounter/", "")
        rec, guidance_ref = _assess(pid, eid)
        return JSONResponse({"cards": [cds_hooks.recommendation_to_card(rec, guidance_ref)]})

    return app


app = create_app()
