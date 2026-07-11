"""End-to-end verification of the live frontier backend: run the real orchestrator (real Claude
model) against a live FHIR patient and confirm the final recommendation is full-schema-valid."""
from oversight.config import Settings  # triggers load_dotenv()
from oversight.fhir.client import FhirClient
from oversight.inference.frontier import FrontierAPIBackend
from oversight.orchestrator.context import ContextBuilder
from oversight.orchestrator.loop import Orchestrator
from oversight.rag.retriever import Retriever
from oversight.schema.validate import validate_recommendation


import sys


def review(patient_id: str, encounter_id: str) -> None:
    s = Settings()
    client = FhirClient.from_settings(s)
    ctx = ContextBuilder(client).build(patient_id, encounter_id)
    passages = Retriever().retrieve("de-escalation stop duration IV to PO culture negative", k=3)
    orch = Orchestrator(FrontierAPIBackend(model=s.model), threshold=s.confidence_threshold, n_samples=2)
    print(f"\n=== {patient_id} — live {s.model} ===")
    rec = orch.run_with_context(ctx, knowledge_passages=passages)
    validate_recommendation(rec)
    print(f"  action     : {rec['candidacy']['recommended_action']} -> {rec['candidacy']['recommended_agent']}")
    print(f"  routing    : {rec['routing']['decision']} (rules: {rec['routing']['triggered_high_risk_rules']})")
    print(f"  assessment : {rec['stewardship_assessment']}")
    print("  evidence   :")
    for r in rec["rationale"]:
        refs = ", ".join(e.get("fhir_reference") or e.get("knowledge_source_id") or "?" for e in r["evidence"])
        print(f"    - {r['assertion'][:78]}  [{refs}]")


def main() -> int:
    review("clean-1", "enc-clean-1")   # MSSA -> narrow to cefazolin
    review("u-anand", "enc-u-anand")   # culture-negative -> stop / reassess / insufficient
    return 0


if __name__ == "__main__":
    main()
