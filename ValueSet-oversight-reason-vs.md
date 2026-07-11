# Oversight Override Reason Value Set - Oversight-on-FHIR Implementation Guide v0.1.0

* [**Table of Contents**](toc.md)
* [**Artifacts Summary**](artifacts.md)
* **Oversight Override Reason Value Set**

## ValueSet: Oversight Override Reason Value Set 

| | |
| :--- | :--- |
| *Official URL*:https://oversight-on-fhir.org/fhir/ValueSet/oversight-reason-vs | *Version*:0.1.0 |
| Active as of 2026-07-11 | *Computable Name*:OversightReasonVS |

 
All structured override reasons. 

 **References** 

* [Oversight Reason Extension](StructureDefinition-oversight-reason-ext.md)

### Logical Definition (CLD)

 

### Expansion

-------

 Explanation of the columns that may appear on this page: 

| | |
| :--- | :--- |
| Level | A few code lists that FHIR defines are hierarchical - each code is assigned a level. In this scheme, some codes are under other codes, and imply that the code they are under also applies |
| System | The source of the definition of the code (when the value set draws in codes defined elsewhere) |
| Code | The code (used as the code in the resource instance) |
| Display | The display (used in the*display*element of a[Coding](http://hl7.org/fhir/R4/datatypes.html#Coding)). If there is no display, implementers should not simply display the code, but map the concept into their application |
| Definition | An explanation of the meaning of the concept |
| Comments | Additional notes about how to use the code |



## Resource Content

```json
{
  "resourceType" : "ValueSet",
  "id" : "oversight-reason-vs",
  "url" : "https://oversight-on-fhir.org/fhir/ValueSet/oversight-reason-vs",
  "version" : "0.1.0",
  "name" : "OversightReasonVS",
  "title" : "Oversight Override Reason Value Set",
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
  "description" : "All structured override reasons.",
  "compose" : {
    "include" : [{
      "system" : "https://oversight-on-fhir.org/fhir/CodeSystem/oversight-reason"
    }]
  }
}

```
