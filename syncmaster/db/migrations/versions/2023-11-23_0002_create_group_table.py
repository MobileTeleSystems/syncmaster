# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
"""Create group table

Revision ID: 0002
Revises: 0001
Create Date: 2023-11-23 11:36:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "group",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.String(length=512), nullable=False),
        sa.Column("owner_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('english'::regconfig, name)", persisted=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"], name=op.f("fk__group__owner_id__user"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__group")),
        sa.UniqueConstraint("name", name=op.f("uq__group__name")),
    )
    op.create_index(op.f("ix__group__owner_id"), "group", ["owner_id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix__group__owner_id"), table_name="group")
    op.drop_table("group")
