### Oversight-on-FHIR

Oversight of agentic clinical AI is **mandated nearly everywhere** (FDA GMLP, EU AI Act Article 14, NIST AI RMF, AMA augmented-intelligence principles) and **observable nearly nowhere**. This draft implementation guide makes the human oversight decision over agentic AI output a first-class, queryable FHIR resource.

The agent proposes; the clinician disposes; and that disposition — accept, edit, or reject, with a structured reason — lands in the record as standard FHIR that any unaffiliated client can retrieve over REST.

The guide defines no new resource types. It profiles three existing FHIR resources — `GuidanceResponse` (the recommendation), `Provenance` (AI authorship), and `AuditEvent` (the human decision) — so the full oversight trail is storable and queryable on any stock FHIR R4 server.

#### Relationship to the HL7 AI Transparency on FHIR IG

This guide is **complementary** to the HL7 AI Transparency on FHIR IG. That effort represents **AI influence on clinical data**. This guide represents the **human decision over agentic AI output**. The two compose: AI authorship is attributed with `Provenance` to a `Device`, mirroring the AI Transparency approach, while the novel contribution here is the **OversightEvent** — a profile on `AuditEvent`.

#### Artifacts

- **OversightEvent** (profile on `AuditEvent`) — the human oversight decision (or a system escalation) over a recommendation.
- **AIAuthorshipProvenance** (profile on `Provenance`) — attributes a recommendation to the AI `Device`.
- **DeescalationGuidanceResponse** (profile on `GuidanceResponse`) — the recommendation carrier.
- **Terminology** — the override-reason CodeSystem/ValueSet, the disposition CodeSystem/ValueSet, the event-type and high-risk-rule CodeSystems.

An independent read-only client can `GET` the `GuidanceResponse`, its `Provenance`, and its `AuditEvent`(s) and reconstruct **who decided what, when, over which AI output, and why** — with no project-specific code.
