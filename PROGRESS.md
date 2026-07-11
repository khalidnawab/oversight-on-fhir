# Progress snapshot — Oversight-on-FHIR

_Last saved: 2026-07-11. Target: HL7 AI Challenge 2026 (deadline July 15). See `BUILD_SPEC.md` §17._

## Public (as of 2026-07-11)

- Repo public: **https://github.com/khalidnawab/oversight-on-fhir** (default branch `main`).
- IG published: **https://khalidnawab.github.io/oversight-on-fhir/** (served from `gh-pages` = built `ig/output` + `.nojekyll`).
- History was scrubbed of AI-authorship before going public (trailers stripped, `docs/superpowers/` removed from all commits). Local backup only: tag `pre-scrub-backup` + `%TEMP%\oversee-prescrub-backup.bundle` — never push these. Keep `docs/superpowers/` untracked going forward.

## Submission artifacts (in `docs/submission/`)

- `executive-summary.md`, `solution-narrative.md` — drafted in Khalid's voice, no AI attribution; clinical + stewardship claims cited to verified sources (Leone 2014, Tabah 2016 [PMID 26703860], Kam 2024, SSC 2021, IDSA/SHEA 2016, Bell 2014, Costelloe 2010, Silva/Cochrane 2013, Huebner 2019, Zhang 2018). Wording deliberately does not outrun the evidence — de-escalation-specific resistance/cost benefit framed as unproven; stewardship rationale is the anchor.
- `demo-video-script.md` — shot-by-shot (~6:30), includes pre-flight setup + backend-honesty guardrail.
- **Author must independently verify the cited PMIDs before final submission.**

## Still to do (session 2026-07-11 handoff)

1. **Record the demo video** per the script.
2. **Submit via the HubSpot form** by end of July 14.
3. Watch the "Everything You Need to Know Before You Apply" webinar; reconcile against any form requirements.

## Status: working end-to-end on the real model

- **~122 tests pass** (`uv run pytest`); 1 live-API test is opt-in. New this session: FHIR activity log panel (`oversight/fhir/log.py`, `/api/fhir-log`, raw-resource viewer, `static/fhir-log.js`).
- HAPI search-result cache disabled in `docker-compose.yml` (`reuse_cached_search_results_millis: -1`) — fixes the old "count lag" flake; recreating the container wipes its H2 DB, so reload fixtures + generated data after.
- The web app runs on the **real Claude model** (`claude-opus-4-8`) by default; key loads from gitignored `.env` (`ANTHROPIC_API_KEY`).
- HAPI FHIR R4 runs in Docker with a 9-patient synthetic unit loaded.

## What's built (all committed)

| Area | State |
| --- | --- |
| Model-agnostic seam (`InferenceBackend`) | frontier (Claude, structured output) / local stub / scripted-demo; swap by config |
| Deterministic clinical tool | Cockcroft-Gault renal dosing, interaction/contraindication checks — no LLM math |
| RAG | local BM25 over synthetic antibiogram/formulary + real stewardship-guideline corpus |
| Census scan | deterministic eligibility triage (day-of-therapy, broad-spectrum, cultures) → worklist |
| Orchestrator + routing | stewardship reasoning; high-risk rules (allergy/renal/neutropenia) + self-consistency; `narrow/continue/stop/switch-iv-to-po/broaden/escalate` |
| Oversight layer (the contribution) | recommendation→GuidanceResponse, AI authorship→Provenance, decision→OversightEvent(AuditEvent); reason taxonomy CodeSystem/ValueSet |
| Independent client | `scripts/independent_client.py` reconstructs who/what/when/why over plain REST, zero project imports |
| Draft IG | FSH profiles + terminology + examples; `npx fsh-sushi ig` compiles clean; IG↔code URL alignment tested |
| CDS Hooks | discovery + card mapping + human-facing explainer page |
| UI | census (instant, lazy assessments) · patient tabs (Recommendation/Orders/Labs & Cultures from FHIR) · Reviewed view · oversight analytics dashboard · reset-test-data |
| FHIR activity panel | live right-rail log of every FHIR read/write on all pages; writes highlighted + click through to raw JSON; writes-only filter |

## How to run

```
docker compose up -d hapi                     # FHIR server
uv run python scripts/load_fixtures.py        # 2 fixtures + clinician
uv run python scripts/generate_synthetic_data.py  # 7-patient unit
uv run uvicorn oversight.app.main:app --port 8000  # app at http://localhost:8000
uv run pytest                                 # tests
uv run python scripts/verify_frontier.py      # live model check (needs key)
```

- Backend: unset/`frontier` (real model), `demo` (offline, instant), or `local` (stub) via `OVERSIGHT_BACKEND` in `.env`.
- Demo flow: Census (pending, assessments fill in ~18s each) → Review → record decision → back to Census → find under Reviewed. Independent proof: `scripts/demo_oversight.py` then `scripts/independent_client.py <gr-id>`.

## Known limits / next steps

- Frontier page loads carry real-model latency (~18s per fresh assessment; cached after). `demo` backend for instant walkthroughs.
- Reviewed list is session-scoped (in-memory; resets on restart/Reset). Decisions themselves persist in FHIR as AuditEvents. Could derive Reviewed from FHIR to survive restarts.
- Guideline RAG passages are accurate but demo-authored — need clinical sign-off before real use.
- Not yet built: deterministic IV-to-PO stability guard (from vitals), duration-vs-syndrome sanity, Notes tab (DocumentReference), full IG Publisher HTML render (needs Jekyll).
- Submission: intent email sent; executive summary + solution narrative drafted and cited (`docs/submission/`); repo public at github.com/khalidnawab/oversight-on-fhir; IG published at khalidnawab.github.io/oversight-on-fhir. **Still to do: demo video; final review + submit via HubSpot form.**
