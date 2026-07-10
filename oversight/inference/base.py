from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class InferenceResult:
    """What every backend returns. `samples` supports self-consistency confidence (Section 9.2)."""
    recommendation: dict
    samples: list[dict] = field(default_factory=list)
    raw_meta: dict = field(default_factory=dict)


@runtime_checkable
class InferenceBackend(Protocol):
    """The single narrow seam (Section 4.1). Every other subsystem imports THIS, never a concrete backend."""

    name: str

    def generate(self, prompt: str, schema: dict, n_samples: int = 1) -> InferenceResult:
        """Return schema-valid structured output. `n_samples` > 1 draws multiple samples for confidence."""
        ...
