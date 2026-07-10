class OversightError(Exception):
    """Base class for all Oversight-on-FHIR errors."""


class ConfigError(OversightError):
    """Invalid or unsafe configuration."""


class SchemaValidationError(OversightError):
    """A recommendation failed JSON Schema validation."""


class BackendPolicyError(OversightError):
    """A backend was used in violation of a safety policy (e.g. frontier + real data)."""


class FhirError(OversightError):
    """A FHIR REST operation failed."""
