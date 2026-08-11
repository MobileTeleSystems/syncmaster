import os
from textwrap import dedent

import pytest

from syncmaster.worker.settings import WorkerAppSettings

pytestmark = [pytest.mark.worker]


def _clear_settings_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for variable_name in tuple(os.environ):
        if variable_name.startswith("SYNCMASTER__"):
            monkeypatch.delenv(variable_name)


def test_worker_settings_are_loaded_from_default_yaml_file(
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
              url: "postgresql+asyncpg://user:password@localhost:5432/syncmaster"
            broker:
              url: amqp://user:password@localhost:5672/
            encryption:
              secret_key: "secret_key"
            worker:
              log_url_template: "https://logs.location.example.com/syncmaster-worker?correlation_id={{ correlation_id }}&run_id={{ run.id }}"
              spark_session_default_config:
                spark.master: local
            """,
        ),
        encoding="utf-8",
    )

    settings = WorkerAppSettings()

    assert str(settings.database.url) == "postgresql+asyncpg://user:password@localhost:5432/syncmaster"
    assert str(settings.broker.url) == "amqp://user:password@localhost:5672/"
    assert settings.encryption.secret_key == "secret_key"
    assert (
        settings.worker.log_url_template
        == "https://logs.location.example.com/syncmaster-worker?correlation_id={{ correlation_id }}&run_id={{ run.id }}"
    )
    assert settings.worker.spark_session_default_config == {"spark.master": "local"}


def test_worker_settings_yaml_file_overrides_environment(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_settings_environment(monkeypatch)
    config_path = tmp_path / "custom.yml"
    config_path.write_text(
        dedent(
            """\
            database:
              url: postgresql+asyncpg://yaml:yaml@localhost:5432/syncmaster
            broker:
              url: amqp://yaml:yaml@localhost:5672/
            encryption:
              secret_key: "yaml_secret_key"
            worker:
              log_url_template: "https://yaml/syncmaster-worker?correlation_id={{ correlation_id }}&run_id={{ run.id }}"
              spark_session_default_config:
                spark.master: yaml
            """,
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("SYNCMASTER_CONFIG_FILE", str(config_path))
    monkeypatch.setenv(
        "SYNCMASTER__DATABASE__URL",
        "postgresql+asyncpg://env:env@localhost:5432/syncmaster",
    )
    monkeypatch.setenv(
        "SYNCMASTER__BROKER__URL",
        "amqp://env:env@localhost:5672/",
    )
    monkeypatch.setenv("SYNCMASTER__ENCRYPTION__SECRET_KEY", "env_secret_key")
    monkeypatch.setenv(
        "SYNCMASTER__WORKER__LOG_URL_TEMPLATE",
        "https://env/syncmaster-worker?correlation_id={{ correlation_id }}&run_id={{ run.id }}",
    )
    monkeypatch.setenv("SYNCMASTER__WORKER__SPARK_SESSION_DEFAULT_CONFIG", '{"spark.master": "env"}')

    settings = WorkerAppSettings()

    assert str(settings.database.url) == "postgresql+asyncpg://yaml:yaml@localhost:5432/syncmaster"
    assert str(settings.broker.url) == "amqp://yaml:yaml@localhost:5672/"
    assert settings.encryption.secret_key == "yaml_secret_key"
    assert (
        settings.worker.log_url_template
        == "https://yaml/syncmaster-worker?correlation_id={{ correlation_id }}&run_id={{ run.id }}"
    )
    assert settings.worker.spark_session_default_config == {"spark.master": "yaml"}


def test_worker_settings_can_be_loaded_from_environment_without_yaml_file(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_settings_environment(monkeypatch)
    monkeypatch.setenv("SYNCMASTER_CONFIG_FILE", str(tmp_path / "missing.yml"))
    monkeypatch.setenv(
        "SYNCMASTER__DATABASE__URL",
        "postgresql+asyncpg://env:env@localhost:5432/syncmaster",
    )
    monkeypatch.setenv(
        "SYNCMASTER__BROKER__URL",
        "amqp://env:env@localhost:5672/",
    )
    monkeypatch.setenv("SYNCMASTER__ENCRYPTION__SECRET_KEY", "env_secret_key")
    monkeypatch.setenv(
        "SYNCMASTER__WORKER__LOG_URL_TEMPLATE",
        "https://env/syncmaster-worker?correlation_id={{ correlation_id }}&run_id={{ run.id }}",
    )
    monkeypatch.setenv("SYNCMASTER__WORKER__SPARK_SESSION_DEFAULT_CONFIG", '{"spark.master": "env"}')

    settings = WorkerAppSettings()

    assert str(settings.database.url) == "postgresql+asyncpg://env:env@localhost:5432/syncmaster"
    assert str(settings.broker.url) == "amqp://env:env@localhost:5672/"
    assert settings.encryption.secret_key == "env_secret_key"
    assert (
        settings.worker.log_url_template
        == "https://env/syncmaster-worker?correlation_id={{ correlation_id }}&run_id={{ run.id }}"
    )
    assert settings.worker.spark_session_default_config == {"spark.master": "env"}
