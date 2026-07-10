# Build Specification: Instrumented Physician Oversight of Agentic Clinical AI

**Working name:** Oversight-on-FHIR (agentic antibiotic de-escalation demonstrator)
**Audience:** the engineering agent building this system
**Status of this document:** authoritative build brief. It defines what to build and the constraints that must hold. Technology stack choices below the "must hold" line are yours to make.
**Immediate submission target:** HL7 AI Challenge 2026 — entries close **July 15, 2026, ~11:00 PM EDT** (deadline already extended once; treat July 14 as the practical cutoff). Section 17 defines the submission plan and the reduced demo scope that must be working by then. Where Section 17 conflicts with the build order in Section 16, Section 17 wins until the submission is in.

---

## 0. How to read this document

Sections 1 through 4 tell you *what this is for* and *what must be true of any implementation*. Sections 5 through 12 give the component-level specification. Section 13 defines the two build targets (the near-term public demo and the eventual production system) and what differs between them. Section 14 lists parameters that are still open; pick sensible defaults, make them configurable, and surface them rather than hard-coding them.

Treat the constraints in Section 4 as non-negotiable. Everything else is guidance you may improve on if you have a better idea, provided the constraints still hold.

---

## 1. Purpose and context

### 1.1 The problem this system exists to solve

Agentic AI systems plan and execute multi-step clinical work with limited human input at each step. Every major governance framework (AMA augmented-intelligence principles, NIST AI RMF, FDA Good Machine Learning Practice, EU AI Act Article 14) requires that a clinician be able to understand and override what such a system produces. None of them specifies how that oversight decision is *captured, represented, or measured* once a system is running in production.

The gap, stated plainly: oversight of agentic clinical AI is mandated nearly everywhere and observable nearly nowhere. The HL7 "AI Transparency on FHIR" implementation guide represents AI *influence on clinical data*, but not the human decision to accept, modify, or reject what an agentic system proposes. That missing layer (escalation, patient disclosure, easy human override, and structured tracking of when and why overrides happen) is the central research object of this project.

### 1.2 What we are building, in one paragraph

An autonomous, standards-native agentic system that performs a real clinical reasoning task (antibiotic de-escalation in suspected sepsis), wrapped in an instrumented oversight layer that makes every human oversight decision a first-class, standards-based, queryable FHIR resource. The clinical task is the vehicle. The oversight instrumentation and its FHIR representation are the contribution. If a reviewer takes away one thing from a demo, it should be this: the agent proposes, the clinician disposes, and that disposition (accept / edit / reject, with a structured reason) lands in the record as a Provenance and AuditEvent resource that any unaffiliated FHIR client can retrieve over standard REST.

### 1.3 Why antibiotic de-escalation in sepsis

It is clinically consequential, guideline-endorsed, and underserved. Multi-hospital evidence shows day-4 de-escalation is as safe as continued broad-spectrum therapy while cutting antibiotic days and length of stay, yet fewer than half of eligible patients are de-escalated, with more than two-fold variation across hospitals. It is also an ideal agentic testbed: the workflow is genuinely multi-step, every step touches standards-based data, and the decision is high-stakes enough that oversight behavior is worth measuring. Do not treat the clinical logic as the hard part. It is real and must be correct, but the engineering novelty is the oversight instrumentation.

### 1.4 The design thesis you are implementing

Oversight is not a compliance feature bolted onto an agent. It is an engineered, standards-based, measurable property of the system. Build it that way: the oversight layer is not a logging afterthought, it is a core subsystem with its own data model, its own FHIR profile, and its own REST surface.

---

## 2. Users and the interaction it supports

There are three human roles the system serves. Build for all three even in the demo, because the oversight story only makes sense across them.

1. **Treating clinician (primary).** Sees a de-escalation recommendation with its evidence, the disclosure that AI produced it, and a trivially easy path to accept, edit, or reject it. When they act, they supply a structured reason. When the system is unsure or a high-risk condition is present, they instead see an escalation rather than a recommendation.
2. **Oversight / stewardship reviewer.** Consumes the accumulated oversight events: how often clinicians override, for what reasons, how often the system escalates, and whether automation bias is detectable. In the demo this can be a simple read-only view driven entirely by querying oversight-event resources from the FHIR server (proving they are real resources, not internal logs).
3. **Downstream / unaffiliated FHIR client.** Not a person but a design constraint: an external application must be able to retrieve recommendations and oversight events as standard FHIR resources over REST, with no project-specific code. This is what "independent implementability" means and it must be demonstrable.

---

## 3. Core interaction loop (the clinical reasoning the agent performs)

For each eligible patient the agent autonomously executes this loop. The agent's agency lies in *orchestration and routing*, not in acting on the record. The system is advisory: it never writes an order, never modifies therapy, never discontinues a drug. The clinician's decision is the only action gate.

1. **Identify a suspected-sepsis candidate.** An adult admission with documented suspicion of infection in whom blood cultures were obtained and IV broad-spectrum antibiotics were started within 48 hours of presentation (Sepsis-3 aligned, community-onset population). Qualifying antibiotic classes and the exact window are configuration, not code (see Section 14).
2. **Retrieve relevant FHIR resources.** Active antimicrobials and their administration (`MedicationRequest`, `MedicationAdministration`), cultures and susceptibilities (`DiagnosticReport`, `Observation`), renal function (`Observation`), allergies (`AllergyIntolerance`), and notes (`DocumentReference`, resolving to `Binary`/`DocumentReference.content`).
3. **Judge information sufficiency.** Decide whether what was retrieved is enough to reason about de-escalation. If not, issue targeted follow-up queries. Insufficiency that cannot be resolved is itself a routing outcome (escalate for missing information), not a guess.
4. **Consult institutional knowledge via retrieval-augmented generation.** Query a curated corpus (institutional antibiogram, formulary) to ground the choice of a narrower agent. RAG over documents, not free recall.
5. **Invoke the deterministic clinical tool for all safety-critical computation.** Drug-interaction checking and renal dose adjustment are computed by deterministic code, never by the language model. No dosing arithmetic is performed by the LLM. This is a hard boundary (Section 4).
6. **Produce a structured, evidence-linked recommendation.** Schema-valid JSON in which every clinical assertion is linked to the specific FHIR resource or note excerpt that supports it. No unsupported claims (Section 8).
7. **Route on confidence and risk.** Low-confidence cases and pre-specified high-risk cases go to a human instead of surfacing as a confident recommendation. The high-risk rules are deterministic and evaluated in code (Section 9).

---

## 4. Non-negotiable constraints (these must hold in every implementation)

These are the load-bearing walls. Do not move them for convenience or speed.

1. **Model-agnostic seam.** The reasoning model sits behind a single narrow interface. Two interchangeable implementations must exist: a hosted frontier model reached over an API, and a local open-weight model (Qwen3-4B class with LoRA). Every other subsystem (FHIR access, orchestration, the deterministic tool, routing, oversight capture, the FHIR profile, the UI) imports the interface and never a concrete model. Swapping backends is a configuration change, never a code change. This single seam is what lets one codebase serve both build targets in Section 13; get it right first.
2. **Advisory only.** The system never writes clinical orders or mutates the therapy record. Its only writes to the FHIR server are the recommendation artifact and oversight-event resources. The clinician's decision is the action gate.
3. **Deterministic safety computation.** All dosing arithmetic, renal adjustment, and interaction checking is performed by deterministic code. The LLM may *request* a computation and *read* its result, but must never produce the number itself.
4. **Evidence-linking is mandatory.** Every clinical assertion in a recommendation carries a reference to the FHIR resource or note span that supports it. An assertion with no evidence link is a schema violation, not a stylistic lapse.
5. **Oversight events are FHIR resources, not logs.** Recommendations and oversight decisions are persisted to the FHIR server as resources conforming to the profiles in Section 10 and are retrievable over standard REST by an unaffiliated client with no bespoke code.
6. **Standards-native throughout.** HL7 FHIR R4, US Core profiles where applicable, OAuth 2.0 / SMART-on-FHIR authorization, and tool interfaces expressed as JSON-Schema function definitions consistent with emerging AI-to-API conventions.
7. **Configuration-driven and containerized.** The FHIR base URL, the model backend, the routing thresholds, the eligibility window, and every other environment-specific value are configuration. The whole system runs from containers with documented, reproducible setup. A different site should be able to run it by changing config, not code.
8. **On-premise-ready by construction.** Nothing in the architecture may assume an external service is reachable. The frontier-API backend is one selectable option; the system must run fully locally with the local backend and no outbound calls. (For the production target, no PHI ever leaves the premises.)
9. **No PHI to external services, ever.** When the frontier-API backend is selected, only synthetic data may flow through it. Real patient data and the frontier API are mutually exclusive by policy and should be enforced in code where feasible (for example, a guard that refuses the API backend unless a `synthetic_data_only` flag is set).

---

## 5. System architecture (component view)

Components, each independently testable, wired through explicit interfaces:

- **FHIR data-access layer.** Reads clinical resources from a FHIR R4 server over REST; writes recommendation and oversight-event resources back. The only component that knows FHIR wire details. Base URL is configuration.
- **Inference backend (the seam).** `InferenceBackend` interface. Implementations: `FrontierAPIBackend`, `LocalModelBackend`. Takes a prompt plus a tool/output schema; returns schema-valid structured output plus whatever the confidence subsystem needs (see Section 9).
- **Agent orchestrator.** Runs the Section 3 loop. Owns the control flow (retrieve, assess sufficiency, RAG, call the deterministic tool, assemble the recommendation, decide routing). Calls the backend through the seam. Contains no dosing arithmetic and no FHIR wire code.
- **Deterministic clinical tool.** Renal dose adjustment and drug-interaction / contraindication checking. Pure functions over structured inputs. No model involvement.
- **Knowledge retrieval (RAG).** Indexes and retrieves from the curated antibiogram/formulary corpus. Returns passages with citable identifiers so retrieved knowledge can be evidence-linked.
- **Routing engine.** Evaluates the deterministic high-risk rules and the confidence threshold and decides surface-vs-escalate. Deterministic; see Section 9.
- **Oversight layer.** Owns disclosure, escalation, and the capture of accept/edit/reject decisions with structured reasons. Translates decisions into the FHIR oversight-event resources of Section 10 and persists them.
- **Recommendation store / carrier.** Persists each recommendation as a retrievable FHIR resource (Section 10) so oversight events can reference it and clients can fetch it.
- **Clinician UI.** Presents recommendation, evidence, disclosure, and the accept/edit/reject control with reason capture; presents escalations distinctly. Drives all writes through the oversight layer.
- **CDS Hooks surface (interface required; implementation optional for the demo).** The oversight layer's API must be shaped so a CDS Hooks service can front it: the recommendation maps to a CDS Hooks card (summary, detail, source, links to the evidence), and the accept/edit/reject actions map to the card's suggestion/override semantics feeding the same oversight capture path. Implement the actual Hooks endpoint only if time allows; either way, document the mapping in the repo. This is the standard EHR-integration path and completes the standards-native story (FHIR + SMART + CDS Hooks).
- **Oversight dashboard (read-only).** Queries oversight-event resources from the FHIR server and summarizes override/escalation behavior. Must read only through the FHIR REST API to prove the resources are real.
- **Config and container layer.** Central configuration; container definitions for the FHIR server, the app, the model backend(s), and the vector store.

**Dependency rule.** Orchestrator, deterministic tool, routing, and oversight layer must not import the inference backend concretely or the FHIR wire layer directly beyond their defined interfaces. Enforce this with module boundaries so the seam cannot rot under deadline.

---

## 6. FHIR data-access layer

- Target FHIR R4. Assume US Core profiles for the clinical resources where they exist.
- Resource types read: `Patient`, `Encounter`, `Condition`, `MedicationRequest`, `MedicationAdministration`, `DiagnosticReport`, `Observation` (susceptibilities, renal function, hematology), `AllergyIntolerance`, `DocumentReference` (plus dereferencing note content).
- Resource types written: the recommendation carrier and the oversight-event resources (Section 10).
- Authorization via OAuth 2.0 / SMART-on-FHIR. In a local demo the server may be open, but the client must be built so that a bearer token is supplied through configuration and the design does not assume anonymous access.
- The base URL is a single configuration parameter. The exact same client code must work against a local HAPI server, an alternate FHIR server, and (later) a vendor sandbox. Do not encode server-specific assumptions.

---

## 7. Synthetic clinical data (for the public demo target)

The demo runs entirely on synthetic patients on a local FHIR server. This is a first-class build task, not an afterthought, because generic synthetic data will not exercise the de-escalation logic.

- Use Synthea to generate a base population, load it onto a local HAPI FHIR server, then **curate** a small set of patients that actually present a de-escalation decision arc: infection suspicion, blood cultures drawn, IV broad-spectrum antibiotics started within the window, and then a susceptibility result that supports narrowing.
- Synthea's default modules will not reliably produce that arc. Expect to author or adjust resources by hand (or via a custom Synthea module) so that each demo patient has a coherent, clinically plausible trajectory including the culture-and-susceptibility resources the agent must reason over.
- Build at least these fixtures:
  1. A clean de-escalation candidate (narrowing clearly supported by susceptibilities): the agent should produce a confident, evidence-linked recommendation.
  2. A high-risk case that must escalate (for example, a documented allergy to the candidate narrower agent, or an isolate not susceptible to it): the routing engine, not the model, forces escalation.
  3. An insufficient-information case (missing susceptibilities): the agent recognizes insufficiency and routes for missing information rather than guessing.
- Fixtures must be reproducible and version-controlled so the recorded demo is deterministic.

---

## 8. The reasoning model and its output contract

- **Backend abstraction.** As in Section 4.1. The frontier backend uses the provider's structured-output / tool-use mode to guarantee schema validity. The local backend uses constrained decoding to enforce the same schema. The orchestrator must not care which is active.
- **Output contract.** The model's recommendation output must validate against a published JSON Schema. Reject and retry on invalid output; never pass unvalidated model text downstream. Sketch of the required shape (finalize the schema as a versioned artifact in the repo):

```json
{
  "$schema": "https://.../deescalation-recommendation.schema.json",
  "schema_version": "0.1.0",
  "patient_reference": "Patient/{id}",
  "encounter_reference": "Encounter/{id}",
  "candidacy": {
    "is_deescalation_candidate": "yes | no | insufficient_information",
    "current_regimen": [
      { "medication": "string", "fhir_reference": "MedicationRequest/{id}" }
    ],
    "recommended_action": "narrow | continue | insufficient_information | escalate",
    "recommended_agent": "string | null",
    "recommended_dose": null
  },
  "rationale": [
    {
      "assertion": "string",
      "evidence": [
        {
          "type": "fhir_resource | note_excerpt | knowledge_passage",
          "fhir_reference": "DiagnosticReport/{id} | null",
          "document_reference": "DocumentReference/{id} | null",
          "text_span": "string | null",
          "knowledge_source_id": "string | null"
        }
      ]
    }
  ],
  "deterministic_tool_result": {
    "renal_dose_adjustment": "object (populated only by the deterministic tool)",
    "interactions": "array (populated only by the deterministic tool)",
    "contraindications": "array (populated only by the deterministic tool)"
  },
  "confidence": {
    "score": 0.0,
    "method": "string",
    "rationale": "string"
  },
  "routing": {
    "decision": "surface | escalate",
    "triggered_high_risk_rules": ["string"],
    "below_confidence_threshold": false
  },
  "disclosure_text": "string"
}
```

- **Evidence-linking is enforced at validation time.** Every element of `rationale` must carry at least one resolvable evidence reference. `recommended_dose` in `candidacy` is intentionally null: dose is owned by the deterministic tool and copied into `deterministic_tool_result`, never authored by the model.
- **Prompting and schema live in the repo as versioned artifacts.** The same prompt and schema are shared across both backends; that shared surface is what makes the pilot's existing extraction work reusable here.

---

## 9. Confidence and routing

Routing has two independent triggers. **Either** forces escalation.

### 9.1 Deterministic high-risk rules (evaluated in code, not by the model)

Evaluated by the routing engine against retrieved FHIR data and the deterministic tool output. If any fires, the case escalates regardless of model confidence:

1. A documented allergy to a candidate narrower agent.
2. An isolate not susceptible to the proposed narrower agent.
3. Polymicrobial or resistant bacteremia.
4. Severe renal impairment altering dosing.
5. Neutropenia or other immunocompromise.
6. Absence of documented source control.

These rules are clinical configuration reviewed by the clinical co-investigators. Implement them as data-driven, inspectable predicates, not buried conditionals, so they can be revised without touching orchestration.

### 9.2 Confidence threshold

- The recommendation carries a confidence score. Below a configurable threshold, the case escalates.
- Self-reported LLM confidence is weakly calibrated. Design the confidence subsystem so the *method* is swappable and does not compromise the design: support at least self-consistency (sample the reasoning several times and measure agreement) and, where the backend exposes them, token-level signals; a separate verifier pass over the drafted recommendation is an acceptable stronger option. Record which method produced the score in `confidence.method`.
- The threshold is configuration (Section 14), tunable without code changes.

### 9.3 Escalation experience

Escalation is not a dead end. It routes to a human (in production, to the infectious-diseases service) with the partial reasoning and the reason for escalation shown. The demo should present an escalation as a distinct, deliberate state, not an error.

---

## 10. Oversight layer and its FHIR representation (the contribution)

This is the part reviewers most care about. Build it with the most care.

### 10.1 What the oversight layer does

1. **Discloses.** Every recommendation shown to a clinician carries an explicit disclosure that AI produced it, using patient-facing disclosure language (text is configurable; content is owned by the clinical team / TEP).
2. **Escalates.** When routing says escalate, the layer makes reaching a human trivially easy and records that an escalation occurred.
3. **Captures every disposition.** Every accept, edit, or reject is captured with a structured reason drawn from a pre-specified taxonomy, plus optional free text, actor, timestamp, and a reference to the exact recommendation acted upon.

### 10.2 The override-reason taxonomy (define as a FHIR CodeSystem + ValueSet)

Minimum reason codes:

- `clinical-disagreement` (clinician disagrees with the clinical judgment)
- `missing-information` (the agent lacked information the clinician has)
- `patient-specific-factor` (a patient-specific consideration the agent did not weigh)
- `data-vintage` (the clinician has newer data than the agent did; this category is analytically important and must be first-class)

Disposition types: `accept`, `edit`, `reject`. Model these as a coded value as well.

### 10.3 FHIR resource model

Represent the flow with existing R4 resources; do not invent new resource types. Profile them.

- **The recommendation** is persisted as a retrievable FHIR resource so it can be referenced and independently fetched. Use `GuidanceResponse` as the primary carrier (it is the natural FHIR representation of the output of a decision-support process); its `outputParameters`/`result` carry the structured recommendation and the evidence links. (If you find `GuidanceResponse` too constraining for the evidence structure, `Communication` is an acceptable fallback carrier; justify the choice in the repo.)
- **AI authorship** is attributed with a `Provenance` resource whose `target` is the recommendation resource, whose `agent.who` references a `Device` representing the AI system (model identity, version, backend), and whose activity marks it as machine-generated. This mirrors how the HL7 AI Transparency work attributes AI influence, and is deliberately complementary to it.
- **The human oversight decision** is the novel object. Represent it as an **OversightEvent**, a profile on `AuditEvent`, carrying:
  - the actor (`agent` referencing a `Practitioner`),
  - the artifact reviewed (`entity` referencing the recommendation `GuidanceResponse`),
  - the disposition (`accept | edit | reject`) as a coded value,
  - the structured reason from the taxonomy ValueSet,
  - optional free-text note,
  - timestamp and outcome.
  A companion `Provenance` may record the lineage of the resulting human decision where an edit produces a modified artifact.
- **Escalations** are also recorded as oversight events (a distinct action code) so escalation frequency is queryable alongside overrides.

### 10.4 Deliverable framing

The profiles (OversightEvent on AuditEvent, the AI-authorship Provenance, the recommendation GuidanceResponse profile) plus the CodeSystem/ValueSet constitute a draft implementation guide with a reference implementation. This is not a "later" deliverable: author the profiles in FHIR Shorthand (FSH), build with SUSHI + the IG Publisher, and publish the rendered IG to a public GitHub Pages URL so a reviewer can click through profile pages, the CodeSystem/ValueSet, and examples. A draft IG is the standards-maturation artifact HL7 reviewers recognize instantly, and it is the single highest-leverage deliverable for the Challenge submission (Section 17). Where this project's representation complements the HL7 AI Transparency IG, that effort represents AI influence on clinical data; this profile represents the human decision over agentic output. Keep that distinction visible in the profile documentation, and reuse the AI Transparency IG's Device/Provenance patterns wherever possible so the two compose rather than compete.

### 10.5 The provable claim

An unaffiliated FHIR client, given only the base URL and appropriate auth, must be able to `GET` the recommendations and their oversight events and reconstruct who decided what, when, over which AI output, and why, with no project-specific code. Build a small independent read-only client (or a documented set of REST calls) that demonstrates exactly this. It is one of the most persuasive things a reviewer can see.

---

## 11. Clinician UI and oversight dashboard

- **Clinician view.** For a selected patient: the recommendation, the current regimen, the recommended action, the evidence for each assertion (each evidence item should let the viewer see the underlying resource or note span), the deterministic tool output (dose, interactions, contraindications), the AI disclosure, and one clear control to accept / edit / reject. Selecting reject or edit requires a structured reason from the taxonomy (with optional free text). Escalations render as a distinct state with the escalation reason.
- **Oversight dashboard.** Read-only, driven solely by FHIR queries against oversight-event resources: counts and rates of accept/edit/reject, distribution of reasons (with `data-vintage` broken out), escalation frequency, and a simple automation-bias-relevant view. Because it reads only via REST, it doubles as proof that the oversight events are genuine resources.
- Keep the UI honest to the workflow but do not over-invest in visual polish at the expense of the oversight instrumentation; the instrumentation is the point.

---

## 12. Standards and interoperability requirements (checklist)

- FHIR R4; US Core profiles where applicable.
- OAuth 2.0 / SMART-on-FHIR authorization, supplied via config.
- CDS Hooks-compatible recommendation surface (mapping documented; endpoint optional for the demo — see Section 5).
- Tool/function interfaces expressed as JSON-Schema function definitions consistent with emerging AI-to-API conventions (the same schema the frontier backend's tool-use mode consumes and the local backend's constrained decoder enforces).
- Recommendation and oversight events exposed as FHIR resources over standard REST, retrievable by unaffiliated clients with no bespoke code.
- Containerized, configuration-driven, documented for independent installation.
- Open-source posture: assume an Apache-2.0 release. No component may require a license fee, a proprietary dependency, or a vendor relationship to run. (The frontier-API backend is optional and swappable; the system must run fully open and local without it.)

---

## 13. The two build targets and what differs

One codebase, two configurations. Nothing structural differs; only config and data.

| Dimension | Public demo target (near-term) | Production target (eventual) |
| --- | --- | --- |
| Inference backend | `FrontierAPIBackend` (hosted frontier model over API) | `LocalModelBackend` (Qwen3-4B + LoRA, on-prem, 24 GB GPU) |
| Data | Synthetic only (Synthea on local HAPI) | Institutional data on an on-prem mirrored FHIR server; no PHI leaves premises |
| FHIR server | Local HAPI (Dockerized) | On-prem mirrored FHIR server; later a vendor production endpoint |
| Knowledge corpus | Small synthetic/generic antibiogram + formulary | Institutional antibiogram + formulary |
| Everything else | Identical | Identical |

**Coherence rule for any public-facing description.** Present the frontier-model backend as a demonstration substrate, not the intended production architecture. A single sentence keeps it consistent: demonstrated here with a hosted frontier model, designed for and deployed with a local open-weight model in resource-limited settings. The model-agnostic seam is a feature to foreground, not a limitation to explain away: it shows the oversight framework, FHIR integration, and routing are independent of any particular model.

**Deferred (do not build for the demo, but do not architecturally preclude):** LoRA fine-tuning of the local model (the demo uses the frontier backend zero/few-shot); the full large-scale evaluation harness and blinded-reference tooling; cross-platform validation across multiple FHIR servers and vendor sandboxes; a production institutional RAG corpus. Leave clean interfaces where these attach.

---

## 14. Open parameters (choose sensible defaults, make them configurable, surface them)

Do not hard-code these. Pick a defensible default, expose it in config, and note it in the README so the clinical team can set the real value.

- Qualifying broad-spectrum antibiotic classes and the exact hours-from-presentation window for candidate identification.
- Confidence threshold for routing, and the default confidence method.
- The exact renal-impairment threshold and the interaction/contraindication rule set used by the deterministic tool (seed with common narrow-spectrum agents; this is clinical configuration).
- The high-risk rule parameters (for example, what counts as "severe" renal impairment, the neutropenia cutoff).
- The disclosure text and the reason-taxonomy display labels.
- The `Device` metadata for AI-authorship provenance (model name, version, backend identifier).

---

## 15. Acceptance criteria (definition of done for the demo target)

The build is done when, on the synthetic fixtures, all of the following are demonstrable end to end:

1. The agent identifies a de-escalation candidate, retrieves the relevant FHIR resources, and assesses sufficiency.
2. It consults the knowledge corpus via RAG and calls the deterministic tool for dose and interaction/contraindication checks, with no dosing arithmetic anywhere in the model path.
3. It emits a schema-valid, fully evidence-linked recommendation; invalid model output is rejected and retried, never surfaced.
4. Routing escalates the high-risk fixture via a deterministic rule and the insufficient-information fixture via sufficiency assessment, and surfaces a confident recommendation for the clean fixture.
5. A clinician can accept, edit, or reject the surfaced recommendation and supply a structured reason, and that disposition is persisted as an OversightEvent (AuditEvent profile) plus the AI-authorship Provenance, referencing the recommendation resource.
6. An independent read-only FHIR client retrieves the recommendation and its oversight events over REST and reconstructs who decided what, when, over which AI output, and why, with no project-specific code.
7. The oversight dashboard renders override/escalation behavior sourced entirely from FHIR queries.
8. The entire system starts from containers with the backend selected by configuration, and switching from the frontier backend to a local backend is a config change with no code edit.
9. The draft implementation guide (OversightEvent, AI-authorship Provenance, GuidanceResponse profile, CodeSystem/ValueSet) builds with the IG Publisher and is browsable at a public URL, with at least one worked example per profile drawn from the demo fixtures.

Meeting criterion 8 is the proof that the near-term demo and the eventual production system are genuinely one codebase.

---

## 16. Build order (suggested, not binding)

You may sequence as you see fit, but this order front-loads the load-bearing constraints:

1. The inference-backend seam and the frontier adapter, with the recommendation JSON Schema and shared prompt.
2. The FHIR data-access layer plus a Dockerized local HAPI server.
3. Synthetic-data generation and the three curated fixtures.
4. The deterministic clinical tool.
5. The agent orchestrator wiring the loop, with RAG.
6. The routing engine (deterministic rules plus confidence).
7. The oversight layer and the FHIR profiles/CodeSystem/ValueSet, plus persistence of recommendation and oversight-event resources.
8. The independent read-only client that proves criterion 6.
9. The clinician UI and the oversight dashboard.
10. Container/config finalization and a scripted, reproducible demo path.

---

## 17. HL7 AI Challenge 2026 submission plan (time-boxed; supersedes Section 16 until submitted)

### 17.1 What the challenge requires (verified against info.hl7.org/ai-challenge and the official T&Cs, July 2026)

- **Deadline:** July 15, 2026, ~11:00 PM EDT (extended once from June 30; a page element suggests the effective cutoff may be an hour or two earlier — submit by July 14).
- **Intent to enter:** an email to `AI-challenge@HL7.org` with primary contact, team name and participants, organization and country, and a brief description of the submission concept. Send this immediately; it costs nothing and registers the entry.
- **Deliverables:** an **executive summary**, a **solution narrative**, and a **demonstration video**; technical materials optional but permitted. Entry is via the HubSpot form linked from the "Enter Challenge" button at info.hl7.org/ai-challenge.
- **Judging:** an international expert panel evaluates "originality, impact, use of HL7 standards, and fitness of the submission against the published evaluation factors." No detailed public rubric exists; the organizers' stated 2026 aims are (a) innovation grounded in open, widely adopted standards, (b) demonstrating how structured, interoperable data improves AI performance, and (c) real-world solutions that scale across organizations and borders.
- **Constraints:** no PHI or PII anywhere in the submission (we are synthetic-only — state this explicitly); participants retain all IP; HL7 gets a non-exclusive promo license to the non-technical materials; no cash prize; winners present at the HL7 40th Annual Plenary & WGM (September 2026) — the submission must survive a live walkthrough there.
- **Reference model:** Trisotech's winning 2025 submission video is public (https://www.youtube.com/watch?v=xG77c3pq2TI); match its register — concrete demo, standards vocabulary, no marketing gloss.

### 17.2 Positioning (how the narrative maps to what this panel rewards)

- **Category lane:** 2025 had a named "Excellence in AI Transparency & Trust" award, won by Trisotech for making agentic AI "explainable, governable and clinically trustworthy" via deterministic logic + HL7 integration. That is exactly this project's lane. Write the submission to lead that category while standing alone as an overall-award contender (2026 categories are not confirmed to repeat).
- **Judge alignment (use their vocabulary, verbatim where honest):** Robert Lario (2025 awardee, now judging) — "explainability, interoperability, governance, traceability"; Michel Dumontier — "open standards to deliver measurable improvements"; Mandana Ahmadi — agentic AI + EMR integration; Josh Mandel — SMART/FHIR architecture (the SMART-on-FHIR and CDS Hooks claims must be technically precise; he will check).
- **The hook, first paragraph of the executive summary:** oversight of agentic clinical AI is mandated everywhere (FDA GMLP, EU AI Act Art. 14, NIST AI RMF, AMA) and observable nowhere. We make the human oversight decision a first-class, queryable FHIR resource. The agent proposes, the clinician disposes, and the disposition is standard FHIR any client can GET.
- **Structured-data-improves-AI argument (stated aim (b)):** the evidence-linking contract — every clinical assertion must reference the FHIR resource or note span that supports it — is only possible because the input data is structured and interoperable. Frame evidence-linking not just as safety but as the demonstration that FHIR-structured data makes AI output verifiable and its failures catchable.
- **Measurable impact (Dumontier; stated aim (c)):** two layers. Clinical: day-4 de-escalation is as safe as continued broad-spectrum therapy while cutting antibiotic days and length of stay, yet under half of eligible patients are de-escalated (cite the multi-hospital evidence). Governance: the oversight dashboard produces the exact monitoring metrics regulators require but nobody can currently generate — override rate by structured reason, escalation rate, automation-bias signal.
- **Equity and scale:** the model-agnostic seam means the same system runs on a local open-weight model (Qwen3-4B class) on a single 24 GB GPU with no external calls and no license fees — deployable in resource-limited settings where frontier APIs are unaffordable or prohibited. Apache-2.0, containerized, config-not-code portability. Make this a lead theme, not a footnote.
- **Standards-maturation story:** the deliverable is not just an app; it is a draft IG (profiles + CodeSystem/ValueSet + reference implementation) explicitly complementary to the HL7 AI Transparency on FHIR IG — that IG covers AI influence on clinical data; ours covers the human decision over agentic output. This positions the entry as contributing to HL7's own standards pipeline, which no pure-application entry can claim.

### 17.3 Submission-scope build (what must exist by July 14 — the vertical slice)

Cut Section 16 to this. Everything here serves the video and the narrative; anything that doesn't is deferred.

1. **Day 1:** Dockerized HAPI FHIR server; two hand-authored fixture bundles (skip the full Synthea pipeline — curate transaction bundles by hand, version-controlled): the clean de-escalation candidate and the high-risk escalation case. (Add the insufficient-information fixture only if time allows.)
2. **Day 1–2:** the inference seam (`InferenceBackend`), the frontier adapter with structured output against the recommendation JSON Schema, and a stub `LocalModelBackend` that proves the config swap is real (it may return a canned schema-valid response labeled as such — the seam is the claim, not local inference quality).
3. **Day 2:** minimal deterministic tool (renal dose adjustment + contraindication check for the narrow agents the fixtures use — data-driven tables, not a full formulary) and a small RAG corpus (one synthetic antibiogram + a short formulary document) with citable passage IDs.
4. **Day 2–3:** orchestrator loop + routing engine (the deterministic high-risk rules for the two fixtures + confidence threshold with self-consistency as the default method).
5. **Day 3:** oversight layer end to end: GuidanceResponse persisted, AI-authorship Provenance, OversightEvent (AuditEvent profile) on accept/edit/reject with the reason taxonomy, escalation events. This is the contribution — it gets the most careful engineering and testing time.
6. **Day 3–4:** the FSH/SUSHI IG build published to GitHub Pages; the independent read-only client (a documented script of plain REST calls is acceptable — its plainness is the point); a minimal clinician UI and dashboard (functional, not polished; the dashboard reads only via FHIR REST).
7. **Day 4:** scripted demo run; record and edit the demonstration video (17.4); write the executive summary and solution narrative; final repo cleanup (README with one-command startup).
8. **Day 5 (July 14):** buffer, review, submit via the HubSpot form. Do not plan work for July 15.

Deferred without guilt: Synthea generation, CDS Hooks endpoint (document the mapping only), real local model inference, SMART auth flow beyond config-supplied bearer token (document the design), UI polish, the third fixture if behind schedule.

### 17.4 Demonstration video (structure the cut around the provable claim)

1. **The gap** (30s): oversight mandated everywhere, observable nowhere — one slide.
2. **The loop** (90s): the agent works the clean fixture live — retrieval, sufficiency, RAG citation, deterministic tool call, schema-valid evidence-linked recommendation.
3. **The routing** (45s): the high-risk fixture escalates via a deterministic rule — show that the model didn't decide this, code did.
4. **The disposition** (60s): clinician rejects with `data-vintage` reason; show disclosure, the structured reason capture.
5. **The climax** (90s): an unaffiliated client — plain `curl` against the FHIR base URL — GETs the GuidanceResponse, the Provenance (AI authorship, Device identity), and the OversightEvent, and reconstructs who decided what, when, over which AI output, and why. No project code on screen.
6. **The dashboard + IG** (45s): override/escalation metrics sourced purely from FHIR queries; a click through the published IG pages.
7. **Scale and equity** (30s): config swap to the local backend on screen; one line — demonstrated with a hosted frontier model, designed for deployment with a local open-weight model in resource-limited settings.

### 17.5 Submission checklist

- [ ] Intent email sent to AI-challenge@HL7.org (immediately)
- [ ] Watch the "Everything You Need to Know Before You Apply" webinar on the challenge page; reconcile 17.1 against it
- [ ] Vertical slice demonstrable end to end (17.3 items 1–6)
- [ ] IG published and browsable at a public URL
- [ ] Demo video recorded, ≤ 10 minutes unless the form says otherwise
- [ ] Executive summary and solution narrative drafted per 17.2, reviewed for judge-vocabulary alignment
- [ ] Explicit "synthetic data only; no PHI/PII" statement in all materials
- [ ] Submitted via HubSpot form by end of day July 14, 2026; confirmation saved
