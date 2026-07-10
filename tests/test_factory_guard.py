import pytest

from oversight.config import Settings
from oversight.errors import BackendPolicyError
from oversight.inference.factory import get_backend
from oversight.inference.frontier import FrontierAPIBackend
from oversight.inference.local_stub import LocalModelBackend


def test_local_backend_selected(monkeypatch):
    monkeypatch.setenv("OVERSIGHT_BACKEND", "local")
    assert isinstance(get_backend(Settings()), LocalModelBackend)


def test_frontier_requires_synthetic_only(monkeypatch):
    monkeypatch.setenv("OVERSIGHT_BACKEND", "frontier")
    monkeypatch.setenv("OVERSIGHT_SYNTHETIC_DATA_ONLY", "false")
    with pytest.raises(BackendPolicyError):
        get_backend(Settings())


def test_frontier_allowed_with_synthetic_flag(monkeypatch):
    monkeypatch.setenv("OVERSIGHT_BACKEND", "frontier")
    monkeypatch.setenv("OVERSIGHT_SYNTHETIC_DATA_ONLY", "true")
    backend = get_backend(Settings(), client=object())  # client injected so no key needed
    assert isinstance(backend, FrontierAPIBackend)
