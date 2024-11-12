# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from typing import NoReturn

from sqlalchemy import ScalarResult, insert, select
from sqlalchemy.exc import DBAPIError, IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.backend.settings import BackendSettings as Settings
from syncmaster.db.models import AuthData
from syncmaster.db.repositories.base import Repository
from syncmaster.db.repositories.utils import decrypt_auth_data, encrypt_auth_data
from syncmaster.exceptions import SyncmasterError
from syncmaster.exceptions.credentials import AuthDataNotFoundError


class CredentialsRepository(Repository[AuthData]):
    def __init__(
        self,
        settings: Settings,
        session: AsyncSession,
        model: type[AuthData],
    ):
        super().__init__(model=model, session=session)
        self._settings = settings

    async def read(
        self,
        connection_id: int,
    ) -> dict:
        query = select(AuthData).where(AuthData.connection_id == connection_id)
        try:
            result: ScalarResult[AuthData] = await self._session.scalars(query)
            return decrypt_auth_data(result.one().value, settings=self._settings)
        except NoResultFound as e:
            raise AuthDataNotFoundError(f"Connection id = {connection_id}") from e

    async def read_bulk(
        self,
        connection_ids: list[int],
    ) -> dict[int, dict]:
        query = select(AuthData).where(AuthData.connection_id.in_(connection_ids))
        result: ScalarResult[AuthData] = await self._session.scalars(query)
        return {item.connection_id: decrypt_auth_data(item.value, settings=self._settings) for item in result}

    async def create(self, connection_id: int, data: dict) -> AuthData:
        query = (
            insert(AuthData)
            .values(
                value=encrypt_auth_data(value=data, settings=self._settings),
                connection_id=connection_id,
            )
            .returning(AuthData)
        )
        try:
            result: ScalarResult[AuthData] = await self._session.scalars(query)
        except IntegrityError as e:
            self._raise_error(e)
        else:
            await self._session.flush()
            return result.one()

    async def update(
        self,
        connection_id: int,
        data: dict,
    ) -> AuthData:
        creds = await self.read(connection_id)
        try:
            for key in creds:
                data[key] = data.get(key, None) or creds[key]
            return await self._update(
                AuthData.connection_id == connection_id,
                value=encrypt_auth_data(value=data, settings=self._settings),
            )
        except IntegrityError as e:
            self._raise_error(e)

    def _raise_error(self, err: DBAPIError) -> NoReturn:
        raise SyncmasterError from err
