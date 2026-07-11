import httpx
import pytest

from oversight.errors import FhirError
from oversight.fhir.client import FhirClient
from oversight.fhir.log import FhirActivityLog, activity_log


def test_ring_buffer_bounds_and_seq():
    log = FhirActivityLog(maxlen=3)
    for i in range(5):
        log.append("GET", f"Patient/p{i}", 200)
    entries = log.since(0)
    assert len(entries) == 3                       # bounded at maxlen
    assert [e["seq"] for e in entries] == [3, 4, 5]  # seq keeps counting past evictions
    assert log.latest == 5


def test_entry_shape_read_vs_write():
    log = FhirActivityLog()
    log.append("GET", "Observation?patient=p1", 200)
    log.append("POST", "AuditEvent", 201, resource_id="AuditEvent/1")
    read, write = log.since(0)
    assert read["kind"] == "read" and read["resource_id"] is None
    assert write["kind"] == "write" and write["resource_id"] == "AuditEvent/1"
    assert read["ts"]  # ISO timestamp present
    assert read["status"] == 200 and write["status"] == 201


def test_since_filters_and_clear_preserves_seq():
    log = FhirActivityLog()
    log.append("GET", "Patient/p1", 200)
    log.append("POST", "AuditEvent", 201, resource_id="AuditEvent/1")
    assert [e["target"] for e in log.since(1)] == ["AuditEvent"]
    log.clear()
    assert log.since(0) == []
    assert log.latest == 2  # seq survives clear so pollers' cursors stay valid


def _mock_client(handler) -> FhirClient:
    client = FhirClient("http://fhir.test/fhir")
    client._http = httpx.Client(transport=httpx.MockTransport(handler),
                                base_url="http://fhir.test/fhir",
                                headers={"Accept": "application/fhir+json"})
    return client


def test_client_logs_read_and_write():
    activity_log.clear()
    start = activity_log.latest

    def handler(request):
        if request.method == "GET":
            return httpx.Response(200, json={"resourceType": "Bundle", "entry": []})
        return httpx.Response(201, json={"resourceType": "AuditEvent", "id": "42"})

    client = _mock_client(handler)
    client.search("Observation", {"patient": "p1"})
    client.create({"resourceType": "AuditEvent"})
    read, write = activity_log.since(start)
    assert read["method"] == "GET" and read["kind"] == "read"
    assert read["target"] == "Observation?patient=p1"   # query params in target
    assert write["kind"] == "write" and write["resource_id"] == "AuditEvent/42"


def test_client_logs_failed_call_with_status():
    activity_log.clear()
    start = activity_log.latest

    def handler(request):
        return httpx.Response(500, text="boom")

    client = _mock_client(handler)
    with pytest.raises(FhirError):
        client.read("Patient", "p1")
    (entry,) = activity_log.since(start)
    assert entry["status"] == 500
    assert entry["target"] == "Patient/p1"


def test_client_logs_transport_error_with_no_status():
    activity_log.clear()
    start = activity_log.latest

    def handler(request):
        raise httpx.ConnectError("connection refused", request=request)

    client = _mock_client(handler)
    with pytest.raises(FhirError):
        client.read("Patient", "p1")
    (entry,) = activity_log.since(start)
    assert entry["status"] is None
    assert entry["target"] == "Patient/p1"
    assert entry["kind"] == "read"


def test_client_logs_write_even_when_body_is_not_a_dict():
    activity_log.clear()
    start = activity_log.latest

    def handler(request):
        return httpx.Response(201, json=["not", "a", "resource"])

    client = _mock_client(handler)
    client.create({"resourceType": "AuditEvent"})
    (entry,) = activity_log.since(start)
    assert entry["kind"] == "write"
    assert entry["resource_id"] is None
