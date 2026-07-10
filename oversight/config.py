from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from oversight.errors import ConfigError


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OVERSIGHT_", env_file=".env", extra="ignore")

    fhir_base_url: str = "http://localhost:8080/fhir"
    fhir_bearer_token: str = ""
    backend: str = "frontier"
    synthetic_data_only: bool = True
    model: str = "claude-opus-4-8"
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)

    def __init__(self, **kwargs):
        try:
            super().__init__(**kwargs)
        except ConfigError:
            raise
        except Exception as e:  # noqa: BLE001 - normalize pydantic ValidationError to ConfigError
            raise ConfigError(str(e)) from e

    @field_validator("backend")
    @classmethod
    def _valid_backend(cls, v: str) -> str:
        if v not in ("frontier", "local"):
            raise ValueError(f"backend must be 'frontier' or 'local', got {v!r}")
        return v
