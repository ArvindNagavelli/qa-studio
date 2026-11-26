"""Application settings, loaded from environment variables and ``backend/.env``.

Rules this module enforces:

* Every secret is a ``SecretStr``: ``repr()``, ``str()`` and logging show ``**********``.
  Call ``.get_secret_value()`` only at the point of use.
* Missing or invalid settings fail fast with a message that names the variable but
  never echoes its value (pydantic's default error text includes the input value,
  which could be a secret, so it is reformatted here).
* Real environment variables take precedence over the ``.env`` file.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class SettingsError(RuntimeError):
    """Raised when configuration is missing or invalid. Never contains secret values."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: Literal["development", "test", "production"] = "development"

    # --- required ---------------------------------------------------------
    # The URL can embed a password, so it is treated as a secret too.
    database_url: SecretStr
    jwt_secret: SecretStr = Field(min_length=32)

    # --- Google sign-in (required once auth is implemented) ---------------
    google_client_id: str | None = None
    google_client_secret: SecretStr | None = None

    # --- LLM -------------------------------------------------------------
    llm_provider: Literal["anthropic", "mock"] = "mock"
    anthropic_api_key: SecretStr | None = None

    # Local-only shortcut login; must never be enabled in production.
    dev_login: bool = False

    @model_validator(mode="after")
    def _check_cross_field_rules(self) -> Settings:
        if self.llm_provider == "anthropic" and self.anthropic_api_key is None:
            raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")
        if self.dev_login and self.app_env == "production":
            raise ValueError("DEV_LOGIN must be false when APP_ENV=production")
        return self


def _describe(exc: ValidationError) -> str:
    lines = []
    for err in exc.errors(include_input=False, include_url=False, include_context=False):
        name = ".".join(str(part) for part in err["loc"]).upper() or "SETTINGS"
        lines.append(f"  - {name}: {err['msg']}")
    return "\n".join(lines)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings, validating them on first use."""
    try:
        return Settings()  # values come from the environment / .env
    except ValidationError as exc:
        # `from None` drops the original exception, whose text may contain secret values.
        raise SettingsError(
            "Invalid or missing configuration. Set these variables in the environment "
            "or in backend/.env (see backend/.env.example):\n" + _describe(exc)
        ) from None
