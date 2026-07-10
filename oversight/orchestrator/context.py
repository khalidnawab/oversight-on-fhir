import datetime as _dt
from dataclasses import dataclass, field

_LOINC_CREATININE = "2160-0"
_LOINC_WEIGHT = "29463-7"
_LOINC_ANC = {"751-8", "26499-4"}  # absolute neutrophils


@dataclass
class ClinicalContext:
    patient_reference: str
    encounter_reference: str
    age: int | None = None
    weight_kg: float | None = None
    serum_creatinine: float | None = None
    is_female: bool | None = None
    current_regimen: list[dict] = field(default_factory=list)
    allergies: list[str] = field(default_factory=list)
    susceptibilities: list[dict] = field(default_factory=list)
    culture_conclusions: list[dict] = field(default_factory=list)
    anc: float | None = None

    def patient_dict(self) -> dict:
        d = {}
        if self.age is not None:
            d["age"] = self.age
        if self.weight_kg is not None:
            d["weight_kg"] = self.weight_kg
        if self.serum_creatinine is not None:
            d["serum_creatinine"] = self.serum_creatinine
        if self.is_female is not None:
            d["is_female"] = self.is_female
        return d


def _age_from_birthdate(birth: str) -> int | None:
    try:
        by = _dt.date.fromisoformat(birth)
    except (ValueError, TypeError):
        return None
    today = _dt.date.today()
    return today.year - by.year - ((today.month, today.day) < (by.month, by.day))


def _loinc_codes(resource: dict) -> set[str]:
    return {c.get("code") for c in resource.get("code", {}).get("coding", [])
            if c.get("system", "").endswith("loinc.org")}


def _display(resource: dict) -> str:
    codings = resource.get("code", {}).get("coding", [])
    return (codings[0].get("display", "") if codings else "") or resource.get("code", {}).get("text", "")


class ContextBuilder:
    """Builds a ClinicalContext by reading FHIR resources through the FhirClient interface (Section 3.2).
    Contains no FHIR wire details — only the injected client speaks HTTP."""

    def __init__(self, fhir):
        self._fhir = fhir

    def build(self, patient_id: str, encounter_id: str) -> ClinicalContext:
        patient = self._fhir.read("Patient", patient_id)
        ctx = ClinicalContext(
            patient_reference=f"Patient/{patient_id}",
            encounter_reference=f"Encounter/{encounter_id}",
            age=_age_from_birthdate(patient.get("birthDate", "")),
            is_female=(patient.get("gender") == "female"),
        )
        for mr in self._fhir.search("MedicationRequest", {"patient": f"Patient/{patient_id}"}):
            if mr.get("status") in (None, "active", "on-hold"):
                med = mr.get("medicationCodeableConcept", {}).get("text") or "unknown"
                ctx.current_regimen.append({"medication": med, "fhir_reference": f"MedicationRequest/{mr['id']}"})
        for al in self._fhir.search("AllergyIntolerance", {"patient": f"Patient/{patient_id}"}):
            text = (al.get("code", {}).get("text") or "").strip().lower()
            if text:
                ctx.allergies.append(text)
        for obs in self._fhir.search("Observation", {"patient": f"Patient/{patient_id}"}):
            codes = _loinc_codes(obs)
            val = obs.get("valueQuantity", {}).get("value")
            if _LOINC_CREATININE in codes and val is not None:
                ctx.serum_creatinine = float(val)
            elif _LOINC_WEIGHT in codes and val is not None:
                ctx.weight_kg = float(val)
            elif codes & _LOINC_ANC and val is not None:
                ctx.anc = float(val)
            elif "[susceptibility]" in _display(obs).lower():
                agent = _display(obs).lower().split("[")[0].strip()
                interp = obs.get("valueCodeableConcept", {}).get("text", "unknown")
                ctx.susceptibilities.append({"agent": agent, "interpretation": interp,
                                             "fhir_reference": f"Observation/{obs['id']}"})
        for dr in self._fhir.search("DiagnosticReport", {"patient": f"Patient/{patient_id}"}):
            if dr.get("conclusion"):
                ctx.culture_conclusions.append({"text": dr["conclusion"],
                                                "fhir_reference": f"DiagnosticReport/{dr['id']}"})
        return ctx
