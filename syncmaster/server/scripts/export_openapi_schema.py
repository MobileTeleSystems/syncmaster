#!/bin/env python3
# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

import json
import sys

from fastapi import FastAPI

from syncmaster.server import get_application


def get_openapi_schema(app: FastAPI) -> dict:
    return app.openapi()


if __name__ == "__main__":
    app = get_application()
    schema = get_openapi_schema(app)
    file_path = sys.argv[1]
    if not file_path:
        raise ValueError("File path not sent")
    with open(file_path, "w") as file:
        json.dump(schema, file)
