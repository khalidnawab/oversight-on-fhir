# Oversight Reason Extension - Oversight-on-FHIR Implementation Guide v0.1.0

* [**Table of Contents**](toc.md)
* [**Artifacts Summary**](artifacts.md)
* **Oversight Reason Extension**

## Extension: Oversight Reason Extension 

| | |
| :--- | :--- |
| *Official URL*:https://oversight-on-fhir.org/fhir/StructureDefinition/oversight-reason-ext | *Version*:0.1.0 |
| Draft as of 2026-07-11 | *Computable Name*:OversightReasonExt |

Carries the structured override reason on an OversightEvent, coded against the oversight-reason value set.

**Context of Use**

**Usage info**

**Usages:**

* Use this Extension: [Oversight Event](StructureDefinition-oversight-event.md)
* Examples for this Extension: [AuditEvent/oversight-reject-example](AuditEvent-oversight-reject-example.md)

You can also check for [usages in the FHIR IG Statistics](https://packages2.fhir.org/xig/resource/oversight-on-fhir|current/StructureDefinition/StructureDefinition-oversight-reason-ext.json)

### Formal Views of Extension Content

 [Description of Profiles, Differentials, Snapshots, and how the XML and JSON presentations work](http://build.fhir.org/ig/FHIR/ig-guidance/readingIgs.html#structure-definitions). 

 

Other representations of profile: [CSV](StructureDefinition-oversight-reason-ext.csv), [Excel](StructureDefinition-oversight-reason-ext.xlsx), [Schematron](StructureDefinition-oversight-reason-ext.sch) 

#### Terminology Bindings

#### Constraints



## Resource Content

```json
{
  "resourceType" : "StructureDefinition",
  "id" : "oversight-reason-ext",
  "url" : "https://oversight-on-fhir.org/fhir/StructureDefinition/oversight-reason-ext",
  "version" : "0.1.0",
  "name" : "OversightReasonExt",
  "title" : "Oversight Reason Extension",
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
  "description" : "Carries the structured override reason on an OversightEvent, coded against the oversight-reason value set.",
  "fhirVersion" : "4.0.1",
  "mapping" : [{
    "identity" : "rim",
    "uri" : "http://hl7.org/v3",
    "name" : "RIM Mapping"
  }],
  "kind" : "complex-type",
  "abstract" : false,
  "context" : [{
    "type" : "element",
    "expression" : "AuditEvent"
  }],
  "type" : "Extension",
  "baseDefinition" : "http://hl7.org/fhir/StructureDefinition/Extension",
  "derivation" : "constraint",
  "differential" : {
    "element" : [{
      "id" : "Extension.extension",
      "path" : "Extension.extension",
      "max" : "0"
    },
    {
      "id" : "Extension.url",
      "path" : "Extension.url",
      "fixedUri" : "https://oversight-on-fhir.org/fhir/StructureDefinition/oversight-reason-ext"
    },
    {
      "id" : "Extension.value[x]",
      "path" : "Extension.value[x]",
      "type" : [{
        "code" : "CodeableConcept"
      }],
      "binding" : {
        "strength" : "required",
        "valueSet" : "https://oversight-on-fhir.org/fhir/ValueSet/oversight-reason-vs"
      }
    }]
  }
}

```
