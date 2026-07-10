from oversight.config import Settings
from oversight.fhir.client import FhirClient
from oversight.orchestrator.census import CensusScanner

for e in CensusScanner(FhirClient.from_settings(Settings())).scan():
    reg = e.regimen[0]["name"][:22] if e.regimen else "-"
    print(f"{e.eligibility:12} | Day {e.day_of_therapy:>2} | {e.patient_name:18} | {e.location:16} | {reg:22} | {e.culture_status}")
