# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from pydantic import BaseModel

from syncmaster.schemas.v1.file_formats import CSV_FORMAT, JSON_FORMAT, JSONLINE_FORMAT


class CSV(BaseModel):
    type: CSV_FORMAT
    delimiter: str = ","
    encoding: str = "utf-8"
    quote: str = '"'
    escape: str = "\\"
    header: bool = False
    line_sep: str = "\n"


class JSONLine(BaseModel):
    type: JSONLINE_FORMAT
    encoding: str = "utf-8"
    line_sep: str = "\n"


class JSON(BaseModel):
    type: JSON_FORMAT
    encoding: str = "utf-8"
    line_sep: str = "\n"
