# Oversight-on-FHIR

Instrumented physician oversight of agentic clinical AI (antibiotic de-escalation demonstrator).
HL7 AI Challenge 2026 submission. Synthetic data only — no PHI.

## Quick start

1. `docker compose up -d`  — start the local HAPI FHIR R4 server (wait ~2 min on first boot).
2. `uv sync`  — install Python deps.
3. `copy .env.example .env`  — then set `ANTHROPIC_API_KEY` in your environment for the frontier backend.
4. `uv run python scripts/load_fixtures.py`  — load synthetic patients.
5. `uv run pytest`  — run the test suite.

## Configuration

All environment-specific values are `OVERSIGHT_`-prefixed env vars; see `.env.example`.
Switching the reasoning backend is a config change, never a code change:
`OVERSIGHT_BACKEND=frontier` (hosted model, synthetic data only) or `OVERSIGHT_BACKEND=local` (on-prem stub).

## Safety

The frontier backend refuses to run unless `OVERSIGHT_SYNTHETIC_DATA_ONLY=true` — real patient
data and the external API are mutually exclusive by policy and in code.
