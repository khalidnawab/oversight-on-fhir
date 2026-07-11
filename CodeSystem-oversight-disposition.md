# Oversight Disposition - Oversight-on-FHIR Implementation Guide v0.1.0

* [**Table of Contents**](toc.md)
* [**Artifacts Summary**](artifacts.md)
* **Oversight Disposition**

## CodeSystem: Oversight Disposition 

| | |
| :--- | :--- |
| *Official URL*:https://oversight-on-fhir.org/fhir/CodeSystem/oversight-disposition | *Version*:0.1.0 |
| Active as of 2026-07-11 | *Computable Name*:OversightDisposition |

 
The clinician's disposition of an agentic AI recommendation. 

 This Code system is referenced in the content logical definition of the following value sets: 

* [OversightDispositionVS](ValueSet-oversight-disposition-vs.md)



## Resource Content

```json
{
  "resourceType" : "CodeSystem",
  "id" : "oversight-disposition",
  "url" : "https://oversight-on-fhir.org/fhir/CodeSystem/oversight-disposition",
  "version" : "0.1.0",
  "name" : "OversightDisposition",
  "title" : "Oversight Disposition",
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
  "description" : "The clinician's disposition of an agentic AI recommendation.",
  "caseSensitive" : true,
  "content" : "complete",
  "count" : 3,
  "concept" : [{
    "code" : "accept",
    "display" : "Accept"
  },
  {
    "code" : "edit",
    "display" : "Edit"
  },
  {
    "code" : "reject",
    "display" : "Reject"
  }]
}

```
