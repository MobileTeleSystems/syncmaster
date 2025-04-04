#!/bin/env python3

from __future__ import annotations

import csv
import gzip
import io
import json
import random
import shutil
import sys
from argparse import ArgumentParser
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from tempfile import gettempdir
from typing import TYPE_CHECKING, Any, TextIO
from xml.etree import ElementTree  # noqa: S405
from zipfile import ZipFile

if TYPE_CHECKING:
    from avro.schema import Schema as AvroSchema
    from pandas import DataFrame as PandasDataFrame
    from pyarrow import Schema as ArrowSchema
    from pyarrow import Table as ArrowTable

SEED = 42


def get_data() -> list:
    try:
        from test_data import data

        return data
    except Exception as e:
        print("File test_data.py does not exists, run 'generate_data.py'.", e)
        exit(1)


def get_intervals() -> list:
    try:
        from test_data import intervals

        return intervals
    except Exception as e:
        print("File test_data.py does not exists, run 'generate_data.py'.", e)
        exit(1)


def get_pandas_dataframe(data: list[dict]) -> PandasDataFrame:
    import pandas as pd

    return pd.DataFrame(data)


def get_pyarrow_schema() -> ArrowSchema:
    import pyarrow as pa

    return pa.schema(
        [
            pa.field("ID", pa.int32()),
            pa.field("PHONE_NUMBER", pa.string()),
            pa.field("REGION", pa.string()),
            pa.field("NUMBER", pa.int32()),
            pa.field("BIRTH_DATE", pa.date32()),
            pa.field("REGISTERED_AT", pa.timestamp("us")),
            pa.field("ACCOUNT_BALANCE", pa.float64()),
        ],
    )


def get_pyarrow_table(data: list[dict]) -> ArrowTable:
    import pyarrow as pa

    schema = get_pyarrow_schema()
    return pa.Table.from_pylist(data, schema)


def get_avro_schema() -> AvroSchema:
    from avro.schema import parse as parse_avro_schema

    schema = {
        "namespace": "my.namespace",
        "type": "record",
        "name": "MyType",
        "fields": [
            {"name": "ID", "type": "int"},
            {"name": "PHONE_NUMBER", "type": "string"},
            {"name": "REGION", "type": "string"},
            {"name": "NUMBER", "type": "int"},
            {"name": "BIRTH_DATE", "type": {"type": "int", "logicalType": "date"}},
            {"name": "REGISTERED_AT", "type": {"type": "long", "logicalType": "timestamp-millis"}},
            {"name": "ACCOUNT_BALANCE", "type": "double"},
        ],
    }
    return parse_avro_schema(json.dumps(schema))


def _to_string(obj):
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    return obj


def _write_csv(data: list[dict], file: TextIO, include_header: bool = False, **kwargs) -> None:
    columns = list(data[0].keys())
    writer = csv.DictWriter(file, fieldnames=columns, lineterminator="\n", **kwargs)

    if include_header:
        writer.writeheader()

    for row in data:
        writer.writerow({key: _to_string(value) for key, value in row.items()})


def save_as_csv_without_header(data: list[dict], path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    with open(path / "file.csv", "w", newline="") as file:
        _write_csv(data, file)


def save_as_csv_with_header(data: list[dict], path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    with open(path / "file.csv", "w", newline="") as file:
        _write_csv(data, file, include_header=True)


def save_as_csv_with_delimiter(data: list[dict], path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    with open(path / "file.csv", "w", newline="") as file:
        _write_csv(data, file, delimiter=";")


def save_as_csv_gz(data: list[dict], path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

    # https://stackoverflow.com/questions/66955482/why-does-recompressing-a-file-using-gzip-produces-a-different-output
    # Instead of just writing data to file we write it to a buffer, and then compress with fixed mtime
    buffer = io.StringIO()
    _write_csv(data, buffer)
    with open(path / "file.csv.gz", "wb") as file:
        with gzip.GzipFile(fileobj=file, mode="w", mtime=0) as gzfile:
            gzfile.write(buffer.getvalue().encode("utf-8"))


def save_as_csv_nested(data: list[dict], path: Path) -> None:
    path.joinpath("some/path").mkdir(parents=True, exist_ok=True)
    path.joinpath("some/path/more").mkdir(parents=True, exist_ok=True)
    path.joinpath("some/path/more/even_more").mkdir(parents=True, exist_ok=True)

    counter = 0

    for num, interval in enumerate(get_intervals()):
        if counter <= 2:
            with open(path / f"some/path/for_val{num}.csv", "w", newline="") as file:
                _write_csv([row for row in data if row["NUMBER"] in interval], file)

        if counter in (3, 4, 5):
            with open(path / f"some/path/more/for_val{num}.csv", "w", newline="") as file:
                _write_csv([row for row in data if row["NUMBER"] in interval], file)

        if counter >= 6:
            with open(path / f"some/path/more/even_more/for_val{num}.csv", "w", newline="") as file:
                _write_csv([row for row in data if row["NUMBER"] in interval], file)

        counter += 1


def save_as_csv_partitioned(data: list[dict], path: Path) -> None:
    def filter_and_drop(rows: list[dict], column: str, value: Any) -> list[dict]:
        result = []
        for row in rows:
            if row[column] == value or row[column] in value:
                row_copy = row.copy()
                row_copy.pop(column)
                result.append(row_copy)
        return result

    for num, _ in enumerate(get_intervals()):
        path.joinpath(f"NUMBER={num}").mkdir(parents=True, exist_ok=True)

    columns = list(data[0].keys())
    columns.remove("NUMBER")

    for num, interval in enumerate(get_intervals()):
        with open(path / f"NUMBER={num}/file.csv", "w", newline="") as file:
            data_for_val = filter_and_drop(data, "NUMBER", interval)
            _write_csv(data_for_val, file)


def save_as_csv(data: list[dict], path: Path) -> None:
    root = path / "csv"
    shutil.rmtree(root, ignore_errors=True)

    save_as_csv_without_header(data, root / "without_header")
    save_as_csv_with_header(data, root / "with_header")
    save_as_csv_with_delimiter(data, root / "with_delimiter")
    save_as_csv_gz(data, root / "with_compression")
    save_as_csv_nested(data, root / "nested")
    save_as_csv_partitioned(data, root / "partitioned")


def save_as_json_plain(data: list[dict], path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    path.joinpath("file.json").write_text(json.dumps(data, default=_to_string))


def save_as_json_gz(data: list[dict], path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    buffer = io.StringIO()
    json.dump(data, buffer, default=_to_string)
    with open(path / "file.json.gz", "wb") as file:
        with gzip.GzipFile(fileobj=file, mode="w", mtime=0) as gzfile:
            gzfile.write(buffer.getvalue().encode("utf-8"))


def save_as_json(data: list[dict], path: Path) -> None:
    root = path / "json"
    shutil.rmtree(root, ignore_errors=True)

    save_as_json_plain(data, root / "without_compression")
    save_as_json_gz(data, root / "with_compression")


def save_as_jsonline_plain(data: list[dict], path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    with open(path / "file.jsonl", "w") as file:
        for row in data:
            row_str = json.dumps(row, default=_to_string)
            file.write(row_str + "\n")


def save_as_jsonline_gz(data: list[dict], path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

    buffer = io.StringIO()
    for row in data:
        row_str = json.dumps(row, default=_to_string)
        buffer.write(row_str + "\n")

    with open(path / "file.jsonl.gz", "wb") as file:
        with gzip.GzipFile(fileobj=file, mode="w", mtime=0) as gzfile:
            gzfile.write(buffer.getvalue().encode("utf-8"))


def save_as_jsonline(data: list[dict], path: Path) -> None:
    root = path / "jsonline"
    shutil.rmtree(root, ignore_errors=True)

    save_as_jsonline_plain(data, root / "without_compression")
    save_as_jsonline_gz(data, root / "with_compression")


def save_as_orc_plain(data: list[dict], path: Path) -> None:
    from pyarrow import orc

    path.mkdir(parents=True, exist_ok=True)
    table = get_pyarrow_table(data)
    orc.write_table(table, path / "file.orc")


def save_as_orc_snappy(data: list[dict], path: Path) -> None:
    from pyarrow import orc

    path.mkdir(parents=True, exist_ok=True)
    table = get_pyarrow_table(data)
    orc.write_table(table, path / "file.snappy.orc", compression="snappy")


def save_as_orc(data: list[dict], path: Path) -> None:
    root = path / "orc"
    shutil.rmtree(root, ignore_errors=True)

    save_as_orc_plain(data, root / "without_compression")
    save_as_orc_snappy(data, root / "with_compression")


def save_as_parquet_plain(data: list[dict], path: Path) -> None:
    from pyarrow.parquet import ParquetWriter

    path.mkdir(parents=True, exist_ok=True)
    table = get_pyarrow_table(data)
    with ParquetWriter(path / "file.parquet", schema=table.schema, compression="none") as writer:
        writer.write_table(table)


def save_as_parquet_snappy(data: list[dict], path: Path) -> None:
    from pyarrow.parquet import ParquetWriter

    path.mkdir(parents=True, exist_ok=True)
    table = get_pyarrow_table(data)
    with ParquetWriter(path / "file.snappy.parquet", schema=table.schema, compression="snappy") as writer:
        writer.write_table(table)


def save_as_parquet(data: list[dict], path: Path) -> None:
    root = path / "parquet"
    shutil.rmtree(root, ignore_errors=True)

    save_as_parquet_plain(data, root / "without_compression")
    save_as_parquet_snappy(data, root / "with_compression")


@contextmanager
def temporary_set_seed(seed: int) -> Iterator[int]:
    """Set random.seed to expected value, and return previous value after exit"""
    state = random.getstate()
    try:  # noqa: WPS501
        random.seed(seed)
        yield seed
    finally:
        random.setstate(state)


def save_as_avro_plain(data: list[dict], path: Path) -> None:
    from avro.datafile import DataFileWriter
    from avro.io import DatumWriter

    path.mkdir(parents=True, exist_ok=True)
    schema = get_avro_schema()
    with open(path / "file.avro", "wb") as file:
        # DataFileDFWriter.sync_marker is initialized with randbytes
        # temporary set seed to avoid generating files with different hashes
        with temporary_set_seed(SEED):
            with DataFileWriter(file, DatumWriter(), schema) as writer:
                for row in data:
                    writer.append(row)


def save_as_avro_snappy(data: list[dict], path: Path) -> None:
    from avro.datafile import DataFileWriter
    from avro.io import DatumWriter

    path.mkdir(parents=True, exist_ok=True)
    schema = get_avro_schema()
    with open(path / "file.snappy.avro", "wb") as file:
        # DataFileDFWriter.sync_marker is initialized with randbytes
        # temporary set seed to avoid generating files with different hashes
        with temporary_set_seed(SEED):
            with DataFileWriter(file, DatumWriter(), schema, codec="snappy") as writer:
                for row in data:
                    writer.append(row)


def save_as_avro(data: list[dict], path: Path) -> None:
    root = path / "avro"
    shutil.rmtree(root, ignore_errors=True)

    save_as_avro_plain(data, root / "without_compression")
    save_as_avro_snappy(data, root / "with_compression")


def save_as_xls_with_options(
    data: list[dict],
    path: Path,
    index: bool = False,
    **kwargs,
) -> None:
    # required to register xlwt writer which supports generating .xls files
    pass

    path.mkdir(parents=True, exist_ok=True)
    file = path / "file.xls"

    df = get_pandas_dataframe(data)
    df["REGISTERED_AT"] = df.REGISTERED_AT.dt.tz_localize(None)
    df.to_excel(file, index=index, engine="xlsxwriter", **kwargs)


def make_zip_deterministic(path: Path) -> None:
    temp_dir = gettempdir()
    file_copy = Path(shutil.copy(path, temp_dir))

    with ZipFile(file_copy, "r") as original_file:
        with ZipFile(path, "w") as new_file:
            for item in original_file.infolist():
                if item.filename == "docProps/core.xml":
                    # this file contains modification time, which produces files with different hashes
                    continue
                # reset modification time of all files
                item.date_time = (1980, 1, 1, 0, 0, 0)
                new_file.writestr(item, original_file.read(item.filename))


def save_as_xlsx_with_options(
    data: list[dict],
    path: Path,
    index: bool = False,
    **kwargs,
) -> None:
    path.mkdir(parents=True, exist_ok=True)
    file = path / "file.xls"

    df = get_pandas_dataframe(data)
    df["REGISTERED_AT"] = df.REGISTERED_AT.dt.tz_localize(None)
    df.to_excel(file, index=index, engine="openpyxl", **kwargs)
    make_zip_deterministic(file)


def save_as_xlsx(data: list[dict], path: Path) -> None:
    root = path / "xlsx"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)

    save_as_xlsx_with_options(data, root / "without_header", include_header=False)
    save_as_xlsx_with_options(data, root / "with_header", include_header=True)
    save_as_xlsx_with_options(
        data,
        root / "with_data_address",
        include_header=False,
        sheet_name="ABC",
        startcol=10,
        startrow=5,
    )


def save_as_xls(data: list[dict], path: Path) -> None:
    root = path / "xls"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)

    save_as_xls_with_options(data, root / "without_header", include_header=False)
    save_as_xls_with_options(data, root / "with_header", include_header=True)
    save_as_xls_with_options(
        data,
        root / "with_data_address",
        include_header=False,
        sheet_name="ABC",
        startcol=10,
        startrow=5,
    )


def save_as_xml_plain(data: list[dict], path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    root = ElementTree.Element("root")

    for record in data:
        item = ElementTree.SubElement(root, "item")
        for key, value in record.items():
            child = ElementTree.SubElement(item, key)
            if isinstance(value, datetime):
                child.text = value.isoformat()
            else:
                child.text = str(value)

    tree = ElementTree.ElementTree(root)
    tree.write(path / "file.xml")


def save_as_xml_with_attributes(data: list[dict], path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    root = ElementTree.Element("root")

    for record in data:
        str_attributes = {
            key: value.isoformat() if isinstance(value, datetime) else str(value) for key, value in record.items()
        }
        item = ElementTree.SubElement(root, "item", attrib=str_attributes)
        for key, value in record.items():
            child = ElementTree.SubElement(item, key)
            if isinstance(value, datetime):
                child.text = value.isoformat()
            else:
                child.text = str(value)

    tree = ElementTree.ElementTree(root)
    tree.write(str(path / "file_with_attributes.xml"))


def save_as_xml_gz(data: list[dict], path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    root = ElementTree.Element("root")

    for record in data:
        item = ElementTree.SubElement(root, "item")
        for key, value in record.items():
            child = ElementTree.SubElement(item, key)
            if isinstance(value, datetime):
                child.text = value.isoformat()
            else:
                child.text = str(value)

    ElementTree.ElementTree(root)
    xml_string = ElementTree.tostring(root, encoding="utf-8")

    with gzip.open(path / "file.xml.gz", "wb", compresslevel=9) as f:
        f.write(xml_string)


def save_as_xml(data: list[dict], path: Path) -> None:
    root = path / "xml"
    shutil.rmtree(root, ignore_errors=True)

    save_as_xml_plain(data, root / "without_compression")
    save_as_xml_with_attributes(data, root / "with_attributes")
    save_as_xml_gz(data, root / "with_compression")


format_mapping = {
    "csv": save_as_csv,
    "json": save_as_json,
    "jsonline": save_as_jsonline,
    "orc": save_as_orc,
    "parquet": save_as_parquet,
    "avro": save_as_avro,
    "xlsx": save_as_xlsx,
    "xls": save_as_xls,
    "xml": save_as_xml,
}


def get_parser() -> ArgumentParser:
    known_formats = ["all", *format_mapping.keys()]
    parser = ArgumentParser()
    parser.add_argument("--path", type=Path, default=Path(__file__).parent)
    parser.add_argument("--format", type=str, default="all", choices=known_formats)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = get_parser()
    args = parser.parse_args(argv or sys.argv[1:])

    if args.format not in format_mapping and args.format != "all":
        raise ValueError(f"Format {args.format} is not supported")

    if args.format == "all":
        save_functions = list(format_mapping.values())
    else:
        save_functions = [format_mapping[args.format]]

    data = get_data()
    for save_func in save_functions:
        save_func(data, args.path)


if __name__ == "__main__":
    main()
