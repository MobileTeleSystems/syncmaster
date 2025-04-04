from pathlib import Path

import pytest
from onetl.file.format import CSV, JSON, ORC, XML, Excel, JSONLine, Parquet
from pytest import FixtureRequest


@pytest.fixture(scope="session")
def resource_path():
    path = Path(__file__).parents[3] / "resources"
    assert path.exists()
    return path


@pytest.fixture(params=[""])
def file_format_flavor(request: FixtureRequest):
    return request.param


@pytest.fixture()
def source_file_format(request: FixtureRequest):
    name, params = request.param
    if name == "csv":
        return "csv", CSV(
            lineSep="\n",
            header=True,
            **params,
        )

    if name == "jsonline":
        return "jsonline", JSONLine(
            encoding="utf-8",
            lineSep="\n",
            **params,
        )

    if name == "json":
        return "json", JSON(
            lineSep="\n",
            encoding="utf-8",
            **params,
        )

    if name == "excel":
        return "excel", Excel(
            header=True,
            inferSchema=True,
            **params,
        )

    if name == "orc":
        return "orc", ORC(
            **params,
        )

    if name == "parquet":
        return "parquet", Parquet(
            **params,
        )

    if name == "xml":
        return "xml", XML(
            row_tag="item",
            **params,
        )

    raise ValueError(f"Unsupported file format: {name}")


@pytest.fixture()
def target_file_format(request: FixtureRequest):
    name, params = request.param
    if name == "csv":
        return "csv", CSV(
            lineSep="\n",
            header=True,
            timestampFormat="yyyy-MM-dd'T'HH:mm:ss.SSSSSS+00:00",
            **params,
        )

    if name == "jsonline":
        return "jsonline", JSONLine(
            encoding="utf-8",
            lineSep="\n",
            timestampFormat="yyyy-MM-dd'T'HH:mm:ss.SSSSSS+00:00",
            **params,
        )

    if name == "excel":
        return "excel", Excel(
            header=False,
            **params,
        )

    if name == "orc":
        return "orc", ORC(
            **params,
        )

    if name == "parquet":
        return "parquet", Parquet(
            **params,
        )

    if name == "xml":
        return "xml", XML(
            row_tag="item",
            **params,
        )

    raise ValueError(f"Unsupported file format: {name}")
