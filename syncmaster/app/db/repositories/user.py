from typing import Any, NoReturn

from sqlalchemy import ScalarResult, insert, select
from sqlalchemy.exc import DBAPIError, IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.db.repositories.base import Repository
from app.db.utils import Pagination
from app.exceptions import (
    EntityNotFound,
    SyncmasterException,
    UsernameAlreadyExists,
    UserNotFound,
)


class UserRepository(Repository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=User, session=session)

    async def paginate(
        self, page: int, page_size: int, is_superuser: bool
    ) -> Pagination:
        stmt = select(User).where(User.is_deleted.is_(False))

        if not is_superuser:
            stmt = stmt.where(User.is_active.is_(True))
        return await self._paginate(
            query=stmt.order_by(User.username), page=page, page_size=page_size
        )

    async def read_by_id(self, user_id: int, **kwargs: Any) -> User:
        try:
            return await self._read_by_id(id=user_id, **kwargs)
        except EntityNotFound as e:
            raise UserNotFound from e

    async def read_by_username(self, username: str) -> User:
        result: ScalarResult[User] = await self._session.scalars(
            select(User).where(User.username == username)
        )
        try:
            return result.one()
        except NoResultFound as e:
            raise EntityNotFound from e

    async def update(self, user_id: int, data: dict) -> User:
        try:
            return await self._update(
                User.id == user_id, User.is_deleted.is_(False), **data
            )
        except EntityNotFound as e:
            raise UserNotFound from e
        except IntegrityError as e:
            await self._session.rollback()
            self._raise_error(e)

    async def create(
        self, username: str, is_active: bool, is_superuser: bool = False
    ) -> User:
        query = (
            insert(User)
            .values(
                username=username,
                is_active=is_active,
                is_superuser=is_superuser,
            )
            .returning(User)
        )
        try:
            result: ScalarResult[User] = await self._session.scalars(query)
            await self._session.commit()
        except IntegrityError as err:
            await self._session.rollback()
            self._raise_error(err)
        else:
            return result.one()

    def _raise_error(self, err: DBAPIError) -> NoReturn:
        constraint = err.__cause__.__cause__.constraint_name  # type: ignore

        if constraint == "ix__user__username":
            raise UsernameAlreadyExists from err

        raise SyncmasterException from err
