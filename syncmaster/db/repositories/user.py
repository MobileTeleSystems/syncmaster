# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from typing import Any, NoReturn

from sqlalchemy import ScalarResult, insert, select
from sqlalchemy.exc import DBAPIError, IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import User
from syncmaster.db.repositories.base import Repository
from syncmaster.db.utils import Pagination
from syncmaster.exceptions import EntityNotFoundError, SyncmasterError
from syncmaster.exceptions.user import UsernameAlreadyExistsError, UserNotFoundError


class UserRepository(Repository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=User, session=session)

    async def paginate(self, page: int, page_size: int, is_superuser: bool) -> Pagination:
        stmt = select(User).where(User.is_deleted.is_(False))

        if not is_superuser:
            stmt = stmt.where(User.is_active.is_(True))
        return await self._paginate_scalar_result(query=stmt.order_by(User.username), page=page, page_size=page_size)

    async def read_by_id(self, user_id: int, **kwargs: Any) -> User:
        try:
            return await self._read_by_id(id=user_id, **kwargs)
        except EntityNotFoundError as e:
            raise UserNotFoundError from e

    async def read_by_username(self, username: str) -> User:
        try:
            result: ScalarResult[User] = await self._session.scalars(select(User).where(User.username == username))
            return result.one()
        except NoResultFound as e:
            raise EntityNotFoundError from e

    async def update(self, user_id: int, data: dict) -> User:
        try:
            return await self._update(User.id == user_id, User.is_deleted.is_(False), **data)
        except EntityNotFoundError as e:
            raise UserNotFoundError from e
        except IntegrityError as e:
            self._raise_error(e)

    async def create(self, username: str, is_active: bool, is_superuser: bool = False) -> User:
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
            await self._session.flush()
        except IntegrityError as err:
            self._raise_error(err)
        else:
            return result.one()

    def _raise_error(self, err: DBAPIError) -> NoReturn:
        constraint = err.__cause__.__cause__.constraint_name

        if constraint == "ix__user__username":
            raise UsernameAlreadyExistsError from err

        raise SyncmasterError from err
