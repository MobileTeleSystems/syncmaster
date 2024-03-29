#!/bin/env python3
# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0

import json
import sys

from fastapi import FastAPI

from syncmaster.backend.main import get_application
from syncmaster.config import Settings


def get_openapi_schema(app: FastAPI) -> dict:
    return app.openapi()


if __name__ == "__main__":
    settings = Settings()
    app = get_application(settings)
    schema = get_openapi_schema(app)
    file_path = sys.argv[1]
    if not file_path:
        raise ValueError("File path not sent")
    with open(file_path, "w") as file:
        json.dump(schema, file)
