# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RunDTO:
    id: int
    created_at: datetime
