# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
"""Create connection table

Revision ID: 0004
Revises: 0003
Create Date: 2023-11-23 11:38:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    sql_expression = (
        "to_tsvector('english'::regconfig, "
        "name || ' ' || "
        "COALESCE(json_extract_path_text(data, 'host'), '') || ' ' || "
        "COALESCE(translate(json_extract_path_text(data, 'host'), '.', ' '), '')"
        ")"
    )
    op.create_table(
        "connection",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("group_id", sa.BigInteger(), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.String(length=512), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("search_vector", postgresql.TSVECTOR(), sa.Computed(sql_expression, persisted=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["group.id"],
            name=op.f("fk__connection__group_id__group"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__connection")),
        sa.UniqueConstraint("name", "group_id", name=op.f("uq__connection__name_group_id")),
    )
    op.create_index(op.f("ix__connection__group_id"), "connection", ["group_id"], unique=False)
    op.create_index(
        "idx_connection_search_vector",
        "connection",
        ["search_vector"],
        unique=False,
        postgresql_using="gin",
    )


def downgrade():
    op.drop_index(op.f("ix__connection__group_id"), table_name="connection")
    op.drop_index("idx_connection_search_vector", table_name="connection", postgresql_using="gin")
    op.drop_table("connection")
