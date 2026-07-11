from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from oversight.errors import ConfigError

# Load .env into the process environment so the Anthropic SDK (which reads ANTHROPIC_API_KEY
# from os.environ) picks up a key placed in the gitignored .env file.
load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OVERSIGHT_", env_file=".env", extra="ignore")

    fhir_base_url: str = "http://localhost:8080/fhir"
    fhir_bearer_token: str = ""
    backend: str = "frontier"
    synthetic_data_only: bool = True
    model: str = "claude-opus-4-8"
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    # Test-only affordance: exposes a destructive "reset recorded data" endpoint. Disable outside demos.
    enable_reset: bool = True

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
        if v not in ("frontier", "local", "demo"):
            raise ValueError(f"backend must be 'frontier', 'local', or 'demo', got {v!r}")
        return v
