# Synthetic fixtures

Version-controlled FHIR R4 transaction bundles. No PHI — all data synthetic (Section 7 / 4.9).

- **clean_candidate.json** — Patient/clean-1. Suspected sepsis on piperacillin-tazobactam; blood culture grows MSSA susceptible to cefazolin; normal renal function. Expected: a confident, evidence-linked recommendation to narrow to cefazolin.
- **high_risk.json** — Patient/hr-1. Same de-escalation arc, but a documented **severe cefazolin allergy**. Expected: the routing engine forces escalation via high-risk rule 1 (Section 9.1), regardless of model confidence.

A third fixture (insufficient information — missing susceptibilities) is planned; add if time allows.

Load with: `uv run python scripts/load_fixtures.py`
