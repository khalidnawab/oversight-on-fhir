import httpx
import pytest
import respx

from oversight.errors import FhirError
from oversight.fhir.client import FhirClient

BASE = "http://fhir.test/fhir"


@respx.mock
def test_read_resource():
    respx.get(f"{BASE}/Patient/p1").mock(return_value=httpx.Response(200, json={"resourceType": "Patient", "id": "p1"}))
    client = FhirClient(base_url=BASE)
    res = client.read("Patient", "p1")
    assert res["resourceType"] == "Patient"
    assert res["id"] == "p1"


@respx.mock
def test_search_returns_entries():
    bundle = {"resourceType": "Bundle", "type": "searchset",
              "entry": [{"resource": {"resourceType": "MedicationRequest", "id": "m1"}}]}
    respx.get(f"{BASE}/MedicationRequest").mock(return_value=httpx.Response(200, json=bundle))
    client = FhirClient(base_url=BASE)
    results = client.search("MedicationRequest", {"patient": "Patient/p1"})
    assert len(results) == 1
    assert results[0]["id"] == "m1"


@respx.mock
def test_create_returns_server_resource():
    respx.post(f"{BASE}/AuditEvent").mock(
        return_value=httpx.Response(201, json={"resourceType": "AuditEvent", "id": "ae1"}))
    client = FhirClient(base_url=BASE)
    created = client.create({"resourceType": "AuditEvent"})
    assert created["id"] == "ae1"


@respx.mock
def test_bearer_token_is_sent():
    route = respx.get(f"{BASE}/Patient/p1").mock(
        return_value=httpx.Response(200, json={"resourceType": "Patient", "id": "p1"}))
    client = FhirClient(base_url=BASE, bearer_token="secret")
    client.read("Patient", "p1")
    assert route.calls.last.request.headers["Authorization"] == "Bearer secret"


@respx.mock
def test_http_error_becomes_fhir_error():
    respx.get(f"{BASE}/Patient/nope").mock(return_value=httpx.Response(404, json={"resourceType": "OperationOutcome"}))
    client = FhirClient(base_url=BASE)
    with pytest.raises(FhirError):
        client.read("Patient", "nope")
