# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
"""add pg_trgm extension to apply fuzzy search

Revision ID: 1df3778daf4f
Revises: b9f5c4315bb2
Create Date: 2024-10-07 06:59:12.667067

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "1df3778daf4f"
down_revision = "b9f5c4315bb2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("DROP EXTENSION IF EXISTS pg_trgm;")
    # ### end Alembic commands ###
