# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
"""Create user table

Revision ID: 2023_11_23_0001_create_user_table
Revises: 2023_11_23_0000_alter_alembic_version
Create Date: 2023-11-23 11:35:18.193060
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2023_11_23_0001_create_user_table"
down_revision = "2023_11_23_0000_alter_alembic_version"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=256), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__user")),
    )
    op.create_index(op.f("ix__user__username"), "user", ["username"], unique=True)


def downgrade():
    op.drop_index(op.f("ix__user__username"), table_name="user")
    op.drop_table("user")
