# High-Risk Routing Rule - Oversight-on-FHIR Implementation Guide v0.1.0

* [**Table of Contents**](toc.md)
* [**Artifacts Summary**](artifacts.md)
* **High-Risk Routing Rule**

## CodeSystem: High-Risk Routing Rule 

| | |
| :--- | :--- |
| *Official URL*:https://oversight-on-fhir.org/fhir/CodeSystem/high-risk-rule | *Version*:0.1.0 |
| Active as of 2026-07-11 | *Computable Name*:HighRiskRule |

 
Deterministic high-risk rules that force escalation regardless of model confidence (Section 9.1). 

 This Code system is referenced in the content logical definition of the following value sets: 

* This CodeSystem is not used here; it may be used elsewhere (e.g. specifications and/or implementations that use this content)



## Resource Content

```json
{
  "resourceType" : "CodeSystem",
  "id" : "high-risk-rule",
  "url" : "https://oversight-on-fhir.org/fhir/CodeSystem/high-risk-rule",
  "version" : "0.1.0",
  "name" : "HighRiskRule",
  "title" : "High-Risk Routing Rule",
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
  "description" : "Deterministic high-risk rules that force escalation regardless of model confidence (Section 9.1).",
  "caseSensitive" : true,
  "content" : "complete",
  "count" : 4,
  "concept" : [{
    "code" : "allergy_to_candidate",
    "display" : "Documented allergy to the candidate narrower agent"
  },
  {
    "code" : "isolate_not_susceptible",
    "display" : "Isolate not susceptible to the proposed narrower agent"
  },
  {
    "code" : "severe_renal_impairment",
    "display" : "Severe renal impairment altering dosing"
  },
  {
    "code" : "neutropenia",
    "display" : "Neutropenia or other immunocompromise"
  }]
}

```
