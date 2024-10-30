# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
"""Create queue table

Revision ID: 0003_create_queue_table
Revises: 0002_create_group_table
Create Date: 2023-11-23 11:37:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0003_create_queue_table"
down_revision = "0002_create_group_table"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "queue",
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("group_id", sa.BigInteger(), nullable=False),
        sa.Column("description", sa.String(length=512), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["group.id"],
            name=op.f("fk__queue__group_id__group"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__queue")),
        sa.UniqueConstraint("name", name=op.f("uq__queue__name")),
    )
    op.create_index(op.f("ix__queue__group_id"), "queue", ["group_id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix__queue__group_id"), table_name="queue")
    op.drop_table("queue")
