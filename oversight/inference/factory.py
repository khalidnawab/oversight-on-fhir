from typing import Any

from oversight.config import Settings
from oversight.errors import BackendPolicyError
from oversight.inference.base import InferenceBackend
from oversight.inference.frontier import FrontierAPIBackend
from oversight.inference.local_stub import LocalModelBackend
from oversight.inference.scripted import ScriptedDemoBackend


def get_backend(settings: Settings, client: Any | None = None) -> InferenceBackend:
    """Select the backend from config. HARD GATE: the frontier backend refuses to run unless
    synthetic_data_only is set (Section 4.9 — real PHI and the frontier API are mutually exclusive)."""
    if settings.backend == "local":
        return LocalModelBackend()
    if settings.backend == "demo":
        return ScriptedDemoBackend()
    if settings.backend == "frontier":
        if not settings.synthetic_data_only:
            raise BackendPolicyError(
                "Frontier API backend refused: OVERSIGHT_SYNTHETIC_DATA_ONLY is false. "
                "Real patient data must never reach an external API (Section 4.9)."
            )
        return FrontierAPIBackend(model=settings.model, client=client)
    raise BackendPolicyError(f"Unknown backend {settings.backend!r}")
