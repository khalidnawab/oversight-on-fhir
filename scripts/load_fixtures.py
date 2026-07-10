"""Load synthetic fixtures onto the configured FHIR server (Section 7)."""
import json
import sys
from pathlib import Path

from oversight.config import Settings
from oversight.fhir.client import FhirClient

FIXTURES = Path(__file__).parent.parent / "fixtures"


def main() -> int:
    settings = Settings()
    client = FhirClient.from_settings(settings)
    for name in ("clean_candidate.json", "high_risk.json", "clinicians.json"):
        bundle = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
        result = client.transaction(bundle)
        entries = result.get("entry", [])
        print(f"Loaded {name}: {len(entries)} responses")
        for e in entries:
            status = e.get("response", {}).get("status", "?")
            location = e.get("response", {}).get("location", "")
            print(f"  {status}  {location}")
    print(f"\nDone. FHIR base: {settings.fhir_base_url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
