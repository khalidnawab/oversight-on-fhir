# Oversight-on-FHIR

Instrumented physician oversight of agentic clinical AI (antibiotic de-escalation demonstrator).
HL7 AI Challenge 2026 submission. Synthetic data only — no PHI.

**Browsable Implementation Guide:** https://khalidnawab.github.io/oversight-on-fhir/

## The idea in brief

FHIR is HL7's standard for exchanging health data: a catalog of standard record types
("resources" — `Patient`, `MedicationRequest`, `Observation`, …) served over a standard
REST API that modern EHRs already expose. This project proposes no new resource types.
Three existing ones each get a job: a `GuidanceResponse` carries the AI's recommendation,
a `Provenance` attributes it to the AI device (transparency), and an `AuditEvent` records
the clinician's accept/edit/reject decision with a coded reason (accountability). A draft
IG profiles all three. Because the oversight trail is ordinary FHIR, any FHIR-capable
system can store and query it — it is EHR-agnostic and not tied to this agent.

## Quick start (local dev)

1. `docker compose up -d hapi`  — start the local HAPI FHIR R4 server (wait ~2 min on first boot).
2. `uv sync`  — install Python deps.
3. `copy .env.example .env`  — optionally set `ANTHROPIC_API_KEY` to use the frontier backend.
4. `uv run python scripts/load_fixtures.py`  — load synthetic patients + clinician.
5. `uv run pytest`  — run the test suite (123 tests; HAPI-dependent ones skip if it is down).
6. `uv run uvicorn oversight.app.main:app --reload`  — clinician UI + dashboard at http://localhost:8000

## Full containerized demo

`docker compose up --build` starts HAPI **and** the app (app at http://localhost:8000). Then load
fixtures once against the running server: `uv run python scripts/load_fixtures.py`.

## Scripted demo path

- Clinician view: http://localhost:8000/patient/clean-1/enc-clean-1 (surfaces) and
  http://localhost:8000/patient/hr-1/enc-hr-1 (escalates via a deterministic high-risk rule).
- Record a rejection with a `data-vintage` reason, then open the dashboard: http://localhost:8000/dashboard
- Reconstruct the oversight story with the **independent** read-only client (zero project code):
  `uv run python scripts/demo_oversight.py` then `uv run python scripts/independent_client.py <gr-id>`

## Implementation guide

The draft IG (profiles + terminology + examples) is published at
**https://khalidnawab.github.io/oversight-on-fhir/** and its source lives in `ig/`. Build the
conformance resources with `npx fsh-sushi ig` (outputs to `ig/fsh-generated/`); the browsable HTML
site is produced by the HL7 IG Publisher (`java -jar ig/publisher.jar -ig ig`), which additionally
needs Jekyll installed.

## Configuration

All environment-specific values are `OVERSIGHT_`-prefixed env vars; see `.env.example`.
Switching the reasoning backend is a config change, never a code change:
`OVERSIGHT_BACKEND=frontier` (hosted model, synthetic data only), `local` (on-prem stub), or
`demo` (offline scripted, for the deterministic recorded demo).

## Standards surface

FHIR R4 · US Core-aligned resources · SMART-on-FHIR bearer auth (config-supplied) ·
CDS Hooks service (`GET /cds-services`, see `docs/CDS-HOOKS.md`) · draft IG in `ig/`.

## Safety

- The frontier backend refuses to run unless `OVERSIGHT_SYNTHETIC_DATA_ONLY=true` — real patient
  data and the external API are mutually exclusive by policy and in code.
- All dosing arithmetic, renal adjustment, and interaction/contraindication checking is deterministic
  code (`oversight/clinical/`), never the language model.
- The system is advisory only: it writes recommendation and oversight-event resources, never orders.
