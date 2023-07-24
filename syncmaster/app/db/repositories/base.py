from abc import ABC
from typing import Any, Generic, TypeVar

from sqlalchemy import ScalarResult, Select, and_, delete, func, select, update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base
from app.db.utils import Pagination
from app.exceptions import EntityNotFound

Model = TypeVar("Model", bound=Base)


class Repository(ABC, Generic[Model]):
    def __init__(self, model: type[Model], session: AsyncSession):
        self._model = model
        self._session = session

    async def _read_by_id(self, id: int, **kwargs: Any) -> Model:
        if hasattr(self._model, "is_deleted"):
            query = select(self._model).filter_by(is_deleted=False, id=id, **kwargs)
            obj = (await self._session.scalars(query)).first()
        else:
            obj = await self._session.get(self._model, id)
        if obj is None:
            raise EntityNotFound
        return obj

    async def _update(self, *args: Any, **kwargs: Any) -> Model:
        query = update(self._model).where(*args).values(**kwargs).returning(self._model)
        result = await self._session.scalars(select(self._model).from_statement(query))
        await self._session.commit()
        try:
            obj = result.one()
        except NoResultFound as e:
            raise EntityNotFound from e
        await self._session.refresh(obj)
        return obj

    async def _delete(self, id: int) -> Model:
        if hasattr(self._model, "is_deleted"):
            return await self._update(
                and_(self._model.is_deleted.is_(False), self._model.id == id),  # type: ignore
                is_deleted=True,
            )

        stmt = delete(self._model).filter_by(id=id).returning(self._model)
        result = await self._session.scalars(select(self._model).from_statement(stmt))
        await self._session.commit()
        try:
            return result.one()
        except NoResultFound as e:
            raise EntityNotFound from e

    async def _paginate(self, query: Select, page: int, page_size: int) -> Pagination:
        items_result: ScalarResult[Model] = await self._session.scalars(
            query.limit(page_size).offset((page - 1) * page_size)
        )
        total: int = await self._session.scalar(
            select(func.count()).select_from(query.subquery())
        )  # type: ignore
        return Pagination(
            items=items_result.all(),
            total=total,
            page=page,
            page_size=page_size,
        )
