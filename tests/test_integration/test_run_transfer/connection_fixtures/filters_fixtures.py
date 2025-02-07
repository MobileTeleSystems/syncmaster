import pytest


@pytest.fixture
def dataframe_rows_filter_transformations(source_type: str):
    regexp_value = "[0-9!@#$.,;_]%" if source_type == "mssql" else "^[^+].*"  # MSSQL regexp is limited
    return [
        {
            "type": "dataframe_rows_filter",
            "filters": [
                {
                    "type": "is_not_null",
                    "field": "BIRTH_DATE",
                },
                {
                    "type": "less_or_equal",
                    "field": "NUMBER",
                    "value": "25",
                },
                {
                    "type": "not_like",
                    "field": "REGION",
                    "value": "%port",
                },
                {
                    "type": "not_ilike",
                    "field": "REGION",
                    "value": "new%",
                },
                {
                    "type": "regexp",
                    "field": "PHONE_NUMBER",
                    "value": regexp_value,
                },
            ],
        },
    ]


@pytest.fixture
def expected_dataframe_rows_filter():
    return lambda df, source_type: df.filter(
        df["BIRTH_DATE"].isNotNull()
        & (df["NUMBER"] <= "25")
        & (~df["REGION"].like("%port"))
        & (~df["REGION"].ilike("new%"))
        & (df["PHONE_NUMBER"].rlike("^[0-9!@#$.,;_]" if source_type == "mssql" else "^[^+].*")),
    )


@pytest.fixture
def dataframe_columns_filter_transformations(source_type: str):
    string_types_per_source_type = {
        "postgres": "VARCHAR(10)",
        "oracle": "VARCHAR2(10)",
        "clickhouse": "VARCHAR(10)",
        "mysql": "CHAR",
        "mssql": "VARCHAR(10)",
        "hive": "VARCHAR(10)",
        "s3": "STRING",
        "hdfs": "STRING",
    }
    return [
        {
            "type": "dataframe_columns_filter",
            "filters": [
                {
                    "type": "include",
                    "field": "ID",
                },
                {
                    "type": "include",
                    "field": "REGION",
                },
                {
                    "type": "include",
                    "field": "PHONE_NUMBER",
                },
                {
                    "type": "rename",
                    "field": "REGION",
                    "to": "REGION2",
                },
                {
                    "type": "cast",
                    "field": "NUMBER",
                    "as_type": string_types_per_source_type[source_type],
                },
                {
                    "type": "include",
                    "field": "REGISTERED_AT",
                },
            ],
        },
    ]


@pytest.fixture
def expected_dataframe_columns_filter():
    return lambda df, source_type: df.selectExpr(
        "ID",
        "REGION",
        "PHONE_NUMBER",
        "REGION AS REGION2",
        "CAST(NUMBER AS STRING) AS NUMBER",
        "REGISTERED_AT",
    )


@pytest.fixture
def file_metadata_filter_transformations():
    return [
        {
            "type": "file_metadata_filter",
            "filters": [
                {
                    "type": "name_glob",
                    "value": "*.csv",
                },
                {
                    "type": "name_regexp",
                    "value": r"\bfile\b",
                },
                {
                    "type": "file_size_min",
                    "value": "1kb",
                },
                {
                    "type": "file_size_max",
                    "value": "3kb",
                },
            ],
        },
    ]
