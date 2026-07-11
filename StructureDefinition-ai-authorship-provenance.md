# AI Authorship Provenance - Oversight-on-FHIR Implementation Guide v0.1.0

* [**Table of Contents**](toc.md)
* [**Artifacts Summary**](artifacts.md)
* **AI Authorship Provenance**

## Resource Profile: AI Authorship Provenance 

| | |
| :--- | :--- |
| *Official URL*:https://oversight-on-fhir.org/fhir/StructureDefinition/ai-authorship-provenance | *Version*:0.1.0 |
| Draft as of 2026-07-11 | *Computable Name*:AIAuthorshipProvenance |

 
Attributes authorship of an AI-generated recommendation to a Device representing the AI system (model identity, version, backend). 

**Usages:**

* Examples for this Profile: [Provenance/prov-example](Provenance-prov-example.md)

You can also check for [usages in the FHIR IG Statistics](https://packages2.fhir.org/xig/resource/oversight-on-fhir|current/StructureDefinition/StructureDefinition-ai-authorship-provenance.json)

### Formal Views of Profile Content

 [Description of Profiles, Differentials, Snapshots and how the different presentations work](http://build.fhir.org/ig/FHIR/ig-guidance/readingIgs.html#structure-definitions). 

 

Other representations of profile: [CSV](StructureDefinition-ai-authorship-provenance.csv), [Excel](StructureDefinition-ai-authorship-provenance.xlsx), [Schematron](StructureDefinition-ai-authorship-provenance.sch) 



## Resource Content

```json
{
  "resourceType" : "StructureDefinition",
  "id" : "ai-authorship-provenance",
  "url" : "https://oversight-on-fhir.org/fhir/StructureDefinition/ai-authorship-provenance",
  "version" : "0.1.0",
  "name" : "AIAuthorshipProvenance",
  "title" : "AI Authorship Provenance",
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
  "description" : "Attributes authorship of an AI-generated recommendation to a Device representing the AI system (model identity, version, backend).",
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
    "identity" : "w3c.prov",
    "uri" : "http://www.w3.org/ns/prov",
    "name" : "W3C PROV"
  },
  {
    "identity" : "w5",
    "uri" : "http://hl7.org/fhir/fivews",
    "name" : "FiveWs Pattern Mapping"
  },
  {
    "identity" : "fhirauditevent",
    "uri" : "http://hl7.org/fhir/auditevent",
    "name" : "FHIR AuditEvent Mapping"
  }],
  "kind" : "resource",
  "abstract" : false,
  "type" : "Provenance",
  "baseDefinition" : "http://hl7.org/fhir/StructureDefinition/Provenance",
  "derivation" : "constraint",
  "differential" : {
    "element" : [{
      "id" : "Provenance",
      "path" : "Provenance"
    },
    {
      "id" : "Provenance.agent.who",
      "path" : "Provenance.agent.who",
      "type" : [{
        "code" : "Reference",
        "targetProfile" : ["http://hl7.org/fhir/StructureDefinition/Device"]
      }]
    }]
  }
}

```
