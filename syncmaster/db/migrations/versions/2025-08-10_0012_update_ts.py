# SPDX-FileCopyrightText: 2023-present MTS PJSC
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
    op.drop_index(
        op.f("idx_connection_search_vector"),
        table_name="connection",
        postgresql_using="gin",
    )
    op.drop_column("connection", "search_vector")
    op.drop_column("group", "search_vector")
    op.drop_index(
        op.f("idx_transfer_search_vector"),
        table_name="transfer",
        postgresql_using="gin",
    )
    op.drop_column("transfer", "search_vector")
    op.drop_column("queue", "search_vector")

    op.add_column(
        "connection",
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed(
                """
                -- === NAME FIELD ===
                -- Russian stemming for better morphological matching of regular words
                to_tsvector('russian', coalesce(name, ''))
                -- Simple dictionary (no stemming) for exact token match
                || to_tsvector('simple', coalesce(name, ''))
                -- Simple dictionary with translate(): split by . / - _ : \
                -- (used when 'name' contains technical fields)
                || to_tsvector(
                    'simple',
                    translate(coalesce(name, ''), './-_:\\', '      ')
                )

                -- === HOST FIELD (from JSON) ===
                -- Simple dictionary (no stemming) for exact match
                || to_tsvector('simple', coalesce(data->>'host', ''))
                -- Simple dictionary with translate(): split by . / - _ : \\ for partial token matching
                || to_tsvector(
                    'simple',
                    translate(coalesce(data->>'host', ''), './-_:\\', '      ')
                )
                """,
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
                """
                -- === NAME FIELD ===
                -- Russian stemming for better morphological matching of regular words
                to_tsvector('russian', coalesce(name, ''))
                -- Simple dictionary (no stemming) for exact token match
                || to_tsvector('simple', coalesce(name, ''))
                -- Simple dictionary with translate(): split by . / - _ : \
                -- (used when 'name' contains technical fields)
                || to_tsvector(
                    'simple',
                    translate(coalesce(name, ''), './-_:\\', '      ')
                )
                """,
                persisted=True,
            ),
            nullable=False,
        ),
    )

    op.add_column(
        "queue",
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed(
                """
                -- === NAME FIELD ===
                -- Russian stemming for better morphological matching of regular words
                to_tsvector('russian', coalesce(name, ''))
                -- Simple dictionary (no stemming) for exact token match
                || to_tsvector('simple', coalesce(name, ''))
                -- Simple dictionary with translate(): split by . / - _ : \
                -- (used when 'name' contains technical fields)
                || to_tsvector(
                    'simple',
                    translate(coalesce(name, ''), './-_:\\', '      ')
                )
                """,
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
                """
                -- === NAME FIELD ===
                -- Russian stemming for better morphological matching of regular words
                to_tsvector('russian', coalesce(name, ''))
                -- Simple dictionary (no stemming) for exact token match
                || to_tsvector('simple', coalesce(name, ''))
                -- Simple dictionary with translate(): split by . / - _ : \
                -- (used when 'name' contains technical fields)
                || to_tsvector(
                    'simple',
                    translate(coalesce(name, ''), './-_:\\', '      ')
                )

                -- === TABLE NAME FIELDS ===
                -- Simple dictionary (no stemming) for exact match
                || to_tsvector('simple', coalesce(source_params->>'table_name', ''))
                || to_tsvector('simple', coalesce(target_params->>'table_name', ''))
                -- Simple dictionary with translate(): split by . / - _ : \\ for partial token matching
                || to_tsvector(
                    'simple',
                    translate(coalesce(source_params->>'table_name', ''), './-_:\\', '      ')
                )
                || to_tsvector(
                    'simple',
                    translate(coalesce(target_params->>'table_name', ''), './-_:\\', '      ')
                )

                -- === DIRECTORY PATH FIELDS ===
                -- Simple dictionary (no stemming) for exact match
                || to_tsvector('simple', coalesce(source_params->>'directory_path', ''))
                || to_tsvector('simple', coalesce(target_params->>'directory_path', ''))
                -- Simple dictionary with translate(): split by . / - _ : \\ for partial token matching
                || to_tsvector(
                    'simple',
                    translate(coalesce(source_params->>'directory_path', ''), './-_:\\', '      ')
                )
                || to_tsvector(
                    'simple',
                    translate(coalesce(target_params->>'directory_path', ''), './-_:\\', '      ')
                )
                """,
                persisted=True,
            ),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_transfer_search_vector",
        "transfer",
        ["search_vector"],
        unique=False,
        postgresql_using="gin",
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
                "to_tsvector('english'::regconfig, "
                "name || ' ') || "
                "COALESCE(json_extract_path_text(source_params, VARIADIC ARRAY['table_name']), '') || ' ' || "
                "COALESCE(json_extract_path_text(target_params, VARIADIC ARRAY['table_name']), '') || ' ' || "
                "COALESCE(json_extract_path_text(source_params, VARIADIC ARRAY['directory_path']), '') || ' ' || "
                "COALESCE(json_extract_path_text(target_params, VARIADIC ARRAY['directory_path']), '') || ' ' || "
                "translate(name, './', '  ') || ' ' || "
                "COALESCE(translate(json_extract_path_text(source_params, VARIADIC ARRAY['table_name']), './', '  '), '') || ' ' || "
                "COALESCE(translate(json_extract_path_text(target_params, VARIADIC ARRAY['table_name']), './', '  '), '') || ' ' || "
                "COALESCE(translate(json_extract_path_text(source_params, VARIADIC ARRAY['directory_path']), './', '  '), '') || ' ' || "
                "COALESCE(translate(json_extract_path_text(target_params, VARIADIC ARRAY['directory_path']), './', '  '), ''))",
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
            sa.Computed("to_tsvector('english'::regconfig, name)", persisted=True),
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
                "to_tsvector('english'::regconfig, "
                "name || ' ' || "
                "COALESCE(json_extract_path_text(data, VARIADIC ARRAY['host']), '') || ' ' || "
                "COALESCE(translate(json_extract_path_text(data, VARIADIC ARRAY['host']), '.', ' '), ''))",
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
            sa.Computed("to_tsvector('english'::regconfig, name)", persisted=True),
            autoincrement=False,
            nullable=False,
        ),
    )
