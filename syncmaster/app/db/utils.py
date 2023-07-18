import math
from asyncio import gather
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession


class Pagination:
    def __init__(self, items: list[Any], page: int, page_size: int, total: int) -> None:
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
        self.pages = int(math.ceil(total / float(page_size)))


async def paginate(
    query: Select, page: int, page_size: int, session: AsyncSession
) -> Pagination:
    items_result, total_result = await gather(
        session.execute(query.limit(page_size).offset((page - 1) * page_size)),
        session.execute(select(func.count()).select_from(query.subquery())),
    )
    return Pagination(
        items=items_result.scalars().all(),
        total=total_result.scalar_one(),
        page=page,
        page_size=page_size,
    )
