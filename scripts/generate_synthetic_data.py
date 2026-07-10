"""Generate a believable synthetic inpatient unit and load it into the FHIR server.

Produces, for each patient, the full set of resources a real chart would expose over FHIR:
Patient, Encounter (with ward/bed location), Condition, MedicationRequest(s),
MedicationAdministration(s), Observations (renal, weight, WBC, ANC, lactate, vitals),
DiagnosticReport (blood culture) + susceptibility Observations, AllergyIntolerance,
DocumentReference clinical notes (H&P + progress note, base64 Binary content), and
ServiceRequest orders.

Timing is relative to "now" so day-of-therapy and eligibility are stable whenever run.
Synthetic data only — no PHI (Section 7 / 4.9).
"""
import base64
import datetime as _dt
import sys

from oversight.config import Settings
from oversight.fhir.client import FhirClient

NOW = _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0)


def _iso(dt: _dt.datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def _hours_ago(h: float) -> str:
    return _iso(NOW - _dt.timedelta(hours=h))


def _put(bundle_entries, resource):
    bundle_entries.append({
        "fullUrl": f"urn:uuid:{resource['resourceType']}-{resource['id']}",
        "resource": resource,
        "request": {"method": "PUT", "url": f"{resource['resourceType']}/{resource['id']}"},
    })


# --- resource builders -------------------------------------------------------

def patient(pid, family, given, gender, birth):
    return {"resourceType": "Patient", "id": pid, "name": [{"family": family, "given": [given]}],
            "gender": gender, "birthDate": birth}


def encounter(pid, ward, bed, started_h):
    return {"resourceType": "Encounter", "id": f"enc-{pid}", "status": "in-progress",
            "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "IMP", "display": "inpatient encounter"},
            "subject": {"reference": f"Patient/{pid}"},
            "location": [{"location": {"display": f"{ward} · Bed {bed}"}, "status": "active"}],
            "period": {"start": _hours_ago(started_h)}}


def condition(pid, text, snomed="91302008"):
    return {"resourceType": "Condition", "id": f"cond-{pid}",
            "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]},
            "verificationStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-ver-status", "code": "provisional"}]},
            "code": {"coding": [{"system": "http://snomed.info/sct", "code": snomed, "display": text}], "text": text},
            "subject": {"reference": f"Patient/{pid}"}, "encounter": {"reference": f"Encounter/enc-{pid}"}}


def med_request(pid, idx, name, rxnorm, hours_ago):
    return {"resourceType": "MedicationRequest", "id": f"mr-{pid}-{idx}", "status": "active", "intent": "order",
            "medicationCodeableConcept": {"coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": rxnorm, "display": name}], "text": name},
            "subject": {"reference": f"Patient/{pid}"}, "encounter": {"reference": f"Encounter/enc-{pid}"},
            "authoredOn": _hours_ago(hours_ago)}


def med_admin(pid, idx, admin_idx, name, rxnorm, hours_ago):
    return {"resourceType": "MedicationAdministration", "id": f"ma-{pid}-{idx}-{admin_idx}", "status": "completed",
            "medicationCodeableConcept": {"coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": rxnorm, "display": name}], "text": name},
            "subject": {"reference": f"Patient/{pid}"}, "context": {"reference": f"Encounter/enc-{pid}"},
            "effectiveDateTime": _hours_ago(hours_ago), "request": {"reference": f"MedicationRequest/mr-{pid}-{idx}"}}


def obs_quantity(pid, key, loinc, display, value, unit, hours_ago=6, category="laboratory"):
    return {"resourceType": "Observation", "id": f"obs-{pid}-{key}", "status": "final",
            "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": category}]}],
            "code": {"coding": [{"system": "http://loinc.org", "code": loinc, "display": display}]},
            "subject": {"reference": f"Patient/{pid}"}, "effectiveDateTime": _hours_ago(hours_ago),
            "valueQuantity": {"value": value, "unit": unit, "system": "http://unitsofmeasure.org", "code": unit}}


def obs_suscept(pid, agent, interp, hours_ago=8):
    return {"resourceType": "Observation", "id": f"obs-{pid}-susc-{agent}", "status": "final",
            "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "laboratory"}]}],
            "code": {"coding": [{"system": "http://loinc.org", "code": "18864-9", "display": f"{agent.title()} [Susceptibility]"}], "text": f"{agent} susceptibility"},
            "subject": {"reference": f"Patient/{pid}"}, "effectiveDateTime": _hours_ago(hours_ago),
            "valueCodeableConcept": {"text": interp}}


def diag_report(pid, conclusion, status="final", hours_ago=10):
    return {"resourceType": "DiagnosticReport", "id": f"dr-{pid}", "status": status,
            "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0074", "code": "MB", "display": "Microbiology"}]}],
            "code": {"coding": [{"system": "http://loinc.org", "code": "600-7", "display": "Bacteria identified in Blood by Culture"}]},
            "subject": {"reference": f"Patient/{pid}"}, "effectiveDateTime": _hours_ago(hours_ago + 60),
            "issued": _hours_ago(hours_ago), "conclusion": conclusion}


def allergy(pid, substance, rxnorm):
    return {"resourceType": "AllergyIntolerance", "id": f"allergy-{pid}",
            "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical", "code": "active"}]},
            "type": "allergy", "category": ["medication"], "criticality": "high",
            "code": {"coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": rxnorm, "display": substance}], "text": substance},
            "patient": {"reference": f"Patient/{pid}"},
            "reaction": [{"manifestation": [{"text": "anaphylaxis"}], "severity": "severe"}]}


def doc_ref(pid, key, loinc, title, text, hours_ago=12):
    data = base64.b64encode(text.encode("utf-8")).decode("ascii")
    return {"resourceType": "DocumentReference", "id": f"doc-{pid}-{key}", "status": "current",
            "type": {"coding": [{"system": "http://loinc.org", "code": loinc, "display": title}], "text": title},
            "subject": {"reference": f"Patient/{pid}"}, "date": _hours_ago(hours_ago),
            "content": [{"attachment": {"contentType": "text/plain", "data": data, "title": title}}],
            "context": {"encounter": [{"reference": f"Encounter/enc-{pid}"}]}}


def service_request(pid, key, text, hours_ago, status="completed"):
    return {"resourceType": "ServiceRequest", "id": f"sr-{pid}-{key}", "status": status, "intent": "order",
            "code": {"text": text}, "subject": {"reference": f"Patient/{pid}"},
            "encounter": {"reference": f"Encounter/enc-{pid}"}, "authoredOn": _hours_ago(hours_ago)}


# --- the unit ---------------------------------------------------------------

def _vitals(pid, temp, hr, wbc):
    return [
        obs_quantity(pid, "temp", "8310-5", "Body temperature", temp, "Cel", hours_ago=4, category="vital-signs"),
        obs_quantity(pid, "hr", "8867-4", "Heart rate", hr, "/min", hours_ago=4, category="vital-signs"),
        obs_quantity(pid, "wbc", "6690-2", "Leukocytes", wbc, "10*3/uL", hours_ago=6),
    ]


def build_patient(spec) -> list:
    pid = spec["id"]
    entries = []
    _put(entries, patient(pid, spec["family"], spec["given"], spec["gender"], spec["birth"]))
    _put(entries, encounter(pid, spec["ward"], spec["bed"], spec["adm_h"]))
    _put(entries, condition(pid, spec["infection"]))

    for idx, m in enumerate(spec["regimen"], 1):
        _put(entries, med_request(pid, idx, m["name"], m["rxnorm"], m["hours_ago"]))
        for a in range(min(3, int(m["hours_ago"] // 8))):
            _put(entries, med_admin(pid, idx, a, m["name"], m["rxnorm"], m["hours_ago"] - a * 8))

    _put(entries, obs_quantity(pid, "creat", "2160-0", "Creatinine", spec["creatinine"], "mg/dL"))
    _put(entries, obs_quantity(pid, "wt", "29463-7", "Body weight", spec["weight"], "kg", category="vital-signs"))
    if spec.get("anc") is not None:
        _put(entries, obs_quantity(pid, "anc", "751-8", "Neutrophils absolute", spec["anc"], "10*3/uL"))
    if spec.get("lactate") is not None:
        _put(entries, obs_quantity(pid, "lactate", "2524-7", "Lactate", spec["lactate"], "mmol/L"))
    for o in _vitals(pid, spec.get("temp", 37.8), spec.get("hr", 92), spec.get("wbc", 13.5)):
        entries.append({"fullUrl": f"urn:uuid:{o['resourceType']}-{o['id']}", "resource": o,
                        "request": {"method": "PUT", "url": f"{o['resourceType']}/{o['id']}"}})

    cul = spec["culture"]
    _put(entries, diag_report(pid, cul["conclusion"], status=cul.get("status", "final")))
    for agent, interp in cul.get("susceptibilities", {}).items():
        _put(entries, obs_suscept(pid, agent, interp))

    if spec.get("allergy"):
        _put(entries, allergy(pid, spec["allergy"]["substance"], spec["allergy"]["rxnorm"]))

    for key, (loinc, title, text) in spec.get("notes", {}).items():
        _put(entries, doc_ref(pid, key, loinc, title, text))

    _put(entries, service_request(pid, "cx", "Blood culture x2", spec["adm_h"]))
    _put(entries, service_request(pid, "cbc", "CBC with differential", 6))

    return entries


UNIT = [
    {"id": "u-webb", "family": "Webb", "given": "Marcus", "gender": "male", "birth": "1965-02-14",
     "ward": "Ward 5B", "bed": "12", "adm_h": 96, "infection": "Suspected sepsis, urinary source",
     "regimen": [{"name": "piperacillin-tazobactam", "rxnorm": "1659149", "hours_ago": 90}],
     "creatinine": 1.0, "weight": 82, "lactate": 1.8, "temp": 38.1, "hr": 96, "wbc": 14.2,
     "culture": {"conclusion": "Escherichia coli in blood culture x2. Susceptible to ceftriaxone, ciprofloxacin.",
                 "susceptibilities": {"ceftriaxone": "Susceptible"}},
     "notes": {"hp": ("34117-2", "History & Physical", "67M admitted from ED with fever and dysuria. Blood and urine cultures obtained. Started on empiric piperacillin-tazobactam for suspected urosepsis. Hemodynamically stable, no pressors."),
               "prog": ("11506-3", "Progress Note", "Day 4. Afebrile x24h. Blood cultures now positive for E. coli, ceftriaxone-susceptible. Candidate for de-escalation. Renal function normal.")}},

    {"id": "u-anand", "family": "Anand", "given": "Priya", "gender": "female", "birth": "1979-11-03",
     "ward": "Ward 5B", "bed": "14", "adm_h": 100, "infection": "Suspected sepsis, source unclear",
     "regimen": [{"name": "piperacillin-tazobactam", "rxnorm": "1659149", "hours_ago": 96}],
     "creatinine": 0.8, "weight": 61, "lactate": 2.1, "temp": 38.4, "hr": 104, "wbc": 16.8,
     "culture": {"conclusion": "Blood cultures pending — no growth to date at 96 hours. Susceptibilities not yet available.", "status": "preliminary", "susceptibilities": {}},
     "notes": {"hp": ("34117-2", "History & Physical", "47F with fever, tachycardia, no clear source. Empiric broad-spectrum started. Cultures drawn on admission."),
               "prog": ("11506-3", "Progress Note", "Day 4. Cultures without growth so far, no organism identified. Insufficient information to narrow therapy. Consider ID consult.")}},

    {"id": "u-becker", "family": "Becker", "given": "Tom", "gender": "male", "birth": "1958-06-22",
     "ward": "Ward 6A", "bed": "3", "adm_h": 22, "infection": "Community-acquired pneumonia, suspected sepsis",
     "regimen": [{"name": "piperacillin-tazobactam", "rxnorm": "1659149", "hours_ago": 20}],
     "creatinine": 1.1, "weight": 78, "lactate": 2.6, "temp": 38.9, "hr": 110, "wbc": 18.1,
     "culture": {"conclusion": "Blood cultures drawn 20h ago; no growth to date.", "status": "registered", "susceptibilities": {}},
     "notes": {"hp": ("34117-2", "History & Physical", "68M admitted overnight with pneumonia and sepsis physiology. Empiric piperacillin-tazobactam started ~20h ago. Too early for de-escalation review.")}},

    {"id": "u-marchetti", "family": "Marchetti", "given": "Sofia", "gender": "female", "birth": "1972-09-30",
     "ward": "Ward 6A", "bed": "7", "adm_h": 120, "infection": "MSSA bacteremia (de-escalated)",
     "regimen": [{"name": "cefazolin", "rxnorm": "2180", "hours_ago": 40}],
     "creatinine": 0.9, "weight": 70, "lactate": 1.2, "temp": 37.1, "hr": 78, "wbc": 8.9,
     "culture": {"conclusion": "MSSA, already narrowed to cefazolin on day 3. Clinically improving.",
                 "susceptibilities": {"cefazolin": "Susceptible"}},
     "notes": {"prog": ("11506-3", "Progress Note", "Day 5. Already de-escalated to cefazolin. Afebrile, improving. No further de-escalation indicated.")}},

    {"id": "u-okon", "family": "Okon", "given": "Grace", "gender": "female", "birth": "1985-04-18",
     "ward": "Ward 7 Onc", "bed": "2", "adm_h": 84, "infection": "Neutropenic fever, MSSA bacteremia",
     "regimen": [{"name": "cefepime", "rxnorm": "1665060", "hours_ago": 80}],
     "creatinine": 0.7, "weight": 58, "anc": 0.3, "lactate": 1.9, "temp": 38.7, "hr": 108, "wbc": 0.8,
     "culture": {"conclusion": "MSSA in blood culture. Susceptible to cefazolin. Patient is neutropenic (ANC 0.3).",
                 "susceptibilities": {"cefazolin": "Susceptible"}},
     "notes": {"hp": ("34117-2", "History & Physical", "41F with AML, neutropenic fever. MSSA bacteremia. On cefepime for febrile neutropenia. Narrowing is high-risk while neutropenic."),
               "prog": ("11506-3", "Progress Note", "Day 4. ANC 0.3. Although MSSA is cefazolin-susceptible, de-escalation should be escalated to ID given profound neutropenia.")}},

    {"id": "u-cole", "family": "Cole", "given": "Henry", "gender": "male", "birth": "1949-12-11",
     "ward": "Ward 5B", "bed": "9", "adm_h": 88, "infection": "MSSA bacteremia, AKI",
     "regimen": [{"name": "piperacillin-tazobactam", "rxnorm": "1659149", "hours_ago": 84}],
     "creatinine": 4.2, "weight": 74, "lactate": 2.0, "temp": 38.0, "hr": 90, "wbc": 12.4,
     "culture": {"conclusion": "MSSA in blood culture, susceptible to cefazolin. Acute kidney injury (creatinine 4.2).",
                 "susceptibilities": {"cefazolin": "Susceptible"}},
     "notes": {"hp": ("34117-2", "History & Physical", "76M with MSSA bacteremia and AKI (creatinine 4.2, baseline 1.0). Cefazolin appropriate by susceptibility but dosing/eligibility affected by severe renal impairment."),
               "prog": ("11506-3", "Progress Note", "Day 4. Severe renal impairment. De-escalation to cefazolin reasonable but should be escalated given renal dosing implications.")}},

    {"id": "u-park", "family": "Park", "given": "Linda", "gender": "female", "birth": "1968-07-25",
     "ward": "Ward 7 Onc", "bed": "5", "adm_h": 100, "infection": "Pseudomonas bacteremia",
     "regimen": [{"name": "cefepime", "rxnorm": "1665060", "hours_ago": 96}],
     "creatinine": 1.2, "weight": 66, "lactate": 1.7, "temp": 38.2, "hr": 98, "wbc": 15.0,
     "culture": {"conclusion": "Pseudomonas aeruginosa in blood culture. Antipseudomonal therapy should be continued; no narrowing target.",
                 "susceptibilities": {"cefepime": "Susceptible"}},
     "notes": {"prog": ("11506-3", "Progress Note", "Day 4. Pseudomonas bacteremia on cefepime. Per antibiogram, do not narrow antipseudomonal coverage. Continue current therapy.")}},
]


def main() -> int:
    settings = Settings()
    client = FhirClient.from_settings(settings)
    total = 0
    for spec in UNIT:
        bundle = {"resourceType": "Bundle", "type": "transaction", "entry": build_patient(spec)}
        result = client.transaction(bundle)
        n = len(result.get("entry", []))
        total += n
        print(f"  {spec['given']} {spec['family']:12} ({spec['ward']} bed {spec['bed']}): {n} resources")
    print(f"\nLoaded {len(UNIT)} patients, {total} resources onto {settings.fhir_base_url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
