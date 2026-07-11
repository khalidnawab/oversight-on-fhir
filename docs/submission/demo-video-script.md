# Oversight-on-FHIR — Demonstration Video Script

**HL7 AI Challenge 2026 · Author: Khalid Nawab · Synthetic data only — no PHI**
**Target runtime: ~6:30 (hard cap 10:00). Format: screen capture + voiceover.**

The film has one job: prove the claim *the agent proposes, the clinician disposes, and
the disposition is standard FHIR any client can retrieve*. Every second should serve that
claim. Register: concrete demo, standards vocabulary, no marketing gloss.

---

## Pre-flight setup (do this before recording)

1. **Stack up:** `docker compose up -d hapi`, then load data:
   `uv run python scripts/load_fixtures.py` and
   `uv run python scripts/generate_synthetic_data.py`.
2. **Backend choice — read this.** Record the reasoning flow (Segments 2–4) on the
   **frontier** backend so the recommendation is genuinely the model's output; the
   fresh-assessment wait (~15–20 s) is trimmed in the edit. If you prefer a fully
   deterministic take, use `OVERSIGHT_BACKEND=demo`, but then **say so on camera** —
   "for a reproducible walkthrough this uses a recorded backend; the reasoning is the
   frontier model's" — never imply demo output is live inference. Set the backend in
   `.env`, then restart uvicorn (no hot reload).
3. **Clean state:** click **Reset test data** in the sidebar once before you start, so
   the dashboard and Reviewed list begin empty.
4. **Panel open:** make sure the right-hand **FHIR activity** panel is expanded (not
   collapsed) and the "writes only" box is unchecked to start.
5. **Browser:** 1600×900 capture, zoom 110–125 % for legibility, hide bookmarks bar.
6. **Terminal (for Segment 5):** dark theme, large font (~18 pt), window cleared.
7. **Two tabs ready:** app at `http://localhost:8000/`, and the published IG at
   `https://khalidnawab.github.io/oversight-on-fhir/`.
8. Run once end-to-end without recording to confirm the clean case narrows to
   **cefazolin** and the high-risk case **escalates**.

---

## Segment 1 — The gap (0:00–0:30)

**On screen:** Title card → one slide.
- Title card (3 s): "Oversight-on-FHIR — physician oversight of agentic clinical AI as
  first-class FHIR. Khalid Nawab · HL7 AI Challenge 2026 · synthetic data only."
- Slide: left column "Mandated" (FDA GMLP · EU AI Act Art. 14 · NIST AI RMF · AMA);
  right column "Observable" with a single struck-through word "nowhere."

**Narration:**
> "Every major framework — the FDA, the EU AI Act, NIST, the AMA — requires that a
> clinician be able to understand and override what an agentic AI system does. None of
> them says how that oversight decision is captured, represented, or measured once the
> system is running. Oversight of agentic clinical AI is mandated nearly everywhere and
> observable nearly nowhere. This closes that gap."

---

## Segment 2 — The loop (0:30–2:00)

**On screen:** Census at `http://localhost:8000/`.
- Let the worklist render; assessments populate. Point the cursor at the **FHIR activity**
  panel as `GET` rows stream in.
- Click into the clean patient (`/patient/clean-1/enc-clean-1`). Land on the
  **Recommendation** tab.
- Slowly scroll the recommendation: action ("Narrow to cefazolin"), the stewardship
  assessment, then the **rationale list** — hover the evidence chips (blue `[FHIR]` and
  amber `[Guideline]`).
- Click the **Labs & Cultures** tab briefly to show the real chart data (culture,
  susceptibilities, creatinine), then back to Recommendation.
- Point at the **deterministic tool** card (renal dose, interaction/contraindication).

**Narration:**
> "This is an antimicrobial-stewardship unit. The agent scans each patient over FHIR —
> you can watch it read the chart in the activity panel on the right: medications,
> cultures, renal function, allergies. For this patient it recommends narrowing broad-
> spectrum therapy to cefazolin. Two things make the recommendation trustworthy. First,
> every clinical assertion is linked to evidence — this chip points to the FHIR
> DiagnosticReport that grew the organism; this one to the stewardship guideline. An
> assertion with no evidence fails validation and never reaches the clinician. Second,
> the dosing and interaction checks are computed in code, never by the language model."

---

## Segment 3 — The routing (2:00–2:45)

**On screen:** Navigate to the high-risk patient (`/patient/hr-1/enc-hr-1`).
- The **escalation banner** is at the top. Point to the named rule
  (`allergy_to_candidate`).
- Scroll to show there is **no confident recommendation to accept** — the screen asks for
  a human.

**Narration:**
> "Not every case should surface as a confident suggestion. This patient has a documented
> allergy to the candidate agent. A deterministic high-risk rule fired and routed the case
> to a human — and the important word is deterministic. The model didn't decide to
> escalate; code did, before the recommendation was ever shown. Allergy, non-
> susceptibility, severe renal impairment, neutropenia — these are hard-coded gates, not
> model judgment."

---

## Segment 4 — The disposition (2:45–3:45)

**On screen:** Back to the clean patient (`/patient/clean-1/enc-clean-1`).
- Point at the **AI disclosure** line (⚑ "AI-generated stewardship suggestion — not an
  order; requires clinician review").
- Select **Reject**. The reason box appears. Choose **data-vintage** from the dropdown;
  type a short note ("Repeat culture from today shows a resistant isolate.").
- Before clicking, hover the **writes only** box in the FHIR panel and check it.
- Click **Record decision**. On the redirect, point to the highlighted **`POST AuditEvent`**
  row that appears in the panel. Click that row → the **raw resource viewer** opens showing
  the `OversightEvent` JSON. Point at `type`, `subtype = reject`, the reason extension, and
  `entity.what` → the GuidanceResponse.

**Narration:**
> "The clinician is told plainly that this is an AI suggestion, not an order. They accept,
> edit, or reject — and when they override, they give a structured reason from a defined
> value set. Here: reject, because the data is stale. Watch the activity panel — the moment
> I record the decision, it becomes a FHIR resource: a POST of an AuditEvent. I'll click it
> and open the raw resource straight off the server. This is the whole contribution — the
> human oversight decision is now a first-class, queryable FHIR resource: what was decided,
> the reason, and a pointer to the exact AI output it was decided over."

---

## Segment 5 — The climax: independent retrieval (3:45–5:15)

**On screen:** Terminal, no app code visible.
- Run `uv run python scripts/demo_oversight.py` to produce/settle a recommendation +
  disposition; copy the printed GuidanceResponse id.
- Run `uv run python scripts/independent_client.py <gr-id>`.
- As output prints, let it breathe. Optionally show one raw `curl` against the FHIR base
  (`curl http://localhost:8080/fhir/GuidanceResponse/<id>`) to underline "plain REST."

**Narration:**
> "Here's the test that matters. This is an unaffiliated client — plain REST against the
> FHIR server, zero project code. It fetches the GuidanceResponse, the Provenance that
> attributes the recommendation to the AI device with its model identity, and the
> AuditEvent that records the human decision. From standard FHIR alone it reconstructs who
> decided what, when, over which AI output, and why. Nothing proprietary. If it's real
> FHIR, anyone's system can read it — which is exactly what independent implementability
> means."

---

## Segment 6 — Dashboard + Implementation Guide (5:15–6:00)

**On screen:** `http://localhost:8000/dashboard`.
- Point to the KPI tiles: total decisions, **override rate**, **escalations**, and the
  starred **data-vintage** (automation-bias) metric. Note the panel logs the
  `GET AuditEvent?_count=…` query as the page loads.
- Cut to the published IG tab (`https://khalidnawab.github.io/oversight-on-fhir/`). Show
  the home page (the "complementary to the HL7 AI Transparency on FHIR IG" framing), then
  click **Profiles → Oversight Event** to show the element table and required bindings.

**Narration:**
> "Because the decisions are real resources, governance is just a query. This dashboard is
> computed live from FHIR AuditEvent queries — no separate database — and it produces the
> exact metrics regulators ask for and institutions can't currently generate: override rate
> by reason, escalation rate, and a rising data-vintage rate as an automation-bias signal.
> And this isn't only an application. It's a draft Implementation Guide — the OversightEvent
> profile, the AI-authorship Provenance, the terminology — published and browsable,
> explicitly complementary to HL7's AI Transparency on FHIR guide. That guide covers AI
> influence on data; this one covers the human decision over agentic output."

---

## Segment 7 — Scale and equity (6:00–6:30)

**On screen:** Show `.env` with `OVERSIGHT_BACKEND=frontier`, change it to `local`, save;
cut to the sidebar **Backend** badge reflecting the change after restart.

**Narration:**
> "One last thing. The reasoning backend is a configuration choice, not a code change. The
> same system runs on a hosted frontier model, or on a local open-weight model with no
> external calls and no license fees — deployable where frontier APIs are unaffordable or
> prohibited. Standards-native, containerized, portable by configuration. The agent
> proposes, the clinician disposes, and the disposition is standard FHIR anyone can read."

**End card:** repo `github.com/khalidnawab/oversight-on-fhir` · IG
`khalidnawab.github.io/oversight-on-fhir` · "Synthetic data only — no PHI or PII."

---

## Editing notes

- Trim any fresh-assessment latency (Segments 2–4) to keep pace; a subtle speed-ramp over
  a loading spinner is fine — don't fake output.
- Keep the FHIR activity panel visible in every app shot; it's the through-line that makes
  "everything is FHIR" legible.
- Caption the FHIR resource names on screen (GuidanceResponse, Provenance, AuditEvent /
  OversightEvent) as they first appear.
- Total spoken words ≈ 900–950 at a calm pace ≈ 6.5 min. If long, cut Segment 2's Labs tab
  detour and tighten Segment 7.
- No music bed is needed; if used, keep it low and neutral. No AI-authorship anywhere in
  titles or credits.
