# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
"""Update text search

Revision ID: 0012
Revises: 0011
Create Date: 2025-08-10 20:03:02.105470

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index(op.f("idx_connection_search_vector"), table_name="connection", postgresql_using="gin")
    op.drop_column("connection", "search_vector")
    op.drop_column("group", "search_vector")
    op.drop_index(op.f("idx_transfer_search_vector"), table_name="transfer", postgresql_using="gin")
    op.drop_column("transfer", "search_vector")
    op.drop_column("queue", "search_vector")

    op.add_column(
        "connection",
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed(
                "\n            to_tsvector('russian', coalesce(name, ''))\n         || to_tsvector('simple',  coalesce(name, '')) \n         || to_tsvector('simple', coalesce(data->>'host', ''))\n         || to_tsvector(\n                'simple',\n                translate(\n                    coalesce(data->>'host', ''),\n                    './-_:\\', '      '\n                )\n            )\n            ",
                persisted=True,
            ),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_connection_search_vector",
        "connection",
        ["search_vector"],
        unique=False,
        postgresql_using="gin",
    )
    op.add_column(
        "group",
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed(
                "\n            to_tsvector('russian', coalesce(name, ''))\n         || to_tsvector('simple',  coalesce(name, '')) \n            ",
                persisted=True,
            ),
            nullable=False,
        ),
    )
    op.add_column(
        "transfer",
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed(
                "\n            to_tsvector('russian', coalesce(name, ''))\n\n         || to_tsvector('simple', coalesce(name, ''))\n         || to_tsvector('simple', coalesce(source_params->>'table_name', ''))\n         || to_tsvector('simple', coalesce(target_params->>'table_name', ''))\n         || to_tsvector('simple', coalesce(source_params->>'directory_path', ''))\n         || to_tsvector('simple', coalesce(target_params->>'directory_path', ''))\n\n         || to_tsvector('simple',\n                translate(coalesce(source_params->>'table_name', ''), './-_:\\', '      ')\n            )\n         || to_tsvector('simple',\n                translate(coalesce(target_params->>'table_name', ''), './-_:\\', '      ')\n            )\n         || to_tsvector('simple',\n                translate(coalesce(source_params->>'directory_path', ''), './-_:\\', '      ')\n            )\n         || to_tsvector('simple',\n                translate(coalesce(target_params->>'directory_path', ''), './-_:\\', '      ')\n            )\n            ",
                persisted=True,
            ),
            nullable=False,
        ),
    )
    op.create_index("idx_transfer_search_vector", "transfer", ["search_vector"], unique=False, postgresql_using="gin")
    op.add_column(
        "queue",
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed(
                "\n            to_tsvector('russian', coalesce(name, ''))\n         || to_tsvector('simple',  coalesce(name, ''))\n            ",
                persisted=True,
            ),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_index("idx_transfer_search_vector", table_name="transfer", postgresql_using="gin")
    op.drop_column("transfer", "search_vector")
    op.drop_column("group", "search_vector")
    op.drop_index("idx_connection_search_vector", table_name="connection", postgresql_using="gin")
    op.drop_column("connection", "search_vector")
    op.drop_column("queue", "search_vector")

    op.add_column(
        "transfer",
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed(
                "to_tsvector('english'::regconfig, (((((((((((((((((((name)::text || ' '::text) || COALESCE(json_extract_path_text(source_params, VARIADIC ARRAY['table_name'::text]), ''::text)) || ' '::text) || COALESCE(json_extract_path_text(target_params, VARIADIC ARRAY['table_name'::text]), ''::text)) || ' '::text) || COALESCE(json_extract_path_text(source_params, VARIADIC ARRAY['directory_path'::text]), ''::text)) || ' '::text) || COALESCE(json_extract_path_text(target_params, VARIADIC ARRAY['directory_path'::text]), ''::text)) || ' '::text) || translate((name)::text, './'::text, '  '::text)) || ' '::text) || COALESCE(translate(json_extract_path_text(source_params, VARIADIC ARRAY['table_name'::text]), './'::text, '  '::text), ''::text)) || ' '::text) || COALESCE(translate(json_extract_path_text(target_params, VARIADIC ARRAY['table_name'::text]), './'::text, '  '::text), ''::text)) || ' '::text) || COALESCE(translate(json_extract_path_text(source_params, VARIADIC ARRAY['directory_path'::text]), './'::text, '  '::text), ''::text)) || ' '::text) || COALESCE(translate(json_extract_path_text(target_params, VARIADIC ARRAY['directory_path'::text]), './'::text, '  '::text), ''::text)))",
                persisted=True,
            ),
            autoincrement=False,
            nullable=False,
        ),
    )
    op.create_index(
        op.f("idx_transfer_search_vector"),
        "transfer",
        ["search_vector"],
        unique=False,
        postgresql_using="gin",
    )
    op.add_column(
        "group",
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('english'::regconfig, (name)::text)", persisted=True),
            autoincrement=False,
            nullable=False,
        ),
    )
    op.add_column(
        "connection",
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed(
                "to_tsvector('english'::regconfig, (((((name)::text || ' '::text) || COALESCE(json_extract_path_text(data, VARIADIC ARRAY['host'::text]), ''::text)) || ' '::text) || COALESCE(translate(json_extract_path_text(data, VARIADIC ARRAY['host'::text]), '.'::text, ' '::text), ''::text)))",
                persisted=True,
            ),
            autoincrement=False,
            nullable=False,
        ),
    )
    op.create_index(
        op.f("idx_connection_search_vector"),
        "connection",
        ["search_vector"],
        unique=False,
        postgresql_using="gin",
    )
    op.add_column(
        "queue",
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('english'::regconfig, (name)::text)", persisted=True),
            autoincrement=False,
            nullable=False,
        ),
    )
