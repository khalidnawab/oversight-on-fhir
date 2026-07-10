from oversight.inference.base import InferenceBackend
from oversight.inference.local_stub import LocalModelBackend
from oversight.schema.validate import load_schema, validate_recommendation


def test_stub_is_a_backend_and_returns_valid_output():
    backend = LocalModelBackend()
    assert isinstance(backend, InferenceBackend)
    assert backend.name.startswith("local:")
    result = backend.generate(prompt="anything", schema=load_schema())
    validate_recommendation(result.recommendation)
    # The stub must self-identify as canned so it can never be mistaken for real inference.
    assert result.raw_meta.get("stub") is True
