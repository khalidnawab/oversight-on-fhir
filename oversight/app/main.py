from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from oversight.app import cds_hooks
from oversight.app.dashboard import aggregate_oversight
from oversight.config import Settings
from oversight.fhir.client import FhirClient
from oversight.inference.factory import get_backend
from oversight.oversight import taxonomy as t
from oversight.oversight.service import OversightService
from oversight.orchestrator.context import ContextBuilder
from oversight.orchestrator.loop import Orchestrator
from oversight.rag.retriever import Retriever

_TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# Demo roster (synthetic patients loaded by scripts/load_fixtures.py).
DEMO_PATIENTS = [
    {"pid": "clean-1", "eid": "enc-clean-1", "label": "Ana Rivera — clean de-escalation candidate"},
    {"pid": "hr-1", "eid": "enc-hr-1", "label": "Daniel Okafor — high-risk (cefazolin allergy)"},
]


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    app = FastAPI(title="Oversight-on-FHIR")

    def _svc() -> OversightService:
        return OversightService(FhirClient.from_settings(settings), model=settings.model,
                                version="0.1.0", backend=settings.backend)

    def _orchestrator() -> Orchestrator:
        return Orchestrator(get_backend(settings), threshold=settings.confidence_threshold, n_samples=3)

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request):
        return _TEMPLATES.TemplateResponse(request, "home.html", {"patients": DEMO_PATIENTS})

    @app.get("/patient/{pid}/{eid}", response_class=HTMLResponse)
    def patient(request: Request, pid: str, eid: str):
        client = FhirClient.from_settings(settings)
        ctx = ContextBuilder(client).build(pid, eid)
        passages = Retriever().retrieve(f"de-escalation {', '.join(a for a in ctx.allergies) or 'MSSA cefazolin'}", k=2)
        rec = _orchestrator().run_with_context(ctx, knowledge_passages=passages)
        refs = _svc().persist_recommendation(rec)
        return _TEMPLATES.TemplateResponse(request, "clinician.html", {
            "rec": rec, "guidance_ref": refs["guidance_response"],
            "reasons": t.REASON_CODES, "pid": pid, "eid": eid,
        })

    @app.post("/disposition")
    def disposition(guidance_ref: str = Form(...), disposition: str = Form(...),
                    reason_code: str = Form(""), note: str = Form("")):
        _svc().capture_disposition(guidance_ref, "Practitioner/dr-alice", disposition=disposition,
                                   reason_code=(reason_code or None), note=(note or None))
        return RedirectResponse(url="/dashboard", status_code=303)

    @app.get("/dashboard", response_class=HTMLResponse)
    def dashboard(request: Request):
        stats = aggregate_oversight(settings.fhir_base_url, settings.fhir_bearer_token)
        return _TEMPLATES.TemplateResponse(request, "dashboard.html", {"stats": stats})

    @app.get("/cds-services")
    def cds_discovery():
        return JSONResponse(cds_hooks.discovery_document())

    @app.post("/cds-services/" + cds_hooks.SERVICE_ID)
    def cds_service(payload: dict):
        ctx = payload.get("context", {})
        pid = (ctx.get("patientId") or "clean-1").replace("Patient/", "")
        eid = ctx.get("encounterId", "enc-clean-1").replace("Encounter/", "")
        client = FhirClient.from_settings(settings)
        cctx = ContextBuilder(client).build(pid, eid)
        rec = _orchestrator().run_with_context(cctx, knowledge_passages=[])
        refs = _svc().persist_recommendation(rec)
        return JSONResponse({"cards": [cds_hooks.recommendation_to_card(rec, refs["guidance_response"])]})

    return app


app = create_app()
