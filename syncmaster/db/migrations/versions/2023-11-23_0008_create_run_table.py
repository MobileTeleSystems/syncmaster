# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
"""Create run table

Revision ID: 0008
Revises: 0007
Create Date: 2023-11-23 11:42:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "run",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("transfer_id", sa.BigInteger(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(255), nullable=False),
        sa.Column("type", sa.String(64), nullable=False),
        sa.Column("log_url", sa.String(length=512), nullable=True),
        sa.Column("transfer_dump", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["transfer_id"],
            ["transfer.id"],
            name=op.f("fk__run__transfer_id__transfer"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__run")),
    )
    op.create_index(op.f("ix__run__type"), "run", ["type"], unique=False)
    op.create_index(op.f("ix__run__status"), "run", ["status"], unique=False)
    op.create_index(op.f("ix__run__transfer_id"), "run", ["transfer_id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix__run__transfer_id"), table_name="run")
    op.drop_index(op.f("ix__run__status"), table_name="run")
    op.drop_index(op.f("ix__run__type"), table_name="run")
    op.drop_table("run")
