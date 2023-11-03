from abc import ABC
from typing import Any, Generic, TypeVar

from sqlalchemy import (
    ScalarResult,
    Select,
    and_,
    delete,
    func,
    insert,
    or_,
    select,
    update,
)
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base
from app.db.models import Group, UserGroup
from app.db.utils import Pagination
from app.exceptions import EntityNotFound

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
            raise EntityNotFound
        return obj

    @staticmethod
    def _model_as_dict(model: Model) -> dict[str, Any]:
        d = []
        for c in model.__table__.columns:  # type: ignore[attr-defined]
            if c.name == "id":  # 'id' is PK autoincrement
                continue
            d.append(c.name)

        return {key: getattr(model, key) for key in d}

    async def _copy(self, *args: Any, **kwargs: Any) -> Model:
        query_prev_row = select(self._model).where(*args)
        result_prev_row = await self._session.scalars(query_prev_row)
        origin_model = result_prev_row.one()

        d = self._model_as_dict(origin_model)

        d.update(
            kwargs
        )  # Process kwargs in order to keep only what needs to be updated
        query_insert_new_row = insert(self._model).values(**d).returning(self._model)
        try:
            new_row = await self._session.scalars(query_insert_new_row)
            await self._session.flush()
            obj = new_row.one()
        except NoResultFound as e:
            raise EntityNotFound from e
        return obj

    async def _update(self, *args: Any, **kwargs: Any) -> Model:
        query = update(self._model).where(*args).values(**kwargs).returning(self._model)
        try:
            result = await self._session.scalars(query)
            await self._session.flush()
            obj = result.one()
        except NoResultFound as e:
            raise EntityNotFound from e
        return obj

    async def _delete(self, id: int) -> Model:
        if hasattr(self._model, "is_deleted"):
            return await self._update(
                and_(self._model.is_deleted.is_(False), self._model.id == id),  # type: ignore
                is_deleted=True,
            )

        query = delete(self._model).filter_by(id=id).returning(self._model)
        result = await self._session.scalars(query)
        await self._session.flush()
        return result.one()

    async def _paginate(self, query: Select, page: int, page_size: int) -> Pagination:
        items_result: ScalarResult[Model] = await self._session.scalars(
            query.limit(page_size).offset((page - 1) * page_size)
        )
        total: int = await self._session.scalar(select(func.count()).select_from(query.subquery()))  # type: ignore
        return Pagination(
            items=items_result.all(),
            total=total,
            page=page,
            page_size=page_size,
        )


class RepositoryWithOwner(Repository, Generic[Model]):
    def check_permission(
        self,
        query: Select,
        user_id: int,
    ) -> Select:
        """Add to query filter access user to resource"""
        query = query.join(
            Group,
            Group.id == self._model.group_id,
            full=True,
        ).join(
            UserGroup,
            UserGroup.group_id == Group.id,
            full=True,
        )
        args = [
            Group.admin_id == user_id,
            self._model.user_id == user_id,
        ]
        args.append(UserGroup.user_id == user_id)
        return query.where(or_(*args)).group_by(self._model.id)

    async def has_owner_access(self, object_id: int, user_id: int) -> bool:
        """Check if user is owner of resource or if resource belong to group and user is group admin"""
        obj = (
            select(self._model.id)
            .join(Group, Group.id == self._model.group_id, full=True)
            .where(
                self._model.id == object_id,
                or_(Group.admin_id == user_id, self._model.user_id == user_id),
            )
            .exists()
            .select()
        )
        return await self._session.scalar(obj)
