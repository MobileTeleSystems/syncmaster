from abc import ABC
from typing import Any, Generic, TypeVar

from sqlalchemy import ScalarResult, Select, and_, delete, func, or_, select, update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base
from app.db.models import Acl, Group, ObjectType, Rule, UserGroup
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
        result = await self._session.scalars(query)
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

        query = delete(self._model).filter_by(id=id).returning(self._model)
        result = await self._session.scalars(query)
        await self._session.commit()
        return result.one()

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


class RepositoryWithAcl(Repository, Generic[Model]):
    _object_type: ObjectType

    def apply_acl(self, query: Select, user_id: int, rule: Rule = Rule.READ) -> Select:
        """Add to query filter access user to resource"""
        query = query.join(Group, Group.id == self._model.group_id, full=True).join(
            UserGroup, UserGroup.group_id == Group.id, full=True
        )
        args = [
            Group.admin_id == user_id,
            self._model.user_id == user_id,
        ]
        if rule == Rule.READ:
            # TODO update when users can set rule without groups
            args.append(UserGroup.user_id == user_id)
        else:
            query = query.join(
                Acl,
                and_(
                    Acl.object_id == self._model.id,
                    Acl.object_type == self._object_type,
                ),
                full=True,
            )
            args.append(
                and_(
                    UserGroup.user_id == user_id,
                    Acl.user_id == user_id,
                    Acl.rule >= rule,
                ),
            )
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

    async def _add_or_update_rule(
        self, object_id: int, user_id: int, rule: Rule
    ) -> Acl:
        acl = (
            await self._session.scalars(
                select(Acl).where(
                    Acl.user_id == user_id,
                    Acl.object_type == self._object_type,
                    Acl.object_id == object_id,
                )
            )
        ).first()
        if acl is not None:
            acl.rule = rule
        else:
            acl = Acl()
            acl.object_id = object_id
            acl.object_type = self._object_type
            acl.user_id = user_id
            acl.rule = rule
            self._session.add(acl)
        await self._session.commit()
        await self._session.refresh(acl)
        return acl

    async def _delete_acl_rule(self, object_id: int, user_id: int) -> None:
        try:
            acl = (
                await self._session.scalars(
                    select(Acl).where(
                        Acl.user_id == user_id,
                        Acl.object_type == self._object_type,
                        Acl.object_id == object_id,
                    )
                )
            ).one()
            await self._session.delete(acl)
            await self._session.commit()
        except NoResultFound as e:
            raise EntityNotFound from e
