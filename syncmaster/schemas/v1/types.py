# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Annotated

from pydantic import AnyUrl, StringConstraints, UrlConstraints

NameConstr = Annotated[str, StringConstraints(min_length=3, max_length=128)]  # noqa: WPS432
URL = Annotated[AnyUrl, UrlConstraints(allowed_schemes=["http", "https"], preserve_empty_path=True)]
