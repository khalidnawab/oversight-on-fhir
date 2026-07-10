"""Census scan + eligibility identification (Section 3.1). Deterministic, no LLM: the agent
queries the whole unit over FHIR and flags patients eligible for de-escalation review."""
import datetime as _dt
from dataclasses import dataclass, field

# Broad-spectrum empiric agents whose therapy is a de-escalation candidate (Section 14 — configurable).
DEFAULT_BROAD_SPECTRUM = ["piperacillin", "cefepime", "meropenem", "imipenem", "ceftazidime"]

ELIGIBILITY_ORDER = {"eligible": 0, "insufficient": 1, "monitoring": 2, "not_eligible": 3}


@dataclass
class CensusEntry:
    patient_id: str
    patient_name: str
    encounter_id: str
    location: str
    day_of_therapy: int
    dot_hours: float
    regimen: list = field(default_factory=list)      # [{name, reference, broad_spectrum}]
    culture_status: str = "none"                     # resulted | pending | none
    eligibility: str = "not_eligible"                # eligible | insufficient | monitoring | not_eligible
    reason: str = ""
    organism: str | None = None


def _parse_iso(s: str) -> _dt.datetime | None:
    try:
        return _dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, TypeError, AttributeError):
        return None


def _display(resource: dict) -> str:
    codings = resource.get("code", {}).get("coding", [])
    return (codings[0].get("display", "") if codings else "") or resource.get("code", {}).get("text", "")


class CensusScanner:
    def __init__(self, fhir, broad_spectrum: list[str] | None = None, deescalation_hours: float = 72):
        self._fhir = fhir
        self._broad = [b.lower() for b in (broad_spectrum or DEFAULT_BROAD_SPECTRUM)]
        self._window = deescalation_hours

    def _is_broad(self, med_name: str) -> bool:
        low = med_name.lower()
        return any(tok in low for tok in self._broad)

    def classify(self, patient_id: str, now: _dt.datetime | None = None) -> CensusEntry | None:
        now = now or _dt.datetime.now(_dt.timezone.utc)
        return self._classify(self._fhir.read("Patient", patient_id), now)

    def scan(self, now: _dt.datetime | None = None) -> list[CensusEntry]:
        now = now or _dt.datetime.now(_dt.timezone.utc)
        entries = []
        for p in self._fhir.search("Patient", {}):
            entry = self._classify(p, now)
            if entry:
                entries.append(entry)
        entries.sort(key=lambda e: (ELIGIBILITY_ORDER.get(e.eligibility, 9), -e.dot_hours))
        return entries

    def _classify(self, patient: dict, now: _dt.datetime) -> CensusEntry | None:
        pid = patient["id"]
        names = patient.get("name", [{}])
        given = " ".join(names[0].get("given", [])) if names else ""
        name = f"{given} {names[0].get('family', '')}".strip() if names else pid

        encounters = self._fhir.search("Encounter", {"patient": f"Patient/{pid}"})
        active_enc = next((e for e in encounters if e.get("status") == "in-progress"), None)
        if active_enc is None:
            return None
        loc = ""
        if active_enc.get("location"):
            loc = active_enc["location"][0].get("location", {}).get("display", "")

        regimen, broad_authored = [], []
        for mr in self._fhir.search("MedicationRequest", {"patient": f"Patient/{pid}"}):
            if mr.get("status") not in (None, "active", "on-hold"):
                continue
            med = mr.get("medicationCodeableConcept", {}).get("text") or _display(mr) or "unknown"
            is_broad = self._is_broad(med)
            regimen.append({"name": med, "reference": f"MedicationRequest/{mr['id']}", "broad_spectrum": is_broad})
            if is_broad:
                authored = _parse_iso(mr.get("authoredOn", ""))
                if authored:
                    broad_authored.append(authored)
        if not regimen:
            return None  # not on antibiotics — off the de-escalation census

        susceptibilities = [o for o in self._fhir.search("Observation", {"patient": f"Patient/{pid}"})
                            if "[susceptibility]" in _display(o).lower()]
        micro = [d for d in self._fhir.search("DiagnosticReport", {"patient": f"Patient/{pid}"}) if d.get("conclusion")]
        organism = micro[0]["conclusion"][:90] if micro else None
        culture_status = "resulted" if susceptibilities else ("pending" if micro else "none")

        entry = CensusEntry(patient_id=pid, patient_name=name, encounter_id=active_enc["id"], location=loc,
                            day_of_therapy=0, dot_hours=0.0, regimen=regimen,
                            culture_status=culture_status, organism=organism)

        if not broad_authored:
            entry.eligibility = "not_eligible"
            entry.reason = "On narrow-spectrum therapy — already de-escalated."
            return entry

        earliest = min(broad_authored)
        entry.dot_hours = (now - earliest).total_seconds() / 3600
        entry.day_of_therapy = int(entry.dot_hours // 24) + 1

        if entry.dot_hours < self._window:
            entry.eligibility = "monitoring"
            entry.reason = f"Day {entry.day_of_therapy} of broad-spectrum therapy — de-escalation review at {int(self._window)}h."
        elif culture_status == "resulted":
            entry.eligibility = "eligible"
            entry.reason = "Broad-spectrum ≥ review window and culture/susceptibilities resulted — ready for de-escalation review."
        else:
            entry.eligibility = "insufficient"
            entry.reason = "Broad-spectrum ≥ review window but no susceptibilities available — insufficient information to narrow."
        return entry
