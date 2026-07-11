# Oversight-on-FHIR — Executive Summary

**HL7 AI Challenge 2026 · Author: Khalid Nawab · Synthetic data only — no PHI or PII**

Oversight of agentic clinical AI is mandated nearly everywhere and observable
nearly nowhere. The FDA's Good Machine Learning Practice, Article 14 of the EU AI
Act, the NIST AI Risk Management Framework, and the AMA's augmented-intelligence
principles all require that a clinician be able to understand and override what an
agentic system produces. None of them says how that oversight decision is
*captured, represented, or measured* once the system is running. The HL7 AI
Transparency on FHIR IG represents AI influence on clinical data; it does not
represent the human decision to accept, modify, or reject what an agent proposes.
That missing layer is what this project builds.

**The contribution.** Oversight-on-FHIR makes the human oversight decision a
first-class, queryable FHIR resource. An autonomous, standards-native agent performs
a real clinical task — antibiotic de-escalation in suspected sepsis — and an
instrumented oversight layer records every disposition as standard FHIR. The agent
proposes; the clinician disposes; and that disposition — accept, edit, or reject,
with a structured reason drawn from a defined ValueSet — lands in the record as a
`GuidanceResponse` (the recommendation), an AI-authorship `Provenance` (attributing
it to a `Device` with model identity and version), and an `AuditEvent` profiled as an
**OversightEvent**. Any unaffiliated FHIR client can retrieve these over plain REST
and reconstruct who decided what, when, over which AI output, and why — with no
project-specific code.

**Why structured, interoperable data is load-bearing, not incidental.** Every
clinical assertion in a recommendation must cite the specific FHIR resource or note
excerpt that supports it; an assertion with no evidence link fails schema validation
and never reaches the clinician. This evidence-linking contract is only possible
because the input is structured and interoperable FHIR — it is the concrete
demonstration that standards-based data makes AI output verifiable and its failures
catchable. All safety-critical computation (renal dose adjustment, drug-interaction
and contraindication checking) is performed by deterministic code, never by the
language model, and a set of deterministic high-risk rules force escalation to a
human regardless of model confidence.

**Measurable impact, on two layers.** Clinically, antimicrobial de-escalation is
endorsed by antibiotic-stewardship and sepsis guidelines (IDSA/SHEA 2016; Surviving
Sepsis Campaign 2021) and, across a randomized trial and large multicenter cohorts,
is not associated with increased mortality relative to continuing broad-spectrum
therapy (Leone 2014; Tabah 2016; Kam 2024) — yet it remains substantially underused:
in 236 US hospitals, only 29.5% of patients with suspected sepsis were de-escalated by
day 4, with wide variation between hospitals (Kam 2024). For governance, the oversight
layer produces the exact monitoring metrics regulators require but institutions
currently cannot generate — override rate by structured reason, escalation rate, and
an automation-bias signal — computed live from FHIR `AuditEvent` queries alone, with
no internal database, which is itself the proof that the oversight events are genuine
interoperable resources.

**Scale and equity.** A model-agnostic seam makes the reasoning backend a
configuration choice, never a code change. The same system runs against a hosted
frontier model or an on-premises open-weight model with no external calls and no
license fees — deployable in resource-limited settings where frontier APIs are
unaffordable or prohibited. The stack is containerized and portable by configuration.

**Standards maturation.** The deliverable is not only an application but a draft
Implementation Guide — FHIR profiles plus a CodeSystem/ValueSet terminology and a
reference implementation — explicitly complementary to the HL7 AI Transparency on
FHIR IG: that guide covers AI influence on clinical data, this one covers the human
decision over agentic output. The two compose. This positions the work as a
contribution to HL7's own standards pipeline, not merely an application built on top
of it.
