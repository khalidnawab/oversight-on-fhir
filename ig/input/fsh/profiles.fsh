Alias: $event-type = https://oversight-on-fhir.org/fhir/CodeSystem/oversight-event-type
Alias: $provenance-participant-type = http://terminology.hl7.org/CodeSystem/provenance-participant-type

// ---------------------------------------------------------------------------
// OversightEvent — the novel object: a human oversight decision as a profiled
// AuditEvent (Section 10.3). Also carries system escalation events.
// ---------------------------------------------------------------------------
Profile: OversightEvent
Parent: AuditEvent
Id: oversight-event
Title: "Oversight Event"
Description: "A human oversight decision (accept/edit/reject) — or a system escalation — over an agentic AI recommendation. type distinguishes decision vs escalation; subtype carries the disposition; the reason extension carries the structured override reason; entity.what references the reviewed recommendation (a GuidanceResponse)."
* extension contains OversightReasonExt named reason 0..1
* type from OversightEventTypeVS (required)
* recorded 1..1
* agent 1..*
* agent.who 1..1
* entity 1..*
* entity.what 1..1

// ---------------------------------------------------------------------------
// AI-authorship Provenance — attributes a recommendation to the AI Device,
// machine-generated (Section 10.3). Complements the HL7 AI Transparency IG.
// ---------------------------------------------------------------------------
Profile: AIAuthorshipProvenance
Parent: Provenance
Id: ai-authorship-provenance
Title: "AI Authorship Provenance"
Description: "Attributes authorship of an AI-generated recommendation to a Device representing the AI system (model identity, version, backend)."
* target 1..*
* recorded 1..1
* agent 1..*
* agent.who 1..1
* agent.who only Reference(Device)

// ---------------------------------------------------------------------------
// De-escalation recommendation carrier — a profiled GuidanceResponse
// (Section 10.3). Performer is the AI Device.
// ---------------------------------------------------------------------------
Profile: DeescalationGuidanceResponse
Parent: GuidanceResponse
Id: deescalation-guidance-response
Title: "De-escalation Guidance Response"
Description: "The output of the agentic de-escalation decision-support process, carrying the structured, evidence-linked recommendation and attributed to the AI Device that produced it."
* status 1..1
* subject 1..1
* performer 1..1
* performer only Reference(Device)
