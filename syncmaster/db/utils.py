# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import math
from collections.abc import Sequence
from enum import IntEnum
from typing import Any


class Pagination:
    def __init__(self, items: Sequence[Any], page: int, page_size: int, total: int) -> None:
        self.items = items
        self.total = total
        self.page_size = page_size
        self.page = page
        self.previous_page = None
        self.next_page = None
        self.has_previous = page > 1
        if self.has_previous:
            self.previous_page = page - 1
        previous_items = (page - 1) * page_size
        self.has_next = previous_items + len(items) < total
        if self.has_next:
            self.next_page = page + 1
        self.pages = int(math.ceil(total / float(page_size))) or 1


class Permission(IntEnum):
    NONE = 0
    READ = 1
    WRITE = 2  # same as CREATE, UPDATE, START, STOP
    DELETE = 3
