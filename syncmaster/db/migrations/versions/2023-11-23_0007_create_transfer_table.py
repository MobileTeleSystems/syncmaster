# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
"""Create transfer table

Revision ID: 0007_create_transfer_table
Revises: 0006_create_auth_data_table
Create Date: 2023-11-23 11:41:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0007_create_transfer_table"
down_revision = "0006_create_auth_data_table"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "transfer",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("group_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.String(length=512), nullable=False),
        sa.Column("source_connection_id", sa.BigInteger(), nullable=False),
        sa.Column("target_connection_id", sa.BigInteger(), nullable=False),
        sa.Column("strategy_params", sa.JSON(), nullable=False),
        sa.Column("source_params", sa.JSON(), nullable=False),
        sa.Column("target_params", sa.JSON(), nullable=False),
        sa.Column("is_scheduled", sa.Boolean(), nullable=False),
        sa.Column("schedule", sa.String(length=32), nullable=False),
        sa.Column("queue_id", sa.BigInteger(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["group.id"],
            name=op.f("fk__transfer__group_id__group"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["queue_id"],
            ["queue.id"],
            name=op.f("fk__transfer__queue_id__queue"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_connection_id"],
            ["connection.id"],
            name=op.f("fk__transfer__source_connection_id__connection"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["target_connection_id"],
            ["connection.id"],
            name=op.f("fk__transfer__target_connection_id__connection"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__transfer")),
        sa.UniqueConstraint("name", "group_id", name=op.f("uq__transfer__name_group_id")),
    )
    op.create_index(op.f("ix__transfer__group_id"), "transfer", ["group_id"], unique=False)
    op.create_index(op.f("ix__transfer__source_connection_id"), "transfer", ["source_connection_id"], unique=False)
    op.create_index(op.f("ix__transfer__target_connection_id"), "transfer", ["target_connection_id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix__transfer__target_connection_id"), table_name="transfer")
    op.drop_index(op.f("ix__transfer__source_connection_id"), table_name="transfer")
    op.drop_index(op.f("ix__transfer__group_id"), table_name="transfer")
    op.drop_table("transfer")
