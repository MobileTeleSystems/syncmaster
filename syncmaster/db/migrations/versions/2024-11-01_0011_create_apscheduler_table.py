# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
"""Create apscheduler table

Revision ID: 0011
Revises: 0010
Create Date: 2024-11-01 08:37:47.078657

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def exists_table(table_name: str) -> bool:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    return table_name in tables


def upgrade() -> None:
    if exists_table("apscheduler_jobs"):
        return

    op.create_table(
        "apscheduler_jobs",
        sa.Column("id", sa.VARCHAR(length=191), autoincrement=False, nullable=False),
        sa.Column("next_run_time", sa.Float(25), autoincrement=False, nullable=True),
        sa.Column("job_state", sa.LargeBinary(), autoincrement=False, nullable=False),
        sa.PrimaryKeyConstraint("id", name="apscheduler_jobs_pkey"),
    )

    op.create_index("ix_apscheduler_jobs_next_run_time", "apscheduler_jobs", ["next_run_time"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_apscheduler_jobs_next_run_time", table_name="apscheduler_jobs")
    op.drop_table("apscheduler_jobs")
