# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
"""Create transfer table

Revision ID: 0007
Revises: 0006
Create Date: 2023-11-23 11:41:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade():
    sql_expression = (
        "to_tsvector('english'::regconfig, "
        "name || ' ' || "
        "COALESCE(json_extract_path_text(source_params, 'table_name'), '') || ' ' || "
        "COALESCE(json_extract_path_text(target_params, 'table_name'), '') || ' ' || "
        "COALESCE(json_extract_path_text(source_params, 'directory_path'), '') || ' ' || "
        "COALESCE(json_extract_path_text(target_params, 'directory_path'), '') || ' ' || "
        "translate(name, './', '  ') || ' ' || "
        "COALESCE(translate(json_extract_path_text(source_params, 'table_name'), './', '  '), '') || ' ' || "
        "COALESCE(translate(json_extract_path_text(target_params, 'table_name'), './', '  '), '') || ' ' || "
        "COALESCE(translate(json_extract_path_text(source_params, 'directory_path'), './', '  '), '') || ' ' || "
        "COALESCE(translate(json_extract_path_text(target_params, 'directory_path'), './', '  '), '')"
        ")"
    )
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
        sa.Column("transformations", sa.JSON(), nullable=False),
        sa.Column("resources", sa.JSON(), nullable=False),
        sa.Column("is_scheduled", sa.Boolean(), nullable=False),
        sa.Column("schedule", sa.String(length=32), nullable=False),
        sa.Column("queue_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
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
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed(sql_expression, persisted=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__transfer")),
        sa.UniqueConstraint("name", "group_id", name=op.f("uq__transfer__name_group_id")),
    )
    op.create_index(op.f("ix__transfer__group_id"), "transfer", ["group_id"], unique=False)
    op.create_index(op.f("ix__transfer__source_connection_id"), "transfer", ["source_connection_id"], unique=False)
    op.create_index(op.f("ix__transfer__target_connection_id"), "transfer", ["target_connection_id"], unique=False)
    op.create_index("idx_transfer_search_vector", "transfer", ["search_vector"], unique=False, postgresql_using="gin")


def downgrade():
    op.drop_index(op.f("ix__transfer__target_connection_id"), table_name="transfer")
    op.drop_index(op.f("ix__transfer__source_connection_id"), table_name="transfer")
    op.drop_index(op.f("ix__transfer__group_id"), table_name="transfer")
    op.drop_index("idx_transfer_search_vector", table_name="transfer", postgresql_using="gin")
    op.drop_table("transfer")
