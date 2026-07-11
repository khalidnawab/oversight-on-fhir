import time

from oversight.config import Settings
from oversight.inference.frontier import FrontierAPIBackend
from oversight.schema.validate import load_model_schema

PROMPT = ("Patient/x Encounter/y on MedicationRequest/m1 piperacillin-tazobactam; DiagnosticReport/d1 "
          "grew MSSA susceptible to cefazolin. Recommend a stewardship action as schema-valid JSON.")

for label, kwargs in [("opus medium", {}),
                      ("opus low", {"effort": "low"}),
                      ("sonnet-4-6 low", {"model": "claude-sonnet-4-6", "effort": "low"})]:
    b = FrontierAPIBackend(**kwargs)
    t = time.time()
    try:
        r = b.generate(PROMPT, load_model_schema(), n_samples=1)
        print(f"{label:16} {time.time()-t:5.1f}s  action={r.recommendation['candidacy']['recommended_action']}")
    except Exception as e:
        print(f"{label:16} FAILED after {time.time()-t:.1f}s: {type(e).__name__}: {str(e)[:80]}")
