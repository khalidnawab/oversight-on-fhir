from typing import Any

import httpx

from oversight.errors import FhirError

_FHIR_JSON = "application/fhir+json"


class FhirClient:
    """Reads clinical resources and writes recommendation/oversight resources over FHIR REST.
    The single component that knows FHIR wire details (Section 5 / Section 6)."""

    def __init__(self, base_url: str, bearer_token: str = "", timeout: float = 30.0):
        self._base = base_url.rstrip("/")
        headers = {"Accept": _FHIR_JSON, "Content-Type": _FHIR_JSON}
        if bearer_token:
            headers["Authorization"] = f"Bearer {bearer_token}"
        self._http = httpx.Client(base_url=self._base, headers=headers, timeout=timeout)

    @classmethod
    def from_settings(cls, settings) -> "FhirClient":
        return cls(base_url=settings.fhir_base_url, bearer_token=settings.fhir_bearer_token)

    def read(self, resource_type: str, resource_id: str) -> dict:
        return self._request("GET", f"/{resource_type}/{resource_id}")

    def search(self, resource_type: str, params: dict[str, Any] | None = None) -> list[dict]:
        bundle = self._request("GET", f"/{resource_type}", params=params)
        return [e["resource"] for e in bundle.get("entry", []) if "resource" in e]

    def create(self, resource: dict) -> dict:
        rt = resource["resourceType"]
        return self._request("POST", f"/{rt}", json=resource)

    def transaction(self, bundle: dict) -> dict:
        return self._request("POST", "/", json=bundle)

    def _request(self, method: str, path: str, **kwargs) -> dict:
        try:
            resp = self._http.request(method, path, **kwargs)
        except httpx.HTTPError as e:
            raise FhirError(f"{method} {path} failed: {e}") from e
        if resp.status_code >= 400:
            raise FhirError(f"{method} {path} -> {resp.status_code}: {resp.text[:500]}")
        if not resp.content:
            return {}
        return resp.json()
