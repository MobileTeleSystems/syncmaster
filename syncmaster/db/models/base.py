# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

convention = {
    "ix": "ix__%(table_name)s__%(all_column_names)s",
    "uq": "uq__%(table_name)s__%(all_column_names)s",
    "ck": "ck__%(table_name)s__%(constraint_name)s",
    "fk": ("fk__%(table_name)s__%(all_column_names)s__%(referred_table_name)s"),
    "pk": "pk__%(table_name)s",
}


# as_declarative decorator causes mypy errors.
# Use inheritance from DeclarativeBase.
class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=convention)
