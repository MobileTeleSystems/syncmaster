# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
"""Create queue table

Revision ID: 0003
Revises: 0002
Create Date: 2023-11-23 11:37:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "queue",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("slug", sa.String(length=256), nullable=False),
        sa.Column("group_id", sa.BigInteger(), nullable=False),
        sa.Column("description", sa.String(length=512), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('english'::regconfig, name)", persisted=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["group.id"],
            name=op.f("fk__queue__group_id__group"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__queue")),
        sa.UniqueConstraint("slug", name=op.f("uq__queue__slug")),
    )
    op.create_index(op.f("ix__queue__group_id"), "queue", ["group_id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix__queue__group_id"), table_name="queue")
    op.drop_table("queue")
