from __future__ import annotations

from collections.abc import Iterator

import pytest

from app.core.config import Settings, SettingsError, get_settings

SETTINGS_VARS = (
    "APP_ENV",
    "DATABASE_URL",
    "JWT_SECRET",
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "LLM_PROVIDER",
    "ANTHROPIC_API_KEY",
    "DEV_LOGIN",
)


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Ignore the developer's shell environment and local backend/.env file."""
    for name in SETTINGS_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_missing_required_settings_are_named(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(SettingsError) as exc_info:
        get_settings()

    message = str(exc_info.value)
    assert "DATABASE_URL" in message
    assert "JWT_SECRET" in message


def test_error_never_echoes_secret_values(monkeypatch: pytest.MonkeyPatch) -> None:
    leaked = "too-short-but-still-private"  # pragma: allowlist secret
    fake_url = "postgresql+asyncpg://u:pw-value@localhost/db"  # pragma: allowlist secret
    monkeypatch.setenv("DATABASE_URL", fake_url)
    monkeypatch.setenv("JWT_SECRET", leaked)

    with pytest.raises(SettingsError) as exc_info:
        get_settings()

    message = str(exc_info.value)
    assert "JWT_SECRET" in message
    assert leaked not in message
    assert "pw-value" not in message
    assert exc_info.value.__cause__ is None
    assert exc_info.value.__suppress_context__ is True


def test_anthropic_provider_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://localhost/db")
    monkeypatch.setenv("JWT_SECRET", "x" * 32)
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")

    with pytest.raises(SettingsError, match="ANTHROPIC_API_KEY"):
        get_settings()


def test_secrets_are_masked_in_repr(monkeypatch: pytest.MonkeyPatch) -> None:
    secret = "s" * 40
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://localhost/db")
    monkeypatch.setenv("JWT_SECRET", secret)

    settings = get_settings()

    assert secret not in repr(settings)
    assert settings.jwt_secret.get_secret_value() == secret
