import os
from textwrap import dedent

import pytest

from syncmaster.server.settings import ServerAppSettings


def _clear_settings_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for variable_name in tuple(os.environ):
        if variable_name.startswith("SYNCMASTER__"):
            monkeypatch.delenv(variable_name)


def test_server_settings_are_loaded_from_default_yaml_file(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_settings_environment(monkeypatch)
    monkeypatch.delenv("SYNCMASTER_CONFIG_FILE", raising=False)
    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / "config.yml"
    config_path.write_text(
        dedent(
            """\
            database:
              url: "postgresql+asyncpg://user:password'#[value]@localhost:5432/syncmaster"
            broker:
              url: amqp://user:password@localhost:5672/
            encryption:
              secret_key: "secret_key"
            server:
              debug: true
              cors:
                enabled: true
                allow_origins: ["*"]
                allow_credentials: true
                allow_methods: ["GET", "POST"]
                allow_headers: ["*"]
                expose_headers: ["X-Request-ID", "Location"]
            """,
        ),
        encoding="utf-8",
    )

    settings = ServerAppSettings()

    assert settings.database.url == "postgresql+asyncpg://user:password'#[value]@localhost:5432/syncmaster"
    assert settings.broker.url == "amqp://user:password@localhost:5672/"
    assert settings.encryption.secret_key == "secret_key"
    assert settings.server.debug is True
    assert settings.server.cors.dict() == {
        "enabled": True,
        "allow_origins": ["*"],
        "allow_credentials": True,
        "allow_methods": ["GET", "POST"],
        "allow_headers": ["*"],
        "expose_headers": ["X-Request-ID", "Location"],
    }


def test_server_settings_yaml_file_overrides_environment(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_settings_environment(monkeypatch)
    config_path = tmp_path / "custom.yml"
    config_path.write_text(
        dedent(
            """\
            database:
              url: postgresql+asyncpg://yaml@localhost:5432/syncmaster
            broker:
              url: amqp://yaml@localhost:5672/
            encryption:
              secret_key: "yaml_secret_key"
            server:
              debug: false
              cors:
                allow_origins: [https://yaml.example.com]
            """,
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("SYNCMASTER_CONFIG_FILE", str(config_path))
    monkeypatch.setenv(
        "SYNCMASTER__DATABASE__URL",
        "postgresql+asyncpg://env@localhost:5432/syncmaster",
    )
    monkeypatch.setenv(
        "SYNCMASTER__BROKER__URL",
        "amqp://env@localhost:5672/",
    )
    monkeypatch.setenv("SYNCMASTER__ENCRYPTION__SECRET_KEY", "env_secret_key")
    monkeypatch.setenv("SYNCMASTER__SERVER__DEBUG", "true")
    monkeypatch.setenv(
        "SYNCMASTER__SERVER__CORS__ALLOW_ORIGINS",
        '["https://env.example.com"]',
    )

    settings = ServerAppSettings()

    assert settings.database.url == "postgresql+asyncpg://yaml@localhost:5432/syncmaster"
    assert settings.broker.url == "amqp://yaml@localhost:5672/"
    assert settings.encryption.secret_key == "yaml_secret_key"
    assert settings.server.debug is False
    assert settings.server.cors.allow_origins == ["https://yaml.example.com"]


def test_server_settings_can_be_loaded_from_environment_without_yaml_file(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_settings_environment(monkeypatch)
    monkeypatch.setenv("SYNCMASTER_CONFIG_FILE", str(tmp_path / "missing.yml"))
    monkeypatch.setenv(
        "SYNCMASTER__DATABASE__URL",
        "postgresql+asyncpg://env@localhost:5432/syncmaster",
    )
    monkeypatch.setenv(
        "SYNCMASTER__BROKER__URL",
        "amqp://env@localhost:5672/",
    )
    monkeypatch.setenv("SYNCMASTER__ENCRYPTION__SECRET_KEY", "env_secret_key")

    settings = ServerAppSettings()

    assert settings.database.url == "postgresql+asyncpg://env@localhost:5432/syncmaster"
    assert settings.broker.url == "amqp://env@localhost:5672/"
    assert settings.encryption.secret_key == "env_secret_key"
