"""empty message

Revision ID: d4484447fbd4
Revises:
Create Date: 2023-08-04 10:49:44.634839

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d4484447fbd4"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "user",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=256), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__user")),
    )
    op.create_index(op.f("ix__user__username"), "user", ["username"], unique=True)
    op.create_table(
        "acl",
        sa.Column("object_id", sa.BigInteger(), nullable=False),
        sa.Column("object_type", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("rule", sa.SmallInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name=op.f("fk__acl__user_id__user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "object_id", "user_id", "object_type", name=op.f("pk__acl")
        ),
    )
    op.create_table(
        "group",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("description", sa.String(length=512), nullable=False),
        sa.Column("admin_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["admin_id"],
            ["user.id"],
            name=op.f("fk__group__admin_id__user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__group")),
        sa.UniqueConstraint("name", name=op.f("uq__group__name")),
    )
    op.create_index(op.f("ix__group__admin_id"), "group", ["admin_id"], unique=False)
    op.create_table(
        "connection",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("group_id", sa.BigInteger(), nullable=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.String(length=512), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint(
            "(user_id IS NULL) <> (group_id IS NULL)",
            name=op.f("ck__connection__owner_constraint"),
        ),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["group.id"],
            name=op.f("fk__connection__group_id__group"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name=op.f("fk__connection__user_id__user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__connection")),
        sa.UniqueConstraint(
            "name",
            "user_id",
            "group_id",
            name=op.f("uq__connection__name_user_id_group_id"),
        ),
    )
    op.create_index(
        op.f("ix__connection__group_id"), "connection", ["group_id"], unique=False
    )
    op.create_index(
        op.f("ix__connection__user_id"), "connection", ["user_id"], unique=False
    )
    op.create_table(
        "transfer",
        sa.Column("source_connection_id", sa.BigInteger(), nullable=False),
        sa.Column("target_connection_id", sa.BigInteger(), nullable=False),
        sa.Column("strategy_params", sa.JSON(), nullable=False),
        sa.Column("source_params", sa.JSON(), nullable=False),
        sa.Column("target_params", sa.JSON(), nullable=False),
        sa.Column("is_scheduled", sa.Boolean(), nullable=False),
        sa.Column("schedule", sa.String(length=32), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("group_id", sa.BigInteger(), nullable=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.String(length=512), nullable=False),
        sa.CheckConstraint(
            "(user_id IS NULL) <> (group_id IS NULL)",
            name=op.f("ck__transfer__owner_constraint"),
        ),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["group.id"],
            name=op.f("fk__transfer__group_id__group"),
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
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name=op.f("fk__transfer__user_id__user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__transfer")),
        sa.UniqueConstraint(
            "name",
            "user_id",
            "group_id",
            name=op.f("uq__transfer__name_user_id_group_id"),
        ),
    )
    op.create_index(
        op.f("ix__transfer__group_id"), "transfer", ["group_id"], unique=False
    )
    op.create_index(
        op.f("ix__transfer__source_connection_id"),
        "transfer",
        ["source_connection_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix__transfer__target_connection_id"),
        "transfer",
        ["target_connection_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix__transfer__user_id"), "transfer", ["user_id"], unique=False
    )
    op.create_table(
        "run",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("transfer_id", sa.BigInteger(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("log_url", sa.String(length=512), nullable=True),
        sa.Column("transfer_dump", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
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
    op.create_table(
        "user_group",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("group_id", sa.BigInteger(), nullable=False),
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
    op.create_index(
        op.f("ix__user_group__group_id"), "user_group", ["group_id"], unique=False
    )
    op.create_index(
        op.f("ix__user_group__user_id"), "user_group", ["user_id"], unique=False
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix__user_group__user_id"), table_name="user_group")
    op.drop_index(op.f("ix__user_group__group_id"), table_name="user_group")
    op.drop_table("user_group")
    op.drop_index(op.f("ix__run__transfer_id"), table_name="run")
    op.drop_index(op.f("ix__run__status"), table_name="run")
    op.drop_table("run")
    op.drop_index(op.f("ix__transfer__user_id"), table_name="transfer")
    op.drop_index(op.f("ix__transfer__target_connection_id"), table_name="transfer")
    op.drop_index(op.f("ix__transfer__source_connection_id"), table_name="transfer")
    op.drop_index(op.f("ix__transfer__group_id"), table_name="transfer")
    op.drop_table("transfer")
    op.drop_index(op.f("ix__connection__user_id"), table_name="connection")
    op.drop_index(op.f("ix__connection__group_id"), table_name="connection")
    op.drop_table("connection")
    op.drop_index(op.f("ix__group__admin_id"), table_name="group")
    op.drop_table("group")
    op.drop_table("acl")
    op.drop_index(op.f("ix__user__username"), table_name="user")
    op.drop_table("user")
    # ### end Alembic commands ###
