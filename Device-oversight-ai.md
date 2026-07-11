# Oversight-on-FHIR AI Device - Oversight-on-FHIR Implementation Guide v0.1.0

* [**Table of Contents**](toc.md)
* [**Artifacts Summary**](artifacts.md)
* **Oversight-on-FHIR AI Device**

## Example Device: Oversight-on-FHIR AI Device

**status**: Active

### DeviceNames

| | | |
| :--- | :--- | :--- |
| - | **Name** | **Type** |
| * | Oversight-on-FHIR agent (claude-opus-4-8) | Model name |

### Versions

| | |
| :--- | :--- |
| - | **Value** |
| * | 0.1.0 |



## Resource Content

```json
{
  "resourceType" : "Device",
  "id" : "oversight-ai",
  "status" : "active",
  "deviceName" : [{
    "name" : "Oversight-on-FHIR agent (claude-opus-4-8)",
    "type" : "model-name"
  }],
  "version" : [{
    "value" : "0.1.0"
  }]
}

```
