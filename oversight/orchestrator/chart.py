"""Builds a display-oriented view of the patient's current chart from FHIR, for the clinician
review tabs (orders / labs / cultures). Reads only through the FhirClient interface."""
from dataclasses import dataclass, field

# LOINC -> (label, default unit, flag function) for the labs we surface.
_LAB_LOINC = {
    "2160-0": ("Creatinine", "mg/dL", lambda v: "high" if v > 1.3 else None),
    "6690-2": ("WBC", "10^3/uL", lambda v: "high" if v > 11 else ("low" if v < 4 else None)),
    "751-8": ("Neutrophils (ANC)", "10^3/uL", lambda v: "low" if v < 0.5 else None),
    "26499-4": ("Neutrophils (ANC)", "10^3/uL", lambda v: "low" if v < 0.5 else None),
    "2524-7": ("Lactate", "mmol/L", lambda v: "high" if v > 2 else None),
    "29463-7": ("Body weight", "kg", None),
    "8310-5": ("Temperature", "Cel", lambda v: "high" if v >= 38 else None),
    "8867-4": ("Heart rate", "/min", lambda v: "high" if v > 100 else None),
}
_ANTIBIOTICS = ["cefazolin", "ceftriaxone", "cefepime", "piperacillin", "tazobactam",
                "meropenem", "vancomycin", "imipenem", "ceftazidime"]


@dataclass
class ChartView:
    orders: list = field(default_factory=list)
    administrations: list = field(default_factory=list)
    labs: list = field(default_factory=list)
    cultures: list = field(default_factory=list)
    allergies: list = field(default_factory=list)


def _loinc(resource: dict) -> set[str]:
    return {c.get("code") for c in resource.get("code", {}).get("coding", [])
            if "loinc" in c.get("system", "")}


def _display(resource: dict) -> str:
    cs = resource.get("code", {}).get("coding", [])
    return (cs[0].get("display", "") if cs else "") or resource.get("code", {}).get("text", "")


def _short(ts: str, length: int = 16) -> str:
    return (ts or "")[:length].replace("T", " ")


def build_chart(fhir, patient_id: str) -> ChartView:
    cv = ChartView()
    pref = f"Patient/{patient_id}"

    for mr in fhir.search("MedicationRequest", {"patient": pref}):
        name = mr.get("medicationCodeableConcept", {}).get("text") or _display(mr) or "medication"
        cv.orders.append({"name": name, "status": mr.get("status", "?"),
                          "authored": _short(mr.get("authoredOn", ""), 10),
                          "antibiotic": any(a in name.lower() for a in _ANTIBIOTICS),
                          "ref": f"MedicationRequest/{mr['id']}"})
    for ma in fhir.search("MedicationAdministration", {"patient": pref}):
        name = ma.get("medicationCodeableConcept", {}).get("text") or "medication"
        cv.administrations.append({"name": name, "when": _short(ma.get("effectiveDateTime", ""))})
    cv.administrations.sort(key=lambda a: a["when"], reverse=True)

    susceptibilities = []
    for obs in fhir.search("Observation", {"patient": pref}):
        disp = _display(obs)
        if "[susceptibility]" in disp.lower():
            agent = disp.lower().split("[")[0].strip()
            interp = obs.get("valueCodeableConcept", {}).get("text", "?")
            susceptibilities.append({"agent": agent, "interpretation": interp})
            continue
        vq = obs.get("valueQuantity")
        code = next(iter(_loinc(obs) & set(_LAB_LOINC)), None)
        if vq and code:
            label, unit, flag_fn = _LAB_LOINC[code]
            val = vq.get("value")
            flag = flag_fn(val) if (flag_fn and val is not None) else None
            cv.labs.append({"name": label, "value": val, "unit": vq.get("unit") or unit,
                            "when": _short(obs.get("effectiveDateTime", "")), "flag": flag,
                            "ref": f"Observation/{obs['id']}"})
    cv.labs.sort(key=lambda x: x["name"])

    for dr in fhir.search("DiagnosticReport", {"patient": pref}):
        cv.cultures.append({"name": _display(dr) or "Culture", "status": dr.get("status", "?"),
                            "conclusion": dr.get("conclusion", ""),
                            "when": _short(dr.get("issued") or dr.get("effectiveDateTime", ""), 10),
                            "ref": f"DiagnosticReport/{dr['id']}", "susceptibilities": susceptibilities})

    for al in fhir.search("AllergyIntolerance", {"patient": pref}):
        reactions = al.get("reaction", [])
        manifestation = ""
        if reactions and reactions[0].get("manifestation"):
            manifestation = reactions[0]["manifestation"][0].get("text", "")
        cv.allergies.append({"substance": al.get("code", {}).get("text", "?"),
                             "criticality": al.get("criticality", ""), "reaction": manifestation})
    return cv
