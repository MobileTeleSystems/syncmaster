# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from pydantic import BaseModel

from syncmaster.schemas.v1.file_formats import (
    CSV_FORMAT,
    EXCEL_FORMAT,
    JSON_FORMAT,
    JSONLINE_FORMAT,
    XML_FORMAT,
)


class CSV(BaseModel):
    type: CSV_FORMAT
    delimiter: str = ","
    encoding: str = "utf-8"
    quote: str = '"'
    escape: str = "\\"
    include_header: bool = False
    line_sep: str = "\n"


class JSONLine(BaseModel):
    type: JSONLINE_FORMAT
    encoding: str = "utf-8"
    line_sep: str = "\n"


class JSON(BaseModel):
    type: JSON_FORMAT
    encoding: str = "utf-8"
    line_sep: str = "\n"


class Excel(BaseModel):
    type: EXCEL_FORMAT
    include_header: bool = False
    start_cell: str | None = None


class XML(BaseModel):
    type: XML_FORMAT
    root_tag: str
    row_tag: str
