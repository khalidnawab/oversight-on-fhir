# Oversight Event Type - Oversight-on-FHIR Implementation Guide v0.1.0

* [**Table of Contents**](toc.md)
* [**Artifacts Summary**](artifacts.md)
* **Oversight Event Type**

## CodeSystem: Oversight Event Type 

| | |
| :--- | :--- |
| *Official URL*:https://oversight-on-fhir.org/fhir/CodeSystem/oversight-event-type | *Version*:0.1.0 |
| Active as of 2026-07-11 | *Computable Name*:OversightEventType |

 
Distinguishes a human oversight decision from a system escalation. 

 This Code system is referenced in the content logical definition of the following value sets: 

* [OversightEventTypeVS](ValueSet-oversight-event-type-vs.md)



## Resource Content

```json
{
  "resourceType" : "CodeSystem",
  "id" : "oversight-event-type",
  "url" : "https://oversight-on-fhir.org/fhir/CodeSystem/oversight-event-type",
  "version" : "0.1.0",
  "name" : "OversightEventType",
  "title" : "Oversight Event Type",
  "status" : "active",
  "experimental" : false,
  "date" : "2026-07-11T15:14:01-04:00",
  "publisher" : "Oversight-on-FHIR",
  "contact" : [{
    "name" : "Oversight-on-FHIR",
    "telecom" : [{
      "system" : "url",
      "value" : "https://oversight-on-fhir.org"
    }]
  }],
  "description" : "Distinguishes a human oversight decision from a system escalation.",
  "caseSensitive" : true,
  "content" : "complete",
  "count" : 2,
  "concept" : [{
    "code" : "oversight-decision",
    "display" : "Human oversight decision over agentic AI output"
  },
  {
    "code" : "escalation",
    "display" : "Escalation of an agentic AI recommendation to a human"
  }]
}

```
