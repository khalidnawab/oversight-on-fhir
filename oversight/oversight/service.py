import datetime as _dt
import uuid

from oversight.oversight import resources as R


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class OversightService:
    """Owns disclosure/escalation and the capture of accept/edit/reject as FHIR resources (Section 10)."""

    def __init__(self, fhir, model: str, version: str, backend: str, device_id: str = "oversight-ai"):
        self._fhir = fhir
        self._device_id = device_id
        self._model, self._version, self._backend = model, version, backend

    def ensure_device(self) -> str:
        device = R.build_device(self._model, self._version, self._backend, self._device_id)
        self._fhir.update(device)  # PUT with stable id
        return self._device_id

    def persist_recommendation(self, rec: dict) -> dict:
        self.ensure_device()
        ts = _now_iso()
        gr_id = f"gr-{uuid.uuid4().hex[:8]}"
        gr = R.build_guidance_response(rec, self._device_id, ts, gr_id)
        created_gr = self._fhir.update(gr)
        gr_ref = f"GuidanceResponse/{created_gr.get('id', gr_id)}"
        prov = R.build_ai_provenance(gr_ref, self._device_id, ts, f"prov-{uuid.uuid4().hex[:8]}")
        self._fhir.create(prov)
        refs = {"guidance_response": gr_ref, "device": f"Device/{self._device_id}"}
        if rec.get("routing", {}).get("decision") == "escalate":
            esc = R.build_escalation_event(gr_ref, rec["routing"].get("triggered_high_risk_rules", []),
                                           ts, f"esc-{uuid.uuid4().hex[:8]}")
            created = self._fhir.create(esc)
            refs["escalation_event"] = f"AuditEvent/{created.get('id')}"
        return refs

    def capture_disposition(self, guidance_ref: str, practitioner_ref: str, disposition: str,
                            reason_code: str | None = None, note: str | None = None) -> dict:
        ae = R.build_oversight_event(guidance_ref, practitioner_ref, disposition, reason_code, note,
                                     _now_iso(), f"ae-{uuid.uuid4().hex[:8]}")
        return self._fhir.create(ae)
