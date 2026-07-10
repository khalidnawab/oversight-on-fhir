import copy
import importlib.util
from pathlib import Path

import httpx
import pytest

from oversight.config import Settings
from oversight.fhir.client import FhirClient
from oversight.oversight.service import OversightService
from tests.test_oversight_integration import SURFACE_REC

_SCRIPT = Path(__file__).parent.parent / "scripts" / "independent_client.py"


def _load_independent_client():
    spec = importlib.util.spec_from_file_location("independent_client", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _hapi_up(base):
    try:
        return httpx.get(f"{base}/metadata", timeout=3).status_code == 200
    except Exception:
        return False


settings = Settings()
pytestmark = pytest.mark.skipif(not _hapi_up(settings.fhir_base_url), reason="HAPI not running")


def test_independent_client_has_no_project_imports():
    src = _SCRIPT.read_text(encoding="utf-8")
    assert "import oversight" not in src and "from oversight" not in src


def test_reconstructs_full_oversight_story_over_rest():
    svc = OversightService(FhirClient.from_settings(settings), model="claude-opus-4-8",
                           version="0.1.0", backend="frontier")
    refs = svc.persist_recommendation(copy.deepcopy(SURFACE_REC))
    gr_id = refs["guidance_response"].split("/", 1)[1]
    svc.capture_disposition(refs["guidance_response"], "Practitioner/dr-alice",
                            disposition="reject", reason_code="data-vintage", note="Newer culture back.")

    ic = _load_independent_client()
    story = ic.reconstruct(settings.fhir_base_url, gr_id)

    assert story["patient"] == "Patient/clean-1"
    assert story["produced_by_ai"] and story["produced_by_ai"].startswith("Device/")
    assert story["dispositions"], "expected at least one disposition"
    d = story["dispositions"][0]
    assert d["who"] == "Practitioner/dr-alice"
    assert d["disposition"] == "reject"
    assert d["reason"] == "data-vintage"
    assert d["note"] == "Newer culture back."
