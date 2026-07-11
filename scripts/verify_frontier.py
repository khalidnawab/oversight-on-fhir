"""End-to-end verification of the live frontier backend: run the real orchestrator (real Claude
model) against a live FHIR patient and confirm the final recommendation is full-schema-valid."""
from oversight.config import Settings  # triggers load_dotenv()
from oversight.fhir.client import FhirClient
from oversight.inference.frontier import FrontierAPIBackend
from oversight.orchestrator.context import ContextBuilder
from oversight.orchestrator.loop import Orchestrator
from oversight.rag.retriever import Retriever
from oversight.schema.validate import validate_recommendation


def main() -> int:
    s = Settings()
    client = FhirClient.from_settings(s)
    ctx = ContextBuilder(client).build("clean-1", "enc-clean-1")
    passages = Retriever().retrieve("de-escalation MSSA cefazolin", k=2)
    orch = Orchestrator(FrontierAPIBackend(model=s.model), threshold=s.confidence_threshold, n_samples=2)
    print(f"Running live orchestrator with the real {s.model} on Patient/clean-1 ...")
    rec = orch.run_with_context(ctx, knowledge_passages=passages)
    validate_recommendation(rec)
    print("OK — full pipeline produced a schema-valid recommendation from the real model.\n")
    print(f"  action        : {rec['candidacy']['recommended_action']} -> {rec['candidacy']['recommended_agent']}")
    print(f"  routing       : {rec['routing']['decision']} (rules: {rec['routing']['triggered_high_risk_rules']})")
    print(f"  confidence    : {rec['confidence']['score']} via {rec['confidence']['method']}")
    print(f"  renal dose    : {rec['deterministic_tool_result']['renal_dose_adjustment'].get('dose')}")
    print("  rationale (model-authored, evidence-linked):")
    for r in rec["rationale"]:
        refs = ", ".join(e.get("fhir_reference") or e.get("knowledge_source_id") or "?" for e in r["evidence"])
        print(f"    - {r['assertion'][:90]}  [{refs}]")
    return 0


if __name__ == "__main__":
    main()
