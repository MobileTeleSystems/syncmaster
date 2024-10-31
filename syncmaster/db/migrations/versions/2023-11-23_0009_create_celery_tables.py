# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
"""Create celery_taskmeta and celery_tasksetmeta tables

Revision ID: 0009
Revises: 0008
Create Date: 2023-11-23 11:43:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def exists_table(table_name: str) -> bool:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    return table_name in tables


def upgrade():
    if exists_table("celery_taskmeta"):
        return

    task_id_sequence = sa.Sequence("task_id_sequence")
    op.execute(sa.schema.CreateSequence(task_id_sequence, if_not_exists=True))

    op.create_table(
        "celery_taskmeta",
        sa.Column("id", sa.Integer(), task_id_sequence, autoincrement=True, nullable=False),
        sa.Column("task_id", sa.String(length=155), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("result", sa.PickleType(), nullable=True),
        sa.Column("date_done", sa.DateTime(), nullable=True),
        sa.Column("traceback", sa.Text(), nullable=True),
        sa.Column("name", sa.String(length=155), nullable=True),
        sa.Column("args", sa.LargeBinary(), nullable=True),
        sa.Column("kwargs", sa.LargeBinary(), nullable=True),
        sa.Column("worker", sa.String(length=155), nullable=True),
        sa.Column("retries", sa.Integer(), nullable=True),
        sa.Column("queue", sa.String(length=155), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id"),
        sqlite_autoincrement=True,
    )

    taskset_id_sequence = sa.Sequence("taskset_id_sequence")
    op.execute(sa.schema.CreateSequence(taskset_id_sequence, if_not_exists=True))

    op.create_table(
        "celery_tasksetmeta",
        sa.Column("id", sa.Integer(), taskset_id_sequence, autoincrement=True, nullable=False),
        sa.Column("taskset_id", sa.String(length=155), nullable=True),
        sa.Column("result", sa.PickleType(), nullable=True),
        sa.Column("date_done", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("taskset_id"),
        sqlite_autoincrement=True,
    )


def downgrade():
    op.drop_table("celery_tasksetmeta")
    op.drop_table("celery_taskmeta")
    op.execute("drop sequence task_id_sequence")
    op.execute("drop sequence taskset_id_sequence")
