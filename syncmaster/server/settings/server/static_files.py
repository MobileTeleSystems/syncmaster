# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class StaticFilesSettings(BaseModel):
    """Static files serving settings.

    Files are served at ``/static`` endpoint.

    Examples
    --------

    .. code-block:: yaml
        :caption: config.yml

        server:
            static_files:
                enabled: True
                directory: /app/syncmaster/server/static
    """

    enabled: bool = Field(default=True, description="Set to ``True`` to enable static file serving")
    directory: Path = Field(
        default=Path("docs/_static"),
        description="Directory containing static files",
    )

    @field_validator("directory")
    @classmethod
    def _validate_directory(cls, value: Path, info: ValidationInfo) -> Path:
        if not info.data.get("enabled"):
            return value
        if not value.exists():
            raise ValueError(f"Directory '{value}' does not exist")
        if not value.is_dir():
            raise ValueError(f"Path '{value}' is not a directory")
        return value
