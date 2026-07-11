// ---------------------------------------------------------------------------
// CodeSystems and ValueSets for the oversight override-reason taxonomy (Section 10.2)
// ---------------------------------------------------------------------------

CodeSystem: OversightReason
Id: oversight-reason
Title: "Oversight Override Reason"
Description: "Structured reasons a clinician gives when overriding (editing or rejecting) an agentic AI recommendation."
* ^status = #active
* ^experimental = false
* ^caseSensitive = true
* ^content = #complete
* #clinical-disagreement "Clinician disagrees with the clinical judgment"
* #missing-information "The agent lacked information the clinician has"
* #patient-specific-factor "A patient-specific consideration the agent did not weigh"
* #data-vintage "The clinician has newer data than the agent did"

ValueSet: OversightReasonVS
Id: oversight-reason-vs
Title: "Oversight Override Reason Value Set"
Description: "All structured override reasons."
* ^status = #active
* ^experimental = false
* include codes from system OversightReason

CodeSystem: OversightDisposition
Id: oversight-disposition
Title: "Oversight Disposition"
Description: "The clinician's disposition of an agentic AI recommendation."
* ^status = #active
* ^experimental = false
* ^caseSensitive = true
* ^content = #complete
* #accept "Accept"
* #edit "Edit"
* #reject "Reject"

ValueSet: OversightDispositionVS
Id: oversight-disposition-vs
Title: "Oversight Disposition Value Set"
Description: "All dispositions."
* ^status = #active
* ^experimental = false
* include codes from system OversightDisposition

CodeSystem: OversightEventType
Id: oversight-event-type
Title: "Oversight Event Type"
Description: "Distinguishes a human oversight decision from a system escalation."
* ^status = #active
* ^experimental = false
* ^caseSensitive = true
* ^content = #complete
* #oversight-decision "Human oversight decision over agentic AI output"
* #escalation "Escalation of an agentic AI recommendation to a human"

ValueSet: OversightEventTypeVS
Id: oversight-event-type-vs
Title: "Oversight Event Type Value Set"
Description: "All oversight event types."
* ^status = #active
* ^experimental = false
* include codes from system OversightEventType

CodeSystem: HighRiskRule
Id: high-risk-rule
Title: "High-Risk Routing Rule"
Description: "Deterministic high-risk rules that force escalation regardless of model confidence (Section 9.1)."
* ^status = #active
* ^experimental = false
* ^caseSensitive = true
* ^content = #complete
* #allergy_to_candidate "Documented allergy to the candidate narrower agent"
* #isolate_not_susceptible "Isolate not susceptible to the proposed narrower agent"
* #severe_renal_impairment "Severe renal impairment altering dosing"
* #neutropenia "Neutropenia or other immunocompromise"
