# De-escalation Guidance Response - Oversight-on-FHIR Implementation Guide v0.1.0

* [**Table of Contents**](toc.md)
* [**Artifacts Summary**](artifacts.md)
* **De-escalation Guidance Response**

## Resource Profile: De-escalation Guidance Response 

| | |
| :--- | :--- |
| *Official URL*:https://oversight-on-fhir.org/fhir/StructureDefinition/deescalation-guidance-response | *Version*:0.1.0 |
| Draft as of 2026-07-11 | *Computable Name*:DeescalationGuidanceResponse |

 
The output of the agentic de-escalation decision-support process, carrying the structured, evidence-linked recommendation and attributed to the AI Device that produced it. 

**Usages:**

* Examples for this Profile: [GuidanceResponse/gr-example](GuidanceResponse-gr-example.md)

You can also check for [usages in the FHIR IG Statistics](https://packages2.fhir.org/xig/resource/oversight-on-fhir|current/StructureDefinition/StructureDefinition-deescalation-guidance-response.json)

### Formal Views of Profile Content

 [Description of Profiles, Differentials, Snapshots and how the different presentations work](http://build.fhir.org/ig/FHIR/ig-guidance/readingIgs.html#structure-definitions). 

 

Other representations of profile: [CSV](StructureDefinition-deescalation-guidance-response.csv), [Excel](StructureDefinition-deescalation-guidance-response.xlsx), [Schematron](StructureDefinition-deescalation-guidance-response.sch) 



## Resource Content

```json
{
  "resourceType" : "StructureDefinition",
  "id" : "deescalation-guidance-response",
  "url" : "https://oversight-on-fhir.org/fhir/StructureDefinition/deescalation-guidance-response",
  "version" : "0.1.0",
  "name" : "DeescalationGuidanceResponse",
  "title" : "De-escalation Guidance Response",
  "status" : "draft",
  "date" : "2026-07-11T15:14:01-04:00",
  "publisher" : "Oversight-on-FHIR",
  "contact" : [{
    "name" : "Oversight-on-FHIR",
    "telecom" : [{
      "system" : "url",
      "value" : "https://oversight-on-fhir.org"
    }]
  }],
  "description" : "The output of the agentic de-escalation decision-support process, carrying the structured, evidence-linked recommendation and attributed to the AI Device that produced it.",
  "fhirVersion" : "4.0.1",
  "mapping" : [{
    "identity" : "workflow",
    "uri" : "http://hl7.org/fhir/workflow",
    "name" : "Workflow Pattern"
  },
  {
    "identity" : "w5",
    "uri" : "http://hl7.org/fhir/fivews",
    "name" : "FiveWs Pattern Mapping"
  },
  {
    "identity" : "rim",
    "uri" : "http://hl7.org/v3",
    "name" : "RIM Mapping"
  }],
  "kind" : "resource",
  "abstract" : false,
  "type" : "GuidanceResponse",
  "baseDefinition" : "http://hl7.org/fhir/StructureDefinition/GuidanceResponse",
  "derivation" : "constraint",
  "differential" : {
    "element" : [{
      "id" : "GuidanceResponse",
      "path" : "GuidanceResponse"
    },
    {
      "id" : "GuidanceResponse.subject",
      "path" : "GuidanceResponse.subject",
      "min" : 1
    },
    {
      "id" : "GuidanceResponse.performer",
      "path" : "GuidanceResponse.performer",
      "min" : 1
    }]
  }
}

```
