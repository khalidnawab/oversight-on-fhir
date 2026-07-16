# Oversight-on-FHIR — Solution Narrative

**HL7 AI Challenge 2026 · Author: Khalid Nawab**
**Synthetic data only — no PHI or PII appears anywhere in this submission.**

**Source repository:** https://github.com/khalidnawab/oversight-on-fhir ·
**Implementation Guide:** https://khalidnawab.github.io/oversight-on-fhir/

## The problem

Agentic AI systems plan and execute multi-step clinical work with limited human
input at each step. Every major governance framework — the AMA's
augmented-intelligence principles, the NIST AI Risk Management Framework, the FDA's
Good Machine Learning Practice, and Article 14 of the EU AI Act — requires that a
clinician be able to understand and override what such a system produces. None of
them specifies how that oversight decision is captured, represented, or measured once
a system is live.

The HL7 AI Transparency on FHIR IG represents AI *influence on clinical data*. It
does not represent the human decision to accept, modify, or reject what an agentic
system proposes — the escalation, the disclosure, the override, and the structured
record of when and why overrides happen. Stated plainly: oversight of agentic
clinical AI is mandated nearly everywhere and observable nearly nowhere. Closing that
gap is the object of this project.

## What a FHIR resource is — and what this project proposes

FHIR (Fast Healthcare Interoperability Resources) is HL7's standard for exchanging
health data. It defines a catalog of standard record types called *resources* —
`Patient`, `MedicationRequest`, `Observation`, and roughly 140 others — each with a
fixed, published structure, created and retrieved over a standard REST API that
modern EHRs already expose. A FHIR resource is not a proprietary log entry: it is a
record that any conformant system can store, validate, and query without knowing
anything about the software that wrote it.

The proposal here is deliberately conservative: no new resource types. Three
existing resources are each given a job. A `GuidanceResponse` carries the AI's
recommendation. A `Provenance` attributes that recommendation to a `Device`
representing the AI, with model identity and version — the *transparency* half: the
record permanently shows what came from AI. An `AuditEvent` records the clinician's
decision over it — accept, edit, or reject, with a coded reason — the
*accountability* half. A draft Implementation Guide then profiles these resources
(constrains their shape) and defines the terminology, so that "an oversight
decision" has one precise, machine-checkable representation rather than a
per-vendor convention. Because the trail is ordinary FHIR, it is EHR-agnostic by
construction — and any vendor's clinical AI, not only this one, could emit the same
pattern.

## What this is

An autonomous, standards-native agent performs a genuine clinical reasoning task —
antibiotic de-escalation in suspected sepsis — wrapped in an instrumented oversight
layer that makes every human oversight decision a first-class, standards-based,
queryable FHIR resource. The clinical task is the vehicle. The oversight
instrumentation and its FHIR representation are the contribution.

De-escalation was chosen because it is clinically consequential, guideline-endorsed,
and underused. Antibiotic-stewardship and sepsis guidelines call for daily reassessment
and narrowing of empiric therapy (IDSA/SHEA 2016; Surviving Sepsis Campaign 2021). A
randomized trial and subsequent multicenter cohorts find de-escalation is not
associated with increased mortality compared with continuing broad-spectrum therapy
(Leone 2014; Tabah 2016; Kam 2024). Yet it remains substantially underused: across 236
US hospitals and more than 124,000 patients with suspected sepsis, only 29.5% were
de-escalated by day 4, with wide between-hospital variation (Kam 2024). It is also an
ideal agentic testbed — the workflow is genuinely multi-step, every step touches
standards-based data, and the decision is high-stakes enough that oversight behavior is
worth measuring.

The stewardship case is broader than any single trial. Higher antibiotic consumption —
especially of broad-spectrum agents — is consistently associated with higher resistance,
both across populations (pooled odds ratio ~2.3; Bell et al. 2014) and within individual
patients for months after exposure (Costelloe et al. 2010); and unnecessary broad-spectrum
use drives costly downstream harm — antimicrobial stewardship programs reduce antibiotic
expenditure (Huebner et al. 2019), while a single *Clostridioides difficile* infection, a
classic consequence of excess broad-spectrum exposure, carries roughly $24,000 in
attributable cost (Zhang et al. 2018). The CDC, WHO, and IDSA/SHEA accordingly endorse
de-escalation and shortest-effective-duration therapy to reduce selective pressure. Two
honest caveats keep the framing grounded — and are themselves part of the argument for
this system: de-escalation *in isolation* has not been shown in randomized trials to
reduce resistance emergence or total cost (a Cochrane review found no qualifying RCTs
(Silva et al. 2013); the largest ICU synthesis judged the resistance question inadequately
investigated (Tabah et al. 2016)). The resistance and cost benefits are established for
reducing unnecessary broad-spectrum exposure, of which de-escalation is the
guideline-endorsed mechanism; the individual-patient effect is exactly what remains to be
measured at scale. A system that keeps a clinician on every de-escalation decision and
emits the outcome as queryable FHIR is built to generate precisely that evidence.

The system is advisory. It never writes an order, never modifies therapy, never
discontinues a drug. The clinician's decision is the only action gate.

## How the loop works

For each eligible patient the agent executes a standards-native loop:

1. **Identify a candidate** — an adult admission with suspected infection, blood
   cultures drawn, and IV broad-spectrum antibiotics started within 48 hours.
   Eligibility triage is deterministic and renders the worklist instantly.
2. **Retrieve the chart over FHIR** — active antimicrobials and administrations
   (`MedicationRequest`, `MedicationAdministration`), cultures and susceptibilities
   (`DiagnosticReport`, `Observation`), renal function (`Observation`), and allergies
   (`AllergyIntolerance`).
3. **Judge information sufficiency** — decide whether what was retrieved is enough to
   reason about de-escalation. Unresolvable insufficiency is itself a routing outcome
   (escalate for missing information), not a guess.
4. **Ground the choice in institutional knowledge** — retrieval over a curated corpus
   (antibiogram, formulary, stewardship guidance) with citable passage identifiers.
   Retrieval over documents, not free recall.
5. **Compute all safety-critical values deterministically** — renal dose adjustment
   (Cockcroft–Gault) and interaction/contraindication checking are performed by code,
   never by the language model. This is a hard boundary.
6. **Produce a structured, evidence-linked recommendation** — schema-valid output in
   which every clinical assertion links to the specific FHIR resource or knowledge
   passage that supports it. An assertion with no evidence fails validation.
7. **Route on risk and confidence** — deterministic high-risk rules
   (`allergy_to_candidate`, `isolate_not_susceptible`, `severe_renal_impairment`,
   `neutropenia`) force escalation regardless of model confidence; low-confidence
   cases escalate as well. The model does not decide whether to escalate; code does.

## The oversight layer — the contribution

When a recommendation is produced, three FHIR resources are written:

- a **`GuidanceResponse`** (profiled as `DeescalationGuidanceResponse`) carrying the
  structured, evidence-linked recommendation;
- an **AI-authorship `Provenance`** (profiled as `AIAuthorshipProvenance`) attributing
  the recommendation to a `Device` that records model identity, version, and backend;
- when routing escalates, an **`AuditEvent`** (profiled as `OversightEvent`) recording
  the escalation and the high-risk rule that fired.

When the clinician acts — accept, edit, or reject — the disposition is captured as an
`OversightEvent`: `type` distinguishes decision from escalation, `subtype` carries the
disposition, an extension carries the structured override reason
(`clinical-disagreement`, `missing-information`, `patient-specific-factor`,
`data-vintage`), and `entity.what` references the reviewed `GuidanceResponse`. The
disclosure that AI produced the suggestion is code-owned and shown to the clinician;
the recommendation is never presented as an order.

This is the design thesis: oversight is not a compliance feature bolted onto an
agent, and not a logging afterthought. It is a core subsystem with its own data model,
its own FHIR profiles, its own terminology, and its own REST surface.

## Independent implementability — the proof

Because the oversight trail is standard FHIR, an unaffiliated read-only client can
`GET` the `GuidanceResponse`, its `Provenance`, and its `OversightEvent`(s) and
reconstruct who decided what, when, over which AI output, and why — using plain REST
and no project-specific code. The submission includes exactly such a client: a
documented sequence of REST calls whose very plainness is the point. This is what
"independent implementability" means, and it is demonstrable rather than asserted.

To make the standards surface legible in the interface itself, every page carries a
live FHIR activity panel: each resource the application reads or writes appears in a
running log as it happens, with the oversight-trail writes
(`GuidanceResponse` → `Provenance` → `AuditEvent`) highlighted and clickable through
to the raw resource as stored on the server. A viewer watches the agent consume
structured chart data and watches the oversight decision become a resource, in real
time — and can then watch an unaffiliated client retrieve the same resources.
Written, observed, independently retrieved: a complete evidentiary chain.

## Measurable impact and the governance dashboard

An oversight dashboard aggregates the accumulated events — override rate by structured
reason, escalation rate, and a `data-vintage` signal that surfaces automation bias
(the agent repeatedly acting on data the clinician has already superseded). Every
figure is computed live from FHIR `AuditEvent` queries with no internal database,
which is itself the proof that the oversight events are genuine interoperable
resources and not private logs. These are the exact monitoring metrics that
regulators require and that institutions running agentic AI currently cannot produce.

## Scale, equity, and portability

The reasoning backend sits behind a model-agnostic seam: switching between a hosted
frontier model, an on-premises open-weight model, and an offline deterministic backend
is a configuration change, never a code change. The on-premises path makes no external
calls and incurs no license fees, so the same system is deployable in resource-limited
settings where frontier APIs are unaffordable or prohibited. As a safety policy
enforced in code, the frontier backend refuses to run unless the deployment is marked
synthetic-data-only — real patient data and the external API are mutually exclusive by
construction. The stack is containerized and portable by configuration.

## Relationship to HL7 standards

The deliverable includes a draft Implementation Guide — the three profiles above, an
override-reason CodeSystem/ValueSet, a disposition CodeSystem/ValueSet, and event-type
and high-risk-rule CodeSystems — with conformant examples and a reference
implementation. It is explicitly complementary to the HL7 AI Transparency on FHIR IG:
that guide covers AI influence on clinical data; this one covers the human decision
over agentic output. AI authorship is attributed with `Provenance` to a `Device`,
mirroring that guide's approach, while the novel object here is the `OversightEvent`
profile on `AuditEvent`. The work is therefore a contribution to HL7's standards
pipeline, not merely an application built on top of it.

## What a reviewer should take away

The agent proposes, the clinician disposes, and that disposition lands in the record
as standard FHIR any client can retrieve. Explainability, interoperability,
governance, and traceability are not features described in a slide — they are
resources on a server, retrievable over REST, and measurable in aggregate. That is
what makes agentic clinical AI governable, and it is built on open standards so it can
scale across organizations and borders.

---

*Standards surface: FHIR R4 · profiles on GuidanceResponse, Provenance, and
AuditEvent · SMART-on-FHIR bearer authorization (configuration-supplied) · CDS Hooks
service · draft Implementation Guide. All data in this submission is synthetic; no PHI
or PII is present.*

## References

1. Leone M, Bechis C, Baumstarck K, et al. De-escalation versus continuation of
   empirical antimicrobial treatment in severe sepsis: a multicenter non-blinded
   randomized noninferiority trial. *Intensive Care Med.* 2014;40(10):1399–1408.
   PMID 25091790.
2. Tabah A, Cotta MO, Garnacho-Montero J, et al. A systematic review of the
   definitions, determinants, and clinical outcomes of antimicrobial de-escalation in
   the intensive care unit. *Clin Infect Dis.* 2016;62(8):1009–1017. PMID 26703860.
3. Kam KQ, Chen T, Kadri SS, et al. Epidemiology and outcomes of antibiotic
   de-escalation in patients with suspected sepsis in US hospitals. *Clin Infect Dis.*
   2024;80(1):108–117. PMID 39657050.
4. Evans L, Rhodes A, Alhazzani W, et al. Surviving Sepsis Campaign: international
   guidelines for management of sepsis and septic shock 2021. *Intensive Care Med.*
   2021;47(11):1181–1247. PMID 34599691.
5. Barlam TF, Cosgrove SE, Abbo LM, et al. Implementing an antibiotic stewardship
   program: guidelines by the Infectious Diseases Society of America and the Society
   for Healthcare Epidemiology of America. *Clin Infect Dis.* 2016;62(10):e51–e77.
   PMID 27080992.
6. Bell BG, Schellevis F, Stobberingh E, Goossens H, Pringle M. A systematic review and
   meta-analysis of the effects of antibiotic consumption on antibiotic resistance.
   *BMC Infect Dis.* 2014;14:13. PMID 24405683.
7. Costelloe C, Metcalfe C, Lovering A, Mant D, Hay AD. Effect of antibiotic prescribing
   in primary care on antimicrobial resistance in individual patients: systematic review
   and meta-analysis. *BMJ.* 2010;340:c2096. PMID 20483949.
8. Silva BNG, Andriolo RB, Atallah ÁN, Salomão R. De-escalation of antimicrobial
   treatment for adults with sepsis, severe sepsis or septic shock. *Cochrane Database
   Syst Rev.* 2013;(3):CD007934. PMID 23543557.
9. Huebner C, Flessa S, Huebner N-O. The economic impact of antimicrobial stewardship
   programmes in hospitals: a systematic literature review. *J Hosp Infect.*
   2019;102(4):369–376. PMID 30880265.
10. Zhang D, Prabhu VS, Marcella SW. Attributable healthcare resource utilization and
    costs for patients with primary and recurrent *Clostridium difficile* infection in
    the United States. *Clin Infect Dis.* 2018;66(9):1326–1332. PMID 29301031.
