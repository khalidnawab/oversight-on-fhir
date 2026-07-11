# Artifacts Summary - Oversight-on-FHIR Implementation Guide v0.1.0

* [**Table of Contents**](toc.md)
* **Artifacts Summary**

## Artifacts Summary

This page provides a list of the FHIR artifacts defined as part of this implementation guide.

### Structures: Resource Profiles 

These define constraints on FHIR resources for systems conforming to this implementation guide.

| | |
| :--- | :--- |
| [AI Authorship Provenance](StructureDefinition-ai-authorship-provenance.md) | Attributes authorship of an AI-generated recommendation to a Device representing the AI system (model identity, version, backend). |
| [De-escalation Guidance Response](StructureDefinition-deescalation-guidance-response.md) | The output of the agentic de-escalation decision-support process, carrying the structured, evidence-linked recommendation and attributed to the AI Device that produced it. |
| [Oversight Event](StructureDefinition-oversight-event.md) | A human oversight decision (accept/edit/reject) — or a system escalation — over an agentic AI recommendation. type distinguishes decision vs escalation; subtype carries the disposition; the reason extension carries the structured override reason; entity.what references the reviewed recommendation (a GuidanceResponse). |

### Structures: Extension Definitions 

These define constraints on FHIR data types for systems conforming to this implementation guide.

| | |
| :--- | :--- |
| [Oversight Reason Extension](StructureDefinition-oversight-reason-ext.md) | Carries the structured override reason on an OversightEvent, coded against the oversight-reason value set. |

### Terminology: Value Sets 

These define sets of codes used by systems conforming to this implementation guide.

| | |
| :--- | :--- |
| [Oversight Disposition Value Set](ValueSet-oversight-disposition-vs.md) | All dispositions. |
| [Oversight Event Type Value Set](ValueSet-oversight-event-type-vs.md) | All oversight event types. |
| [Oversight Override Reason Value Set](ValueSet-oversight-reason-vs.md) | All structured override reasons. |

### Terminology: Code Systems 

These define new code systems used by systems conforming to this implementation guide.

| | |
| :--- | :--- |
| [High-Risk Routing Rule](CodeSystem-high-risk-rule.md) | Deterministic high-risk rules that force escalation regardless of model confidence (Section 9.1). |
| [Oversight Disposition](CodeSystem-oversight-disposition.md) | The clinician's disposition of an agentic AI recommendation. |
| [Oversight Event Type](CodeSystem-oversight-event-type.md) | Distinguishes a human oversight decision from a system escalation. |
| [Oversight Override Reason](CodeSystem-oversight-reason.md) | Structured reasons a clinician gives when overriding (editing or rejecting) an agentic AI recommendation. |

### Example: Example Instances 

These are example instances that show what data produced and consumed by systems conforming with this implementation guide might look like.

| |
| :--- |
| [Example AI Authorship Provenance](Provenance-prov-example.md) |
| [Example De-escalation Guidance Response](GuidanceResponse-gr-example.md) |
| [Example Oversight Event — Escalation (allergy_to_candidate)](AuditEvent-escalation-example.md) |
| [Example Oversight Event — Reject (data-vintage)](AuditEvent-oversight-reject-example.md) |
| [Example Patient (synthetic)](Patient-clean-1.md) |
| [Example Practitioner (synthetic)](Practitioner-dr-alice.md) |
| [Oversight-on-FHIR AI Device](Device-oversight-ai.md) |

