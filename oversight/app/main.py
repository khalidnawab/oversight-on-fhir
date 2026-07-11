import datetime as _dt
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from oversight.app import cds_hooks
from oversight.app.dashboard import aggregate_oversight
from oversight.config import Settings
from oversight.fhir.client import FhirClient
from oversight.inference.factory import get_backend
from oversight.oversight import taxonomy as t
from oversight.oversight.service import OversightService
from oversight.orchestrator.census import CensusScanner
from oversight.orchestrator.context import ContextBuilder
from oversight.orchestrator.loop import Orchestrator
from oversight.rag.retriever import Retriever

_TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
_STATIC = Path(__file__).parent / "static"
_HEADLINE_CACHE: dict = {}
_REC_CACHE: dict = {}  # (pid, eid, backend) -> (rec, guidance_ref); avoids re-running the model + re-persisting on every view


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    app = FastAPI(title="Oversight-on-FHIR")
    app.mount("/static", StaticFiles(directory=str(_STATIC)), name="static")

    def _svc() -> OversightService:
        return OversightService(FhirClient.from_settings(settings), model=settings.model,
                                version="0.1.0", backend=settings.backend)

    def _orchestrator() -> Orchestrator:
        return Orchestrator(get_backend(settings), threshold=settings.confidence_threshold, n_samples=3)

    def ctx(**kw) -> dict:
        return {"backend": settings.backend, "enable_reset": settings.enable_reset, **kw}

    def _headline(entry) -> dict | None:
        key = (entry.patient_id, entry.encounter_id, settings.backend)
        if key in _HEADLINE_CACHE:
            return _HEADLINE_CACHE[key]
        try:
            cc = ContextBuilder(FhirClient.from_settings(settings)).build(entry.patient_id, entry.encounter_id)
            passages = Retriever().retrieve("de-escalation stop duration IV to PO", k=2)
            # Single sample for the worklist headline keeps the census fast/cheap on the frontier
            # backend; the patient detail view uses full self-consistency sampling.
            headline_orch = Orchestrator(get_backend(settings), threshold=settings.confidence_threshold, n_samples=1)
            rec = headline_orch.run_with_context(cc, knowledge_passages=passages)
            h = {"action": rec["candidacy"]["recommended_action"], "agent": rec["candidacy"]["recommended_agent"],
                 "escalate": rec["routing"]["decision"] == "escalate",
                 "rules": rec["routing"]["triggered_high_risk_rules"]}
        except Exception:
            h = None
        _HEADLINE_CACHE[key] = h
        return h

    @app.get("/", response_class=HTMLResponse)
    def census(request: Request):
        entries = CensusScanner(FhirClient.from_settings(settings)).scan()
        # Compute the per-patient agent assessments concurrently so the worklist loads quickly even
        # on the frontier backend (each is an independent model call; results are cached).
        eligible = [e for e in entries if e.eligibility == "eligible"]
        with ThreadPoolExecutor(max_workers=8) as ex:
            hl = list(ex.map(_headline, eligible))
        headlines = {e.patient_id: h for e, h in zip(eligible, hl)}
        counts = {k: sum(1 for e in entries if e.eligibility == k)
                  for k in ("eligible", "insufficient", "monitoring", "not_eligible")}
        scanned_at = _dt.datetime.now().strftime("%H:%M")
        return _TEMPLATES.TemplateResponse(request, "census.html",
            ctx(entries=entries, headlines=headlines, counts=counts, scanned_at=scanned_at))

    @app.get("/patient/{pid}/{eid}", response_class=HTMLResponse)
    def patient(request: Request, pid: str, eid: str):
        client = FhirClient.from_settings(settings)
        entry = CensusScanner(client).classify(pid)
        key = (pid, eid, settings.backend)
        if key in _REC_CACHE:
            rec, guidance_ref = _REC_CACHE[key]
        else:
            cc = ContextBuilder(client).build(pid, eid)
            passages = Retriever().retrieve(
                f"de-escalation stop duration IV to PO {', '.join(cc.allergies)}", k=3)
            rec = _orchestrator().run_with_context(cc, knowledge_passages=passages)
            guidance_ref = _svc().persist_recommendation(rec)["guidance_response"]
            _REC_CACHE[key] = (rec, guidance_ref)
        return _TEMPLATES.TemplateResponse(request, "clinician.html", ctx(
            rec=rec, guidance_ref=guidance_ref, reasons=t.REASON_CODES,
            patient_name=(entry.patient_name if entry else pid),
            location=(entry.location if entry else ""),
            day_of_therapy=(entry.day_of_therapy if entry else 0)))

    @app.post("/disposition")
    def disposition(guidance_ref: str = Form(...), disposition: str = Form(...),
                    reason_code: str = Form(""), note: str = Form("")):
        _svc().capture_disposition(guidance_ref, "Practitioner/dr-alice", disposition=disposition,
                                   reason_code=(reason_code or None), note=(note or None))
        return RedirectResponse(url="/dashboard", status_code=303)

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
        _HEADLINE_CACHE.clear()
        _REC_CACHE.clear()
        return RedirectResponse(url=request.headers.get("referer") or "/", status_code=303)

    @app.get("/dashboard", response_class=HTMLResponse)
    def dashboard(request: Request):
        stats = aggregate_oversight(settings.fhir_base_url, settings.fhir_bearer_token)
        return _TEMPLATES.TemplateResponse(request, "dashboard.html", ctx(stats=stats))

    @app.get("/cds-services")
    def cds_discovery():
        return JSONResponse(cds_hooks.discovery_document())

    @app.post("/cds-services/" + cds_hooks.SERVICE_ID)
    def cds_service(payload: dict):
        c = payload.get("context", {})
        pid = (c.get("patientId") or "clean-1").replace("Patient/", "")
        eid = c.get("encounterId", "enc-clean-1").replace("Encounter/", "")
        client = FhirClient.from_settings(settings)
        cc = ContextBuilder(client).build(pid, eid)
        rec = _orchestrator().run_with_context(cc, knowledge_passages=[])
        refs = _svc().persist_recommendation(rec)
        return JSONResponse({"cards": [cds_hooks.recommendation_to_card(rec, refs["guidance_response"])]})

    return app


app = create_app()
