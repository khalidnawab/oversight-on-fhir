import json
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from oversight.inference.base import InferenceResult


class FrontierAPIBackend:
    """Hosted frontier model behind the seam. Uses the Anthropic Messages API with a
    JSON-Schema output_config so the response is schema-constrained (Section 8)."""

    def __init__(self, model: str = "claude-opus-4-8", client: Any | None = None,
                 max_tokens: int = 4000, effort: str = "medium", timeout: float = 90.0):
        self.model = model
        self.name = f"frontier:{model}"
        self._max_tokens = max_tokens
        self._effort = effort
        if client is not None:
            self._client = client
        else:
            from anthropic import Anthropic
            self._client = Anthropic(timeout=timeout, max_retries=1)  # reads ANTHROPIC_API_KEY from env

    def _one(self, prompt: str, schema: dict) -> dict:
        msg = self._client.messages.create(
            model=self.model,
            max_tokens=self._max_tokens,
            thinking={"type": "adaptive"},
            output_config={"format": {"type": "json_schema", "schema": schema}, "effort": self._effort},
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(block.text for block in msg.content if getattr(block, "type", None) == "text")
        return json.loads(text)

    def generate(self, prompt: str, schema: dict, n_samples: int = 1) -> InferenceResult:
        n = max(1, n_samples)
        if n == 1:
            samples = [self._one(prompt, schema)]
        else:
            # Self-consistency samples are independent — run them concurrently, not sequentially.
            with ThreadPoolExecutor(max_workers=n) as ex:
                samples = list(ex.map(lambda _: self._one(prompt, schema), range(n)))
        return InferenceResult(recommendation=samples[0], samples=samples,
                               raw_meta={"backend": self.name, "model": self.model})
