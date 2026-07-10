# CDS Hooks surface

The recommendation is exposed as a CDS Hooks service so an EHR can surface it in-workflow — the
standard EHR-integration path that completes the standards-native story (FHIR + SMART + CDS Hooks,
Section 5 / Section 12).

## Discovery

`GET /cds-services` returns:

```json
{"services": [{"hook": "patient-view", "id": "deescalation-oversight",
  "title": "Antibiotic de-escalation oversight",
  "description": "Surfaces an agentic de-escalation recommendation with AI disclosure and an accept/edit/reject oversight control."}]}
```

## Invocation

`POST /cds-services/deescalation-oversight` with a CDS Hooks request whose `context` carries
`patientId` (and optionally `encounterId`). The service runs the agent loop, persists the
recommendation (GuidanceResponse + AI-authorship Provenance), and returns a card.

## Recommendation → card mapping

| Recommendation state | Card `indicator` | Card content |
| --- | --- | --- |
| `routing.decision == surface`, action `narrow` | `info` | Summary "Consider de-escalation to \<agent\>", rationale in `detail`, a **suggestion** carrying the accept semantics (its `uuid` is the GuidanceResponse reference) |
| `routing.decision == escalate` | `warning` | Escalation summary; triggered high-risk rules in `detail`; **no suggestion** (a human must decide) |
| otherwise | `info` | "Insufficient information" |

Every card's `detail` ends with the AI disclosure text.

## Disposition → oversight capture

Selecting the card's suggestion (accept) or overriding it maps to the same oversight-capture path
used by the clinician UI: it produces an **OversightEvent** (`AuditEvent` profile) referencing the
GuidanceResponse, with the disposition coded and — for edit/reject — a structured reason from the
override-reason ValueSet. The card's `suggestions[].uuid` is the GuidanceResponse reference, so the
EHR's `suggestion` acceptance can be tied back to the exact AI output that was reviewed.

## Status

The discovery document and card mapping are implemented and tested (`tests/test_cds_hooks.py`,
`tests/test_app.py`). Wiring an EHR's `suggestion`-accepted callback directly into
`OversightService.capture_disposition` is the remaining production step; the demo captures
dispositions through the clinician UI over the same service.
