# Example Patient (synthetic) - Oversight-on-FHIR Implementation Guide v0.1.0

* [**Table of Contents**](toc.md)
* [**Artifacts Summary**](artifacts.md)
* **Example Patient (synthetic)**

## Example Patient: Example Patient (synthetic)

Security Label: [test health data (Details: ActReason code HTEST = 'test health data')](http://terminology.hl7.org/7.2.0/CodeSystem-v3-ActReason.html)

Pat Example Unknown, DoB Unknown

-------



## Resource Content

```json
{
  "resourceType" : "Patient",
  "id" : "clean-1",
  "meta" : {
    "security" : [{
      "system" : "http://terminology.hl7.org/CodeSystem/v3-ActReason",
      "code" : "HTEST",
      "display" : "test health data"
    }]
  },
  "name" : [{
    "family" : "Example",
    "given" : ["Pat"]
  }],
  "gender" : "unknown"
}

```
