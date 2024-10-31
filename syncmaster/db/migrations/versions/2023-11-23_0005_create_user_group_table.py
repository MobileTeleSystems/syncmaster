# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
"""Create user_group table

Revision ID: 0005
Revises: 0004
Create Date: 2023-11-23 11:39:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_group",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("group_id", sa.BigInteger(), nullable=False),
        sa.Column("role", sa.String(255), nullable=False),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["group.id"],
            name=op.f("fk__user_group__group_id__group"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name=op.f("fk__user_group__user_id__user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", "group_id", name=op.f("pk__user_group")),
    )
    op.create_index(op.f("ix__user_group__group_id"), "user_group", ["group_id"], unique=False)
    op.create_index(op.f("ix__user_group__user_id"), "user_group", ["user_id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix__user_group__user_id"), table_name="user_group")
    op.drop_index(op.f("ix__user_group__group_id"), table_name="user_group")
    op.drop_table("user_group")
