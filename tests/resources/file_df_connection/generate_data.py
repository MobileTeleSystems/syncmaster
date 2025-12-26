#!/bin/env python3

from __future__ import annotations

import sys
from argparse import ArgumentParser
from datetime import UTC
from pathlib import Path

from faker import Faker


def create_data(elements: int) -> list[dict]:
    fake = Faker(["ru_RU", "en_US"])

    return [
        {
            "ID": fake.random_int(),
            "PHONE_NUMBER": fake.phone_number(),
            "REGION": fake.city(),
            "NUMBER": i + 1,
            "BIRTH_DATE": fake.date_object(),
            "REGISTERED_AT": fake.date_time(tzinfo=UTC),
            "ACCOUNT_BALANCE": fake.random_int() + (fake.random_int() / 10000),
        }
        for i in range(elements)
    ]


def calculate_intravals(elements: int, parts: int):
    intervals = []
    batch_size: int = int(elements / parts)  # the result should not be fractional
    for batch_num in range(parts):
        temp_list = []
        for batch_position_number in range(batch_size):
            temp_list.append((batch_num * batch_size) + batch_position_number + 1)
        intervals.append(temp_list)

    return intervals


def generate_data_file(elements: int, parts: int):
    data = create_data(elements)
    with Path("test_data.py").open("w") as f:
        data_to_write = f"import datetime\nintervals={calculate_intravals(elements, parts)}\ndata={data}"
        f.write(data_to_write)


def main(argv: list[str] | None = None) -> None:
    parser = ArgumentParser()
    parser.add_argument("--parts", type=int, default=9)
    parser.add_argument("--elements", type=int, default=27)
    args = parser.parse_args(argv or sys.argv[1:])

    generate_data_file(args.elements, args.parts)


if __name__ == "__main__":
    main()
