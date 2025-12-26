from pathlib import Path

import pytest
from onetl.file.format import CSV, JSON, ORC, XML, Excel, JSONLine, Parquet


@pytest.fixture(scope="session")
def resource_path():
    path = Path(__file__).parents[3] / "resources"
    assert path.exists()
    return path


@pytest.fixture(params=[""])
def file_format_flavor(request: pytest.FixtureRequest):
    return request.param


@pytest.fixture
def source_file_format(request: pytest.FixtureRequest):
    name, params = request.param
    result_map = {
        "csv": CSV(lineSep="\n", header=True, **params),
        "jsonline": JSONLine(encoding="utf-8", lineSep="\n", **params),
        "json": JSON(lineSep="\n", encoding="utf-8", **params),
        "excel": Excel(header=True, inferSchema=True, **params),
        "orc": ORC(**params),
        "parquet": Parquet(**params),
        "xml": XML(rowTag="item", **params),
    }

    try:
        return name, result_map[name]
    except KeyError as e:
        msg = f"Unsupported file format: {name}"
        raise ValueError(msg) from e


@pytest.fixture
def target_file_format(request: pytest.FixtureRequest):
    name, params = request.param
    timestamp_format = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS+00:00"
    result_map = {
        "csv": CSV(lineSep="\n", header=True, timestampFormat=timestamp_format, **params),
        "jsonline": JSONLine(encoding="utf-8", lineSep="\n", timestampFormat=timestamp_format, **params),
        "excel": Excel(header=True, inferSchema=True, **params),
        "orc": ORC(**params),
        "parquet": Parquet(**params),
        "xml": XML(rowTag="item", **params),
    }

    try:
        return name, result_map[name]
    except KeyError as e:
        msg = f"Unsupported file format: {name}"
        raise ValueError(msg) from e
