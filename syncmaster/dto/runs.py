# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RunDTO:
    id: str
    created_at: datetime
