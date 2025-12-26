#!/bin/env python3
# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0

import json
import sys
from pathlib import Path

from fastapi import FastAPI

from syncmaster.server import get_application


def get_openapi_schema(app: FastAPI) -> dict:
    return app.openapi()


if __name__ == "__main__":
    app = get_application()
    schema = get_openapi_schema(app)
    file_path = sys.argv[1]
    if not file_path:
        msg = "File path not sent"
        raise ValueError(msg)
    with Path(file_path).open("w") as file:
        json.dump(schema, file)
