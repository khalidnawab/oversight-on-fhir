import json
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft202012Validator

from oversight.errors import SchemaValidationError

_SCHEMA_PATH = Path(__file__).parent / "deescalation-recommendation.schema.json"


@lru_cache(maxsize=1)
def load_schema() -> dict:
    return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


# Validation-only keywords that strict structured-output mode does not accept in a request schema.
_STRIP_KEYWORDS = {"minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
                   "pattern", "format", "minItems", "maxItems", "minLength", "maxLength"}

# Fields the model must NOT author — they are computed by deterministic code after generation
# (Section 4.3 tool result; Section 9 routing; Section 9.2 self-consistency confidence). The model
# is constrained to emit null for these; the orchestrator fills them in.
_CODE_OWNED_FIELDS = ("deterministic_tool_result", "confidence", "routing")


def _sanitize(node):
    if isinstance(node, dict):
        out = {k: _sanitize(v) for k, v in node.items() if k not in _STRIP_KEYWORDS}
        # Strict structured output: every object needs additionalProperties:false and all
        # properties listed in required.
        types = out.get("type")
        is_object = out.get("properties") is not None or types == "object" or (
            isinstance(types, list) and "object" in types)
        if is_object and "properties" in out:
            out["additionalProperties"] = False
            out["required"] = list(out["properties"].keys())
        return out
    if isinstance(node, list):
        return [_sanitize(x) for x in node]
    return node


@lru_cache(maxsize=1)
def load_model_schema() -> dict:
    """Schema sent to a constrained backend (frontier structured output / local decoder).

    Nulls the code-owned fields so the model only authors the clinical recommendation and its
    evidence, and strips validation-only keywords the strict API rejects. The full artifact is
    still checked against the complete schema by validate_recommendation after the orchestrator
    fills the code-owned fields in."""
    import copy
    s = copy.deepcopy(load_schema())
    for field in _CODE_OWNED_FIELDS:
        s["properties"][field] = {"type": "null"}
    return _sanitize(s)


@lru_cache(maxsize=1)
def _validator() -> Draft202012Validator:
    return Draft202012Validator(load_schema())


def validate_recommendation(obj: dict) -> None:
    """Raise SchemaValidationError if obj does not conform. Returns None on success."""
    errors = sorted(_validator().iter_errors(obj), key=lambda e: list(e.path))
    if errors:
        messages = "; ".join(f"{list(e.path)}: {e.message}" for e in errors)
        raise SchemaValidationError(messages)
