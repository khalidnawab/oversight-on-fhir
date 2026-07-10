import pytest

from oversight.config import Settings
from oversight.errors import ConfigError


def test_defaults_load(monkeypatch):
    monkeypatch.delenv("OVERSIGHT_FHIR_BASE_URL", raising=False)
    monkeypatch.delenv("OVERSIGHT_BACKEND", raising=False)
    s = Settings()
    assert s.fhir_base_url == "http://localhost:8080/fhir"
    assert s.backend == "frontier"
    assert s.synthetic_data_only is True
    assert s.model == "claude-opus-4-8"
    assert 0.0 <= s.confidence_threshold <= 1.0


def test_env_override(monkeypatch):
    monkeypatch.setenv("OVERSIGHT_BACKEND", "local")
    monkeypatch.setenv("OVERSIGHT_CONFIDENCE_THRESHOLD", "0.55")
    s = Settings()
    assert s.backend == "local"
    assert s.confidence_threshold == 0.55


def test_invalid_backend_rejected(monkeypatch):
    monkeypatch.setenv("OVERSIGHT_BACKEND", "gpt")
    with pytest.raises(ConfigError):
        Settings()
