from oversight.inference.base import InferenceBackend, InferenceResult


def test_result_shape():
    r = InferenceResult(recommendation={"a": 1}, samples=[{"a": 1}], raw_meta={"backend": "x"})
    assert r.recommendation == {"a": 1}
    assert r.samples == [{"a": 1}]
    assert r.raw_meta["backend"] == "x"


def test_protocol_is_structural():
    class Dummy:
        name = "dummy"

        def generate(self, prompt, schema, n_samples=1):
            return InferenceResult(recommendation={}, samples=[{}], raw_meta={})

    # A structural Protocol check: Dummy satisfies InferenceBackend without inheritance.
    assert isinstance(Dummy(), InferenceBackend)
