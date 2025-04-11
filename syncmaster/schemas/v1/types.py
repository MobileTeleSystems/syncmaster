# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Annotated

from pydantic import StringConstraints

NameConstr = Annotated[str, StringConstraints(min_length=3, max_length=128)]  # noqa: WPS432
