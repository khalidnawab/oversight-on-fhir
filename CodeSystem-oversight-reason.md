# Oversight Override Reason - Oversight-on-FHIR Implementation Guide v0.1.0

* [**Table of Contents**](toc.md)
* [**Artifacts Summary**](artifacts.md)
* **Oversight Override Reason**

## CodeSystem: Oversight Override Reason 

| | |
| :--- | :--- |
| *Official URL*:https://oversight-on-fhir.org/fhir/CodeSystem/oversight-reason | *Version*:0.1.0 |
| Active as of 2026-07-11 | *Computable Name*:OversightReason |

 
Structured reasons a clinician gives when overriding (editing or rejecting) an agentic AI recommendation. 

 This Code system is referenced in the content logical definition of the following value sets: 

* [OversightReasonVS](ValueSet-oversight-reason-vs.md)



## Resource Content

```json
{
  "resourceType" : "CodeSystem",
  "id" : "oversight-reason",
  "url" : "https://oversight-on-fhir.org/fhir/CodeSystem/oversight-reason",
  "version" : "0.1.0",
  "name" : "OversightReason",
  "title" : "Oversight Override Reason",
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
  "description" : "Structured reasons a clinician gives when overriding (editing or rejecting) an agentic AI recommendation.",
  "caseSensitive" : true,
  "content" : "complete",
  "count" : 4,
  "concept" : [{
    "code" : "clinical-disagreement",
    "display" : "Clinician disagrees with the clinical judgment"
  },
  {
    "code" : "missing-information",
    "display" : "The agent lacked information the clinician has"
  },
  {
    "code" : "patient-specific-factor",
    "display" : "A patient-specific consideration the agent did not weigh"
  },
  {
    "code" : "data-vintage",
    "display" : "The clinician has newer data than the agent did"
  }]
}

```
