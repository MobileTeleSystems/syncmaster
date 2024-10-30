# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
"""Create auth_data table

Revision ID: 0006_create_auth_data_table
Revises: 0005_create_user_group_table
Create Date: 2023-11-23 11:40:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0006_create_auth_data_table"
down_revision = "0005_create_user_group_table"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "auth_data",
        sa.Column("connection_id", sa.BigInteger(), nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["connection_id"],
            ["connection.id"],
            name=op.f("fk__auth_data__connection_id__connection"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("connection_id", name=op.f("pk__auth_data")),
    )


def downgrade():
    op.drop_table("auth_data")
