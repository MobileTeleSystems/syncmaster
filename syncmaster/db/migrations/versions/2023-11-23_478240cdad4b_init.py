# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
"""init

Revision ID: 478240cdad4b
Revises:
Create Date: 2023-11-23 11:35:18.193060

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "478240cdad4b"
down_revision = None
branch_labels = None
depends_on = None


def exists_table(table_name: str) -> bool:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    return table_name in tables


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "user",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=256), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__user")),
    )
    op.create_index(op.f("ix__user__username"), "user", ["username"], unique=True)
    op.create_table(
        "group",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("description", sa.String(length=512), nullable=False),
        sa.Column("owner_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"], name=op.f("fk__group__owner_id__user"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__group")),
        sa.UniqueConstraint("name", name=op.f("uq__group__name")),
    )
    op.create_index(op.f("ix__group__owner_id"), "group", ["owner_id"], unique=False)
    op.create_table(
        "connection",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("group_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.String(length=512), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
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
    op.create_table(
        "queue",
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("group_id", sa.BigInteger(), nullable=False),
        sa.Column("description", sa.String(length=512), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["group.id"],
            name=op.f("fk__queue__group_id__group"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__queue")),
        sa.UniqueConstraint("name", name=op.f("uq__queue__name")),
    )
    op.create_index(op.f("ix__queue__group_id"), "queue", ["group_id"], unique=False)
    op.create_table(
        "user_group",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("group_id", sa.BigInteger(), nullable=False),
        sa.Column("role", sa.String(255), nullable=False),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["group.id"],
            name=op.f("fk__user_group__group_id__group"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name=op.f("fk__user_group__user_id__user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", "group_id", name=op.f("pk__user_group")),
    )
    op.create_index(op.f("ix__user_group__group_id"), "user_group", ["group_id"], unique=False)
    op.create_index(op.f("ix__user_group__user_id"), "user_group", ["user_id"], unique=False)
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
    op.create_table(
        "run",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("transfer_id", sa.BigInteger(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(255), nullable=False),
        sa.Column("log_url", sa.String(length=512), nullable=True),
        sa.Column("transfer_dump", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["transfer_id"],
            ["transfer.id"],
            name=op.f("fk__run__transfer_id__transfer"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__run")),
    )
    op.create_index(op.f("ix__run__status"), "run", ["status"], unique=False)
    op.create_index(op.f("ix__run__transfer_id"), "run", ["transfer_id"], unique=False)

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
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("celery_tasksetmeta")
    op.drop_table("celery_taskmeta")
    op.drop_index(op.f("ix__run__transfer_id"), table_name="run")
    op.drop_index(op.f("ix__run__status"), table_name="run")
    op.drop_table("run")
    op.drop_index(op.f("ix__transfer__target_connection_id"), table_name="transfer")
    op.drop_index(op.f("ix__transfer__source_connection_id"), table_name="transfer")
    op.drop_index(op.f("ix__transfer__group_id"), table_name="transfer")
    op.drop_table("transfer")
    op.drop_table("auth_data")
    op.drop_index(op.f("ix__user_group__user_id"), table_name="user_group")
    op.drop_index(op.f("ix__user_group__group_id"), table_name="user_group")
    op.drop_table("user_group")
    op.drop_index(op.f("ix__queue__group_id"), table_name="queue")
    op.drop_table("queue")
    op.drop_index(op.f("ix__connection__group_id"), table_name="connection")
    op.drop_table("connection")
    op.drop_index(op.f("ix__group__owner_id"), table_name="group")
    op.drop_table("group")
    op.drop_index(op.f("ix__user__username"), table_name="user")
    op.drop_table("user")
    op.execute("drop sequence task_id_sequence")
    op.execute("drop sequence taskset_id_sequence")
    # ### end Alembic commands ###
