import json
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft202012Validator

from oversight.errors import SchemaValidationError

_SCHEMA_PATH = Path(__file__).parent / "deescalation-recommendation.schema.json"


@lru_cache(maxsize=1)
def load_schema() -> dict:
    return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _validator() -> Draft202012Validator:
    return Draft202012Validator(load_schema())


def validate_recommendation(obj: dict) -> None:
    """Raise SchemaValidationError if obj does not conform. Returns None on success."""
    errors = sorted(_validator().iter_errors(obj), key=lambda e: list(e.path))
    if errors:
        messages = "; ".join(f"{list(e.path)}: {e.message}" for e in errors)
        raise SchemaValidationError(messages)
