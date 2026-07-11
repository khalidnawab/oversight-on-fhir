# Oversight Event - Oversight-on-FHIR Implementation Guide v0.1.0

* [**Table of Contents**](toc.md)
* [**Artifacts Summary**](artifacts.md)
* **Oversight Event**

## Resource Profile: Oversight Event 

| | |
| :--- | :--- |
| *Official URL*:https://oversight-on-fhir.org/fhir/StructureDefinition/oversight-event | *Version*:0.1.0 |
| Draft as of 2026-07-11 | *Computable Name*:OversightEvent |

 
A human oversight decision (accept/edit/reject) — or a system escalation — over an agentic AI recommendation. type distinguishes decision vs escalation; subtype carries the disposition; the reason extension carries the structured override reason; entity.what references the reviewed recommendation (a GuidanceResponse). 

**Usages:**

* Examples for this Profile: [AuditEvent/escalation-example](AuditEvent-escalation-example.md) and [AuditEvent/oversight-reject-example](AuditEvent-oversight-reject-example.md)

You can also check for [usages in the FHIR IG Statistics](https://packages2.fhir.org/xig/resource/oversight-on-fhir|current/StructureDefinition/StructureDefinition-oversight-event.json)

### Formal Views of Profile Content

 [Description of Profiles, Differentials, Snapshots and how the different presentations work](http://build.fhir.org/ig/FHIR/ig-guidance/readingIgs.html#structure-definitions). 

 

Other representations of profile: [CSV](StructureDefinition-oversight-event.csv), [Excel](StructureDefinition-oversight-event.xlsx), [Schematron](StructureDefinition-oversight-event.sch) 



## Resource Content

```json
{
  "resourceType" : "StructureDefinition",
  "id" : "oversight-event",
  "url" : "https://oversight-on-fhir.org/fhir/StructureDefinition/oversight-event",
  "version" : "0.1.0",
  "name" : "OversightEvent",
  "title" : "Oversight Event",
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
  "description" : "A human oversight decision (accept/edit/reject) — or a system escalation — over an agentic AI recommendation. type distinguishes decision vs escalation; subtype carries the disposition; the reason extension carries the structured override reason; entity.what references the reviewed recommendation (a GuidanceResponse).",
  "fhirVersion" : "4.0.1",
  "mapping" : [{
    "identity" : "workflow",
    "uri" : "http://hl7.org/fhir/workflow",
    "name" : "Workflow Pattern"
  },
  {
    "identity" : "rim",
    "uri" : "http://hl7.org/v3",
    "name" : "RIM Mapping"
  },
  {
    "identity" : "dicom",
    "uri" : "http://nema.org/dicom",
    "name" : "DICOM Tag Mapping"
  },
  {
    "identity" : "w5",
    "uri" : "http://hl7.org/fhir/fivews",
    "name" : "FiveWs Pattern Mapping"
  },
  {
    "identity" : "w3c.prov",
    "uri" : "http://www.w3.org/ns/prov",
    "name" : "W3C PROV"
  },
  {
    "identity" : "fhirprovenance",
    "uri" : "http://hl7.org/fhir/provenance",
    "name" : "FHIR Provenance Mapping"
  }],
  "kind" : "resource",
  "abstract" : false,
  "type" : "AuditEvent",
  "baseDefinition" : "http://hl7.org/fhir/StructureDefinition/AuditEvent",
  "derivation" : "constraint",
  "differential" : {
    "element" : [{
      "id" : "AuditEvent",
      "path" : "AuditEvent"
    },
    {
      "id" : "AuditEvent.extension",
      "path" : "AuditEvent.extension",
      "slicing" : {
        "discriminator" : [{
          "type" : "value",
          "path" : "url"
        }],
        "ordered" : false,
        "rules" : "open"
      }
    },
    {
      "id" : "AuditEvent.extension:reason",
      "path" : "AuditEvent.extension",
      "sliceName" : "reason",
      "min" : 0,
      "max" : "1",
      "type" : [{
        "code" : "Extension",
        "profile" : ["https://oversight-on-fhir.org/fhir/StructureDefinition/oversight-reason-ext"]
      }]
    },
    {
      "id" : "AuditEvent.type",
      "path" : "AuditEvent.type",
      "binding" : {
        "strength" : "required",
        "valueSet" : "https://oversight-on-fhir.org/fhir/ValueSet/oversight-event-type-vs"
      }
    },
    {
      "id" : "AuditEvent.agent.who",
      "path" : "AuditEvent.agent.who",
      "min" : 1
    },
    {
      "id" : "AuditEvent.entity",
      "path" : "AuditEvent.entity",
      "min" : 1
    },
    {
      "id" : "AuditEvent.entity.what",
      "path" : "AuditEvent.entity.what",
      "min" : 1
    }]
  }
}

```
