# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from abc import ABC
from typing import Any, Generic, TypeVar

from sqlalchemy import ScalarResult, Select, and_, delete, func, insert, select, update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.base import Base
from syncmaster.db.utils import Pagination
from syncmaster.exceptions import EntityNotFoundError

Model = TypeVar("Model", bound=Base)


class Repository(Generic[Model], ABC):
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
            raise EntityNotFoundError
        return obj

    @staticmethod
    def _model_as_dict(model: Model) -> dict[str, Any]:
        d = []
        for c in model.__table__.columns:
            if c.name == "id":  # 'id' is PK autoincrement
                continue
            d.append(c.name)

        return {key: getattr(model, key) for key in d}

    async def _copy(self, *args: Any, **kwargs: Any) -> Model:
        query_prev_row = select(self._model).where(*args)
        result_prev_row = await self._session.scalars(query_prev_row)
        origin_model = result_prev_row.one()

        d = self._model_as_dict(origin_model)

        for k, v in kwargs.items():
            if v is None:
                kwargs.update({k: getattr(origin_model, k)})

        d.update(kwargs)  # Process kwargs in order to keep only what needs to be updated
        query_insert_new_row = insert(self._model).values(**d).returning(self._model)
        try:
            new_row = await self._session.scalars(query_insert_new_row)
            await self._session.flush()
            obj = new_row.one()
        except NoResultFound as e:
            raise EntityNotFoundError from e
        return obj

    async def _update(self, *args: Any, **kwargs: Any) -> Model:
        query = update(self._model).where(*args).values(**kwargs).returning(self._model)
        try:
            result = await self._session.scalars(query)
            await self._session.flush()
            obj = result.one()
        except NoResultFound as e:
            raise EntityNotFoundError from e
        return obj

    async def _delete(self, id: int) -> Model:
        if hasattr(self._model, "is_deleted"):
            return await self._update(
                and_(self._model.is_deleted.is_(False), self._model.id == id),
                is_deleted=True,
            )

        query = delete(self._model).filter_by(id=id).returning(self._model)
        result = await self._session.scalars(query)
        await self._session.flush()
        return result.one()

    async def _paginate_raw_result(self, query: Select, page: int, page_size: int) -> Pagination:
        items_result = await self._session.execute(query.limit(page_size).offset((page - 1) * page_size))
        total: int = await self._session.scalar(select(func.count()).select_from(query.subquery()))
        return Pagination(
            items=items_result.all(),
            total=total,
            page=page,
            page_size=page_size,
        )

    async def _paginate_scalar_result(self, query: Select, page: int, page_size: int) -> Pagination:
        """
        This method is needed for those queries where all fields are needed,
        the scalars method discards all fields except the first
        """
        items_result: ScalarResult[Model] = await self._session.scalars(
            query.limit(page_size).offset((page - 1) * page_size)
        )
        total: int = await self._session.scalar(select(func.count()).select_from(query.subquery()))
        return Pagination(
            items=items_result.all(),
            total=total,
            page=page,
            page_size=page_size,
        )
