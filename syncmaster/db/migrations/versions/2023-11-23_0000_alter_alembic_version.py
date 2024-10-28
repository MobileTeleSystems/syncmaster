# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
"""Alter alembic_version table to increase version_num length

Revision ID: 2023_11_23_0000_alter_alembic_version
Revises:
Create Date: 2023-11-23 11:34:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2023_11_23_0000_alter_alembic_version"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "alembic_version",
        "version_num",
        existing_type=sa.String(length=32),
        type_=sa.String(length=128),
        existing_nullable=False,
    )


def downgrade():
    op.alter_column(
        "alembic_version",
        "version_num",
        existing_type=sa.String(length=128),
        type_=sa.String(length=32),
        existing_nullable=False,
    )
