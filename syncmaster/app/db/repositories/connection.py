from typing import Any, NoReturn

from sqlalchemy import ScalarResult, insert, select
from sqlalchemy.exc import DBAPIError, IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Acl, Connection, ObjectType, Rule
from app.db.repositories.base import RepositoryWithAcl
from app.db.utils import Pagination
from app.exceptions import (
    AclNotFound,
    ActionNotAllowed,
    ConnectionNotFound,
    ConnectionOwnerException,
    GroupNotFound,
    SyncmasterException,
    UserNotFound,
)
from app.exceptions.base import EntityNotFound


class ConnectionRepository(RepositoryWithAcl[Connection]):
    def __init__(self, session: AsyncSession, provider):
        self.provider = provider
        self._object_type = ObjectType.CONNECTION
        super().__init__(model=Connection, session=session)

    async def paginate(
        self,
        page: int,
        page_size: int,
        current_user_id: int,
        is_superuser: bool,
        group_id: int | None = None,
        user_id: int | None = None,
    ) -> Pagination:
        if not is_superuser and user_id and current_user_id != user_id:
            raise ActionNotAllowed
        stmt = select(Connection).where(Connection.is_deleted.is_(False))
        args = []
        if user_id is not None:
            args.append(Connection.user_id == user_id)
        if group_id is not None:
            args.append(Connection.group_id == group_id)

        if not is_superuser:
            stmt = self.apply_acl(stmt, current_user_id)
        return await self._paginate(
            query=stmt.where(*args).order_by(Connection.name),
            page=page,
            page_size=page_size,
        )

    async def read_by_id(
        self,
        connection_id: int,
        current_user_id: int,
        is_superuser: bool,
        rule: Rule = Rule.READ,
    ) -> Connection:
        stmt = select(Connection).where(
            Connection.id == connection_id, Connection.is_deleted.is_(False)
        )
        if not is_superuser:
            stmt = self.apply_acl(stmt, current_user_id, rule=rule)
        result: ScalarResult[Connection] = await self._session.scalars(stmt)
        try:
            return result.one()
        except NoResultFound as e:
            raise ConnectionNotFound from e

    async def create(
        self,
        user_id: int | None,
        group_id: int | None,
        name: str,
        description: str,
        data: dict[str, Any],
    ) -> Connection:
        stmt = (
            insert(Connection)
            .values(
                user_id=user_id,
                group_id=group_id,
                name=name,
                description=description,
                data=data,
            )
            .returning(Connection)
        )
        try:
            result: ScalarResult[Connection] = await self._session.scalars(
                select(Connection).from_statement(stmt)
            )
        except IntegrityError as e:
            await self._session.rollback()
            self._raise_error(e)
        else:
            await self._session.commit()
            return result.one()

    async def update(
        self,
        connection_id: int,
        current_user_id: int,
        is_superuser: bool,
        name: str | None,
        description: str | None,
        connection_data: dict[str, Any],
    ) -> Connection:
        try:
            connection = await self.read_by_id(
                connection_id=connection_id,
                current_user_id=current_user_id,
                is_superuser=is_superuser,
                rule=Rule.WRITE,
            )
            for key in connection.data:
                if key not in connection_data or connection_data[key] is None:
                    connection_data[key] = connection.data[key]
            return await self._update(
                Connection.id == connection_id,
                Connection.is_deleted.is_(False),
                name=name or connection.name,
                description=description or connection.description,
                data=connection_data,
            )
        except IntegrityError as e:
            await self._session.rollback()
            self._raise_error(e)

    async def delete(
        self, connection_id: int, current_user_id: int, is_superuser: bool
    ) -> None:
        if not is_superuser:
            await self.read_by_id(
                connection_id=connection_id,
                current_user_id=current_user_id,
                is_superuser=False,
                rule=Rule.DELETE,
            )
        try:
            await self._delete(connection_id)
        except (NoResultFound, EntityNotFound) as e:
            raise ConnectionNotFound from e

    async def change_owner(
        self,
        connection_id: int,
        new_group_id: int | None,
        new_user_id: int | None,
        current_user_id: int,
        is_superuser: bool,
    ) -> None:
        if not is_superuser and not await self.has_owner_access(
            connection_id, current_user_id
        ):
            raise ConnectionNotFound
        kwargs = dict(user_id=new_user_id, group_id=new_group_id)
        try:
            await self._update(Connection.id == connection_id, **kwargs)
        except IntegrityError as e:
            await self._session.rollback()
            self._raise_error(e)

    async def add_or_update_rule(
        self,
        connection_id: int,
        current_user_id: int,
        is_superuser: bool,
        rule: Rule,
        target_user_id: int,
    ) -> Acl:
        if not is_superuser and not await self.has_owner_access(
            object_id=connection_id,
            user_id=current_user_id,
        ):
            raise ConnectionNotFound
        connection = await self.read_by_id(
            connection_id=connection_id,
            current_user_id=current_user_id,
            is_superuser=is_superuser,
        )
        if connection.group_id is None:
            raise ActionNotAllowed
        try:
            return await self._add_or_update_rule(
                object_id=connection_id, user_id=target_user_id, rule=rule
            )
        except IntegrityError as e:
            await self._session.rollback()
            self._raise_error(e)

    async def delete_rule(
        self,
        current_user_id: int,
        is_superuser: bool,
        connection_id: int,
        target_user_id: int,
    ):
        if not is_superuser and not await self.has_owner_access(
            object_id=connection_id,
            user_id=current_user_id,
        ):
            raise ConnectionNotFound
        connection = await self.read_by_id(
            connection_id=connection_id,
            current_user_id=current_user_id,
            is_superuser=is_superuser,
        )
        if connection.group_id is None:
            raise ActionNotAllowed
        try:
            await self._delete_acl_rule(object_id=connection_id, user_id=target_user_id)
        except EntityNotFound as e:
            raise AclNotFound from e
        return

    def _raise_error(self, err: DBAPIError) -> NoReturn:
        constraint = err.__cause__.__cause__.constraint_name  # type: ignore[union-attr]
        if constraint == "fk__connection__group_id__group":
            raise GroupNotFound from err
        if constraint == "fk__connection__user_id__user":
            raise UserNotFound from err
        if constraint == "ck__connection__owner_constraint":
            raise ConnectionOwnerException from err
        raise SyncmasterException from err
