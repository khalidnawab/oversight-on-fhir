Extension: OversightReasonExt
Id: oversight-reason-ext
Title: "Oversight Reason Extension"
Description: "Carries the structured override reason on an OversightEvent, coded against the oversight-reason value set."
* ^context[0].type = #element
* ^context[0].expression = "AuditEvent"
* value[x] only CodeableConcept
* valueCodeableConcept from OversightReasonVS (required)
